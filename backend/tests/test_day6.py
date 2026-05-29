import pytest
from unittest.mock import patch, MagicMock
import logging

# Initialize the logger
log = logging.getLogger(__name__)


# ── Filler word counter ─────────────────────────────────────────────────────

def test_filler_count_basic():
    from services.ai import count_filler_words
    transcript = "Um I think like you know this is uh really good"
    counts = count_filler_words(transcript)
    assert counts["um"] == 1
    assert counts["uh"] == 1
    assert counts["like"] == 1
    assert counts["you know"] == 1


def test_filler_count_case_insensitive():
    from services.ai import count_filler_words
    transcript = "UM um Um UH uh LIKE like"
    counts = count_filler_words(transcript)
    assert counts["um"] == 3
    assert counts["uh"] == 2
    assert counts["like"] == 2


def test_filler_count_whole_word_only():
    from services.ai import count_filler_words
    # "umbrella" should not match "um", "unlike" should not match "like"
    transcript = "I have an umbrella and unlike others I am unlike that"
    counts = count_filler_words(transcript)
    assert counts["um"] == 0
    assert counts["like"] == 0


def test_filler_count_zero_fillers():
    from services.ai import count_filler_words
    transcript = "My experience in Python spans five years of backend development."
    counts = count_filler_words(transcript)
    assert all(v == 0 for v in counts.values())
    assert set(counts.keys()) == {"um", "uh", "like", "you know", "so"}


# ── Transcript validator ────────────────────────────────────────────────────

def test_validate_transcript_empty():
    from services.ai import validate_transcript
    with pytest.raises(ValueError, match="empty"):
        validate_transcript("")


def test_validate_transcript_whitespace_only():
    from services.ai import validate_transcript
    with pytest.raises(ValueError, match="empty"):
        validate_transcript("   \n\t  ")


def test_validate_transcript_too_short():
    from services.ai import validate_transcript
    with pytest.raises(ValueError, match="too short"):
        validate_transcript("Hello world this is short")


def test_validate_transcript_passes():
    from services.ai import validate_transcript
    transcript = " ".join(["word"] * 15)
    validate_transcript(transcript)  # should not raise


# ── analyze_transcript_with_ai ──────────────────────────────────────────────

def test_analyze_transcript_merges_filler_counts():
    """
    LLM result must not override deterministic filler counts.
    Even if LLM returns filler_words, we use our computed counts.
    """
    from services.ai import analyze_transcript_with_ai

    mock_llm_response = MagicMock()
    mock_llm_response.choices[0].message.content = (
        '{"pace_wpm": 130, "clarity_score": 72, "tips": ["t1","t2","t3","t4","t5"]}'
    )

    with patch("services.ai.groq_client") as mock_groq:
        mock_groq.chat.completions.create.return_value = mock_llm_response
        transcript = "Um I think my experience is like really strong you know"
        result = analyze_transcript_with_ai(transcript, duration_seconds=30.0)

    assert result["filler_words"]["um"] == 1
    assert result["filler_words"]["like"] == 1
    assert result["filler_words"]["you know"] == 1
    assert result["pace_wpm"] == 130
    assert result["clarity_score"] == 72
    assert len(result["tips"]) == 5


def test_analyze_transcript_fallback_on_groq_failure():
    from services.ai import analyze_transcript_with_ai

    fallback_result = {
        "pace_wpm": 120,
        "clarity_score": 60,
        "tips": ["t1", "t2", "t3", "t4", "t5"]
    }

    with patch("services.ai.groq_client") as mock_groq, \
         patch("services.ai.call_openrouter_fallback", return_value=fallback_result):
        mock_groq.chat.completions.create.side_effect = Exception("Groq down")
        transcript = " ".join(["word"] * 20)
        result = analyze_transcript_with_ai(transcript, duration_seconds=60.0)

    assert result["clarity_score"] == 60
    assert result["pace_wpm"] == 120


# ── Task-level validation failure ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_s3_deleted_on_silent_video_failure():
    """
    S3 object must be deleted even when task fails due to silent video.
    Previously this was a bug — delete only ran on happy path.
    """
    with patch("tasks.celery_app.download_from_s3"), \
         patch("tasks.celery_app.extract_audio",
               side_effect=ValueError("does not contain a valid audio track")), \
         patch("tasks.celery_app.delete_from_s3") as mock_s3_delete, \
         patch("tasks.celery_app.os.path.exists", return_value=False), \
         patch("tasks.celery_app.tempfile.mkdtemp", return_value="/tmp/fake"):

        from tasks.celery_app import analyze_video

        with pytest.raises(ValueError):
            analyze_video.run(
                object_key="videos/1/silent.mp4",
                user_id=1
            )

        # S3 delete must have been called despite task failure
        mock_s3_delete.assert_called_once_with("videos/1/silent.mp4")





@pytest.mark.asyncio
async def test_task_fails_on_empty_transcript(client):
    """
    Validates that empty transcript causes task FAILURE not retry.
    """
    from unittest.mock import patch, MagicMock

    with patch("tasks.celery_app.download_from_s3"), \
         patch("tasks.celery_app.extract_audio", return_value=5.0), \
         patch("tasks.celery_app.transcribe_audio", return_value=""), \
         patch("tasks.celery_app.os.remove"), \
         patch("tasks.celery_app.tempfile.mkdtemp", return_value="/tmp/fake"), \
        patch("tasks.celery_app.analyze_video.update_state"):  # <-- NEW MOCK

        from tasks.celery_app import analyze_video

        with pytest.raises(ValueError, match="empty"):
            analyze_video.run(
                object_key="videos/1/test.mp4",
                user_id=1
            )


@pytest.mark.asyncio
async def test_task_fails_on_short_transcript(client):
    with patch("tasks.celery_app.download_from_s3"), \
         patch("tasks.celery_app.extract_audio", return_value=5.0), \
         patch("tasks.celery_app.transcribe_audio", return_value="only six words here"), \
         patch("tasks.celery_app.os.remove"), \
         patch("tasks.celery_app.tempfile.mkdtemp", return_value="/tmp/fake"), \
        patch("tasks.celery_app.analyze_video.update_state"):  # <-- NEW MOCK
         
        from tasks.celery_app import analyze_video

        with pytest.raises(ValueError, match="too short"):
            analyze_video.run(
                object_key="videos/1/test.mp4",
                user_id=1
            )


@pytest.mark.asyncio
async def test_full_pipeline_day6(client):
    """End-to-end Day 6 pipeline with real filler counting."""
    transcript = (
        "Um I think my experience is like really strong. "
        "You know I have worked on Python and FastAPI for about five years. "
        "Uh the projects I have led were really impactful."
    )
    analysis_result = {
        "pace_wpm": 125,
        "clarity_score": 68,
        "tips": ["t1", "t2", "t3", "t4", "t5"]
    }

    with patch("tasks.celery_app.download_from_s3"), \
         patch("tasks.celery_app.extract_audio", return_value=60.0), \
         patch("tasks.celery_app.transcribe_audio", return_value=transcript), \
         patch("tasks.celery_app.analyze_transcript_with_ai",
               return_value={**analysis_result,
                             "filler_words": {"um": 1, "uh": 1, "like": 1,
                                              "you know": 1, "so": 0}}), \
         patch("tasks.celery_app.delete_from_s3"), \
         patch("tasks.celery_app.os.remove"), \
         patch("tasks.celery_app.tempfile.mkdtemp", return_value="/tmp/fake"):

        from tasks.celery_app import analyze_video
        result = analyze_video.run(
            object_key="videos/1/test.mp4",
            user_id=1
        )

    assert result["transcript"] == transcript
    assert result["duration_seconds"] == 60.0
    assert result["analysis"]["filler_words"]["um"] == 1
    assert result["analysis"]["clarity_score"] == 68
    assert result["analysis"]["pace_wpm"] == 125
    assert len(result["analysis"]["tips"]) == 5