import os
import uuid
import subprocess
import tempfile
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import Celery
from tenacity import retry, stop_after_attempt, wait_exponential
from services.ai import analyze_transcript_with_ai, validate_transcript
from logger import log

REDIS_URL     = os.getenv("REDIS_URL", "redis://localhost:6379/0")
AWS_REGION    = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET     = os.getenv("S3_BUCKET_NAME")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY")

celery = Celery(
    "resume_scanner",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=86400,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)


# ── S3 helpers ──────────────────────────────────────────────────────────────

def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4")
    )


def download_from_s3(object_key: str, local_path: str) -> None:
    s3 = get_s3_client()
    try:
        s3.download_file(S3_BUCKET, object_key, local_path)
       # print(f"[S3] Downloaded {object_key} → {local_path}")
        log.info("S3 Downloaded", object_key=object_key, local_path=local_path)
    except ClientError as e:
        log.error("S3 Download Failed", object_key=object_key, local_path=local_path, error=str(e))
        raise RuntimeError(f"S3 download failed: {e}")


def delete_from_s3(object_key: str) -> None:
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=S3_BUCKET, Key=object_key)
        #print(f"[S3] Deleted {object_key}")
        log.info("S3 Deleted", object_key=object_key)
    except ClientError as e:
        # Log but never raise — deletion failure must not fail the job
        #print(f"[S3] Delete failed for {object_key}: {e}")
        log.error("S3 Delete Failed", object_key=object_key, error=str(e))


# ── FFmpeg audio extraction ─────────────────────────────────────────────────
def extract_audio(video_path: str, wav_path: str) -> float:
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-ar", "16000",
        "-ac", "1",
        "-vn",
        wav_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        stderr = result.stderr.lower()
        # All known FFmpeg messages for missing/silent audio tracks
        no_audio_signals = [
            "does not contain any stream",
            "no audio",
            "output file is empty",
            "invalid data found",
            "unable to find a suitable output format",
        ]
        if any(signal in stderr for signal in no_audio_signals):
            log.warning("FFmpeg No Audio", video_path=video_path, wav_path=wav_path)
            raise ValueError(
                "The uploaded video does not contain a valid audio track. "
                "Please record a video with clear speech and re-upload."
            )
        log.error("FFmpeg Failed", video_path=video_path, wav_path=wav_path, error=result.stderr)
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    # ffprobe for duration
    probe = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            wav_path
        ],
        capture_output=True,
        text=True
    )
    try:
        duration = float(probe.stdout.strip())
    except ValueError:
        duration = 0.0

    #print(f"[FFmpeg] Extracted audio → {wav_path} ({duration:.1f}s)")
    log.info("FFmpeg Extracted", wav_path=wav_path, duration=duration)
    return duration




@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def transcribe_audio(wav_path: str) -> str:
    """
    Sends WAV file to Groq Whisper API.
    Retries up to 3 times with exponential backoff on rate limits.
    Raises on final failure — Celery autoretry handles task-level retry.
    """
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)

    # Groq Whisper limit is 25MB — check before sending
    file_size = os.path.getsize(wav_path)
    if file_size > 25 * 1024 * 1024:
        log.warning("Whisper File Too Large", wav_path=wav_path, file_size=file_size)
        raise RuntimeError(
            f"WAV file too large for Whisper: {file_size / 1024 / 1024:.1f}MB. "
            "Compress to 64kbps AAC first."
        )

    with open(wav_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f,
            response_format="text"
        )

    #print(f"[Whisper] Transcription complete ({len(transcription)} chars)")
    log.info("Whisper Transcription Complete", transcription_length=len(transcription))
    return transcription


# ── Main Celery task ────────────────────────────────────────────────────────

@celery.task(
    bind=True,
    name="tasks.analyze_video",
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    dont_autoretry_for=(ValueError,),   # transcript validation failures — no retry
)
def analyze_video(self, object_key: str, user_id: int):
    """
    Full pipeline:
    S3 download → FFmpeg WAV → Groq Whisper → transcript
    Day 6 adds: transcript → Groq LLM → analysis JSON
    """
    task_id = self.request.id
    #print(f"[Task {task_id}] Starting | object_key={object_key} user_id={user_id}")
    log.info("Task Starting", task_id=task_id, object_key=object_key, user_id=user_id)

    # Use a unique temp dir per task — prevents collision under concurrency
    tmp_dir = tempfile.mkdtemp(prefix=f"scanner_{task_id}_")
    video_path = os.path.join(tmp_dir, f"{uuid.uuid4()}.mp4")
    wav_path   = os.path.join(tmp_dir, f"{uuid.uuid4()}.wav")

    # 👇 FIX 1: Initialize the tracking variable before the try block
    s3_cleanup_done = False

    try:
        # ── Step 1: Download video from S3 ──────────────────────────────
        print(f"[Task {task_id}] Step 1: Downloading from S3")
        log.info("Task Step 1: Downloading from S3", task_id=task_id)
        download_from_s3(object_key, video_path)

        # ── Step 2: Extract audio with FFmpeg ───────────────────────────
        print(f"[Task {task_id}] Step 2: Extracting audio")
        log.info("Task Step 2: Extracting audio", task_id=task_id)
        duration_seconds = extract_audio(video_path, wav_path)

        # Delete video immediately — only WAV needed from here
        os.remove(video_path)
        print(f"[Task {task_id}] Video deleted from /tmp")
        log.info("Task Video Deleted", task_id=task_id)

        # ── Step 3: Transcribe with Groq Whisper ────────────────────────
        print(f"[Task {task_id}] Step 3: Transcribing audio")
        log.info("Task Step 3: Transcribing audio", task_id=task_id)
        transcript = transcribe_audio(wav_path)

        # Delete WAV after transcription — no audio persisted
        os.remove(wav_path)
        print(f"[Task {task_id}] WAV deleted from /tmp")
        log.info("Task WAV Deleted", task_id=task_id)

        # ── Step 4: Validate transcript ─────────────────────────────────
        print(f"[Task {task_id}] Step 4: Validating transcript")
        log.info("Task Step 4: Validating transcript", task_id=task_id)
        try:
            validate_transcript(transcript)
        except ValueError as e:
            # Hard failure — no retry. Silent/corrupted video won't improve.
            # Raise without autoretry by wrapping in a non-retried exception path.
            self.update_state(
                state="FAILURE",
                meta={"error": str(e), "exc_type": "TranscriptValidationError"}
            )
            log.error("Transcript Validation Failed", task_id=task_id, error=str(e))
            raise ValueError(str(e)) from None

        # ── Step 5: LLM communication analysis ──────────────────────────
        print(f"[Task {task_id}] Step 5: Analysing transcript")
        log.info("Task Step 5: Analysing transcript", task_id=task_id)
        analysis = analyze_transcript_with_ai(transcript, duration_seconds)

        # ── Step 6: Delete video from S3 ────────────────────────────────
        delete_from_s3(object_key)
        # 👇 FIX 2: Mark it as done so the finally block skips it
        s3_cleanup_done = True 
        print(f"[Task {task_id}] S3 object deleted")
        log.info("Task S3 Object Deleted", task_id=task_id)

        result = {
            "transcript": transcript,
            "duration_seconds": duration_seconds,
            "analysis": analysis
        }
        print(f"[Task {task_id}] Complete | clarity={analysis['clarity_score']} pace={analysis['pace_wpm']}wpm")
        log.info("Task Complete", task_id=task_id, clarity=analysis['clarity_score'], pace=analysis['pace_wpm'])
        return result

    except Exception as e:
        print(f"[Task {task_id}] Failed at step: {e}")
        log.error("Task Failed", task_id=task_id, error=str(e))
        raise

    finally:
        # ── Always: clean /tmp ───────────────────────────────────────
        for path in [video_path, wav_path]:
            if os.path.exists(path):
                os.remove(path)
                print(f"[Task {task_id}] Cleaned /tmp: {path}")
                log.info("Task Cleaned /tmp", task_id=task_id, path=path)

        # ── Always: delete S3 object unless already done ─────────────
        # Covers: ValueError (silent video), RuntimeError (FFmpeg fail),
        # Whisper failure, LLM failure — every failure path
        if not s3_cleanup_done:
            print(f"[Task {task_id}] Cleaning S3 on failure path")
            log.info("Task Cleaning S3 on failure path", task_id=task_id)
            delete_from_s3(object_key)