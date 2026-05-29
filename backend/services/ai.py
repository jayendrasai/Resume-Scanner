import os
import json
import re
from groq import Groq
from openai import OpenAI
from logger import log

# services/ai.py — add after imports, before existing functions

FILLER_WORDS = {
    "um": r"\bum\b",
    "uh": r"\buh\b",
    "like": r"\blike\b",
    "you know": r"\byou know\b",
    "so": r"\bso\b",
}

MIN_TRANSCRIPT_WORDS = 10


def count_filler_words(transcript: str) -> dict:
    """
    Deterministic string matching — never trust LLM to count tokens.
    Case-insensitive, whole-word matches only.
    Returns counts for every filler regardless of whether count is zero.
    """
    text = transcript.lower()
    return {
        filler: len(re.findall(pattern, text))
        for filler, pattern in FILLER_WORDS.items()
    }


def validate_transcript(transcript: str) -> None:
    """
    Raises ValueError immediately if transcript is unusable.
    Caller (Celery task) catches this and fails the task with a clear message.
    No retry — a silent/corrupted video won't improve on retry.
    """
    if not transcript or not transcript.strip():
        log.error("Transcript is empty. The video may be silent or contain no speech.")
        raise ValueError(
            "Transcript is empty. The video may be silent or contain no speech."
        )
    word_count = len(transcript.strip().split())
    if word_count < MIN_TRANSCRIPT_WORDS:
        log.error(f"Transcript too short ({word_count} words). Minimum 10 words required for meaningful analysis. Check that the video contains clear speech.")
        raise ValueError(
            f"Transcript too short ({word_count} words). "
            "Minimum 10 words required for meaningful analysis. "
            "Check that the video contains clear speech."
        )

# ── clients ────────────────────-───────────────────────────────────────────

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# ── JSON safety ─────────────────────────────────────────────────────────────

def parse_llm_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            log.error("No JSON found in LLM response", text=text)
            raise ValueError("No JSON found in LLM response")
        cleaned = match.group(0).replace("\n", " ").replace("\t", " ")
        return json.loads(cleaned)


# ── resume analysis (Phase 1 logic — untouched) ────────────────────────────

RESUME_SYSTEM_PROMPT = """
You are a Senior Technical Recruiter and ATS Optimization Expert.
Your task is to conduct a high-fidelity GAP analysis between a Job Description (JD) and a Resume.

CRITICAL INSTRUCTIONS:
1. SCORING RUBRIC: Calculate a single overall match score from 0 to 100. Weigh your calculation based on:
   - Hard Skills (50%): Tech stack, tools, platforms.
   - Experience (30%): Relevance of past roles.
   - Soft Skills/Education (20%): Leadership, degrees.
2. MISSING KEYWORDS: Identify specific technical terms present in the JD but missing from the resume.
3. TIPS: Provide exactly 5 actionable suggestions. These MUST be plain text strings.
4. FORMAT: Return ONLY a valid JSON object exactly matching the schema below.

EXPECTED JSON SCHEMA:
{
  "match_score": <integer between 0 and 100>,
  "missing_keywords": ["keyword1", "keyword2"],
  "tips": ["string1", "string2", "string3", "string4", "string5"]
}
"""

OPENROUTER_FALLBACK_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "minimax/minimax-m2.5:free",
    "qwen/qwen3-coder:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
]


def call_openrouter_fallback(
    system_prompt: str,
    user_content: str,
    context_label: str = "resume"
) -> dict:
    log.info(f"OpenRouter fallback triggered for: {context_label}")
    for model_name in OPENROUTER_FALLBACK_MODELS:
        log.info(f"Trying {model_name}")
        try:
            completion = openrouter_client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Resume AI Scanner",
                },
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            if not getattr(completion, "choices", None):
                log.error("Empty choices")
                raise ValueError("Empty choices")
            content = completion.choices[0].message.content
            if not content:
                log.error("Empty content")
                raise ValueError("Empty content")
            log.info(f"Success with {model_name}")
            return parse_llm_json(content)
        except Exception as e:
            log.error(f" {model_name} failed: ", e)
            continue

    log.error("All AI services are currently unavailable.")
    return {
        "match_score": 0,
        "missing_keywords": ["API Error: Could not analyze"],
        "tips": ["Please try again later. All AI services are currently unavailable."]
    }


# services/ai.py — add before analyze_resume_with_ai

MAX_JD_LENGTH = 5000  # characters
MAX_RESUME_LENGTH = 15000

def sanitize_llm_input(text: str, max_length: int, field_name: str) -> str:
    """
    Strips null bytes, excessive whitespace, and truncates to max length.
    Does not block content — LLM handles adversarial prompts via system
    prompt isolation. This prevents token bloat and injection via length.
    """
    if not text or not text.strip():
        log.error(f"{field_name} cannot be empty")
        raise ValueError(f"{field_name} cannot be empty")
    # Strip null bytes — can cause encoding issues
    cleaned = text.replace('\x00', '')
    # Collapse excessive whitespace
    cleaned = ' '.join(cleaned.split())
    # Truncate — prevents token limit abuse
    if len(cleaned) > max_length:
        log.warning(f"{field_name} is too long. Truncating to {max_length} characters.")
        cleaned = cleaned[:max_length]
    return cleaned

def analyze_resume_with_ai(job_description: str, resume_text: str) -> dict:
    """Called by FastAPI /analyze endpoint — Phase 1 logic unchanged."""
    user_content = f"JD: {job_description}\n\nResume: {resume_text}"
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatileqqqq",
            messages=[
                {"role": "system", "content": RESUME_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        log.error(f"Groq failed ({e}) → OpenRouter fallback")
        return call_openrouter_fallback(
            RESUME_SYSTEM_PROMPT,
            user_content,
            context_label="resume"
        )


# ── video interview analysis (Phase 2 — Day 6 fills this out) ─────────────

INTERVIEW_SYSTEM_PROMPT = """
You are an expert communication coach analyzing a recorded job interview response.
You will receive a transcript and metadata including estimated speaking pace and filler word counts.

Your task is to assess communication quality and return ONLY a valid JSON object.

CRITICAL INSTRUCTIONS:
1. pace_wpm: Estimate actual speaking pace as an integer (words per minute).
   Use the metadata estimate as a reference but adjust based on transcript complexity.
2. clarity_score: Score overall communication clarity from 0 to 100.
   Consider: sentence structure, vocabulary appropriateness, logical flow,
   conciseness, and absence of rambling. 70+ is good, 50-69 needs work, below 50 is poor.
3. tips: Provide exactly 5 specific, actionable improvement suggestions as plain strings.
   Reference specific patterns you observe in the transcript.
   Do NOT give generic advice like "speak more clearly".

RETURN ONLY this JSON schema — no markdown, no explanation:
{
  "pace_wpm": <integer>,
  "clarity_score": <integer 0-100>,
  "tips": ["specific tip 1", "specific tip 2", "specific tip 3", "specific tip 4", "specific tip 5"]
}
"""


def analyze_transcript_with_ai(
    transcript: str,
    duration_seconds: float
) -> dict:
    """
    Receives validated transcript from Celery worker.
    Filler words counted deterministically here — not by LLM.
    LLM handles: pace_wpm, clarity_score, tips (semantic tasks only).
    """
    word_count = len(transcript.split())
    duration_minutes = max(duration_seconds / 60, 0.1)
    estimated_wpm = int(word_count / duration_minutes)

    # Deterministic counts — computed before LLM call
    filler_counts = count_filler_words(transcript)
    total_fillers = sum(filler_counts.values())

    user_content = (
        f"Interview transcript:\n\n{transcript}\n\n"
        f"Metadata: {word_count} words, "
        f"{duration_seconds:.1f} seconds duration, "
        f"estimated {estimated_wpm} WPM, "
        f"{total_fillers} total filler words detected."
    )

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": INTERVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        llm_result = json.loads(completion.choices[0].message.content)

    except Exception as e:
        log.error(f"Groq transcript analysis failed ({e}) → OpenRouter fallback")
        llm_result = call_openrouter_fallback(
            INTERVIEW_SYSTEM_PROMPT,
            user_content,
            context_label="transcript"
        )

    # Merge: use deterministic filler counts, LLM handles everything else
    return {
        "filler_words": filler_counts,
        "pace_wpm": llm_result.get("pace_wpm", estimated_wpm),
        "clarity_score": llm_result.get("clarity_score", 0),
        "tips": llm_result.get("tips", []),
    }