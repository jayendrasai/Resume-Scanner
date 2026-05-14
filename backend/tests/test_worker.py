import pytest
import os
from unittest.mock import patch, MagicMock, mock_open, ANY


# ── S3 helpers ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_download_from_s3_success():
    with patch("tasks.celery_app.boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        from tasks.celery_app import download_from_s3
        download_from_s3("videos/1/test.mp4", "/tmp/test.mp4")

        mock_s3.download_file.assert_called_once()


@pytest.mark.asyncio
async def test_download_from_s3_failure():
    from botocore.exceptions import ClientError
    with patch("tasks.celery_app.boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_s3.download_file.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "download_file"
        )
        mock_boto.return_value = mock_s3

        from tasks.celery_app import download_from_s3
        with pytest.raises(RuntimeError, match="S3 download failed"):
            download_from_s3("videos/1/missing.mp4", "/tmp/test.mp4")


# ── FFmpeg extraction ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extract_audio_success():
    mock_run = MagicMock()
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "12.5\n"
    mock_run.return_value.stderr = ""

    with patch("tasks.celery_app.subprocess.run", return_value=mock_run.return_value):
        from tasks.celery_app import extract_audio
        duration = extract_audio("/tmp/test.mp4", "/tmp/test.wav")
        assert duration == 12.5


@pytest.mark.asyncio
async def test_extract_audio_ffmpeg_failure():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Invalid data found"

    with patch("tasks.celery_app.subprocess.run", return_value=mock_result):
        from tasks.celery_app import extract_audio
        with pytest.raises(RuntimeError, match="FFmpeg failed"):
            extract_audio("/tmp/bad.mp4", "/tmp/out.wav")


# ── Whisper transcription ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_transcribe_audio_success():
    mock_groq = MagicMock()
    mock_groq.return_value.audio.transcriptions.create.return_value = \
        "Hello, my name is Sai and I am applying for this role."

    with patch("tasks.celery_app.os.path.getsize", return_value=1024 * 1024):  # 1MB
       
        # with patch("tasks.celery_app.Groq", mock_groq):
        #     with patch("builtins.open", mock_open(read_data=b"fake-wav")):
        #         from tasks.celery_app import transcribe_audio
        #         result = transcribe_audio("/tmp/test.wav")
        #         assert "Sai" in result
        # FIX 1: Patch the groq module directly instead of tasks.celery_app.Groq
        with patch("groq.Groq", mock_groq): 
            with patch("builtins.open", mock_open(read_data=b"fake-wav")):
                from tasks.celery_app import transcribe_audio
                result = transcribe_audio("/tmp/test.wav")
                assert "Sai" in result


@pytest.mark.asyncio
async def test_transcribe_audio_file_too_large():
    with patch("tasks.celery_app.os.path.getsize",
               return_value=30 * 1024 * 1024):  # 30MB > 25MB limit
        from tasks.celery_app import transcribe_audio
        with pytest.raises(RuntimeError, match="too large"):
            transcribe_audio("/tmp/huge.wav")


#  # ── Full task pipeline ──────────────────────────────────────────────────────

# @pytest.mark.asyncio
# async def test_analyze_video_full_pipeline(client):
#     """
#     Mocks every external call.
#     Validates the pipeline runs start to finish without real S3/FFmpeg/Groq.
#     """
#     with patch("tasks.celery_app.download_from_s3") as mock_dl, \
#          patch("tasks.celery_app.extract_audio", return_value=45.0) as mock_ffmpeg, \
#          patch("tasks.celery_app.transcribe_audio",
#                return_value="Um, I think my experience is, like, really relevant") as mock_whisper, \
#          patch("tasks.celery_app.delete_from_s3") as mock_del, \
#          patch("tasks.celery_app.os.remove") as mock_rm, \
#          patch("tasks.celery_app.tempfile.mkdtemp", return_value="/tmp/fake_task"):

#         from tasks.celery_app import analyze_video

#         # Call task directly (bypass Celery broker)
#         result = analyze_video.run(
#             object_key="videos/1/test.mp4",
#             user_id=1
#         )

#         # Pipeline ran in correct order
#         mock_dl.assert_called_once_with("videos/1/test.mp4", pytest.approx(str, abs=1))
#         mock_ffmpeg.assert_called_once()
#         mock_whisper.assert_called_once()
#         mock_del.assert_called_once_with("videos/1/test.mp4")

#         # Result shape correct
#         assert "transcript" in result
#         assert "duration_seconds" in result
#         assert result["duration_seconds"] == 45.0
#         assert "analysis" in result


# @pytest.mark.asyncio
# async def test_analyze_video_cleans_up_on_failure(client):
#     """If S3 download fails, no temp files left behind."""
#     with patch("tasks.celery_app.download_from_s3",
#                side_effect=RuntimeError("S3 unreachable")), \
#          patch("tasks.celery_app.tempfile.mkdtemp", return_value="/tmp/fake_fail"), \
#          patch("tasks.celery_app.os.path.exists", return_value=False), \
#          patch("tasks.celery_app.os.remove") as mock_rm:

#         from tasks.celery_app import analyze_video

#         with pytest.raises(Exception):
#             analyze_video.run(object_key="videos/1/test.mp4", user_id=1)

 # ── Full task pipeline ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_analyze_video_full_pipeline(client):
    with patch("tasks.celery_app.download_from_s3") as mock_dl, \
         patch("tasks.celery_app.extract_audio", return_value=45.0) as mock_ffmpeg, \
         patch("tasks.celery_app.transcribe_audio", return_value="Um, I think my experience is, like, really relevant") as mock_whisper, \
         patch("tasks.celery_app.delete_from_s3") as mock_del, \
         patch("tasks.celery_app.os.remove") as mock_rm, \
         patch("tasks.celery_app.tempfile.mkdtemp", return_value="/tmp/fake_task"):
        
        from tasks.celery_app import analyze_video
        result = analyze_video.run(object_key="videos/1/test.mp4", user_id=1)

        # FIX 2: Use ANY from unittest.mock instead of pytest.approx for the string path
        mock_dl.assert_called_once_with("videos/1/test.mp4", ANY)
        
        mock_ffmpeg.assert_called_once()
        mock_whisper.assert_called_once()
        mock_del.assert_called_once_with("videos/1/test.mp4")

        assert "transcript" in result
        assert "duration_seconds" in result
        assert result["duration_seconds"] == 45.0
        assert "analysis" in result

@pytest.mark.asyncio
async def test_analyze_video_cleans_up_on_failure(client):
    with patch("tasks.celery_app.download_from_s3", side_effect=RuntimeError("S3 unreachable")), \
         patch("tasks.celery_app.tempfile.mkdtemp", return_value="/tmp/fake_fail"), \
         patch("tasks.celery_app.os.path.exists", return_value=False), \
         patch("tasks.celery_app.os.remove") as mock_rm:
        
        from tasks.celery_app import analyze_video
        with pytest.raises(Exception):
            analyze_video.run(object_key="videos/1/test.mp4", user_id=1)