import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

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
    # Results expire after 24h — matches Phase 2 spec
    result_expires=86400,
    # Retry failed tasks with exponential backoff
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)


@celery.task(
    bind=True,
    name="tasks.analyze_video",
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
)
def analyze_video(self, object_key: str, user_id: int):
    """
    Day 4: skeleton task — validates args, simulates work.
    Day 5: replace body with FFmpeg extraction + Groq Whisper.
    Day 6: add LLM analysis on transcript.
    """
    import time

    print(f"[Task {self.request.id}] Starting analysis")
    print(f"  object_key : {object_key}")
    print(f"  user_id    : {user_id}")

    # Simulate processing time — replaced by real work on Day 5
    time.sleep(2)

    # Day 5 will return real transcript + analysis here
    return {
        "status": "ok",
        "object_key": object_key,
        "user_id": user_id,
        "transcript": "stub — real transcript added Day 5",
        "analysis": {
            "filler_words": {},
            "pace_wpm": 0,
            "clarity_score": 0,
            "tips": []
        }
    }