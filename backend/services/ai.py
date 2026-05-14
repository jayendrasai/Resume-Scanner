import os
import json
import re
from groq import Groq
from openai import OpenAI

# ── clients ────────────────────────────────────────────────────────────────

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
    print(f"[AI] OpenRouter fallback triggered for: {context_label}")
    for model_name in OPENROUTER_FALLBACK_MODELS:
        print(f"[AI] Trying {model_name}")
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
                raise ValueError("Empty choices")
            content = completion.choices[0].message.content
            if not content:
                raise ValueError("Empty content")
            print(f"[AI] Success with {model_name}")
            return parse_llm_json(content)
        except Exception as e:
            print(f"[AI] {model_name} failed: {e}")
            continue

    return {
        "match_score": 0,
        "missing_keywords": ["API Error: Could not analyze"],
        "tips": ["Please try again later. All AI services are currently unavailable."]
    }


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
        print(f"[AI] Groq failed ({e}) → OpenRouter fallback")
        return call_openrouter_fallback(
            RESUME_SYSTEM_PROMPT,
            user_content,
            context_label="resume"
        )


# ── video interview analysis (Phase 2 — Day 6 fills this out) ─────────────

INTERVIEW_SYSTEM_PROMPT = """
You are an expert communication coach analyzing a job interview response.
Analyze the transcript and return ONLY a valid JSON object matching this schema:

{
  "filler_words": {
    "um": <count>,
    "uh": <count>,
    "like": <count>,
    "you know": <count>,
    "so": <count>
  },
  "pace_wpm": <integer words per minute>,
  "clarity_score": <integer 0-100>,
  "tips": ["tip1", "tip2", "tip3", "tip4", "tip5"]
}
"""


def analyze_transcript_with_ai(transcript: str, duration_seconds: float) -> dict:
    """
    Called by Celery worker after Whisper transcription.
    Day 6 wires this into the task pipeline.
    """
    word_count = len(transcript.split())
    duration_minutes = max(duration_seconds / 60, 0.1)
    estimated_wpm = int(word_count / duration_minutes)

    user_content = (
        f"Interview transcript ({word_count} words, "
        f"~{estimated_wpm} WPM estimated):\n\n{transcript}"
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
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"[AI] Groq transcript analysis failed ({e}) → OpenRouter fallback")
        return call_openrouter_fallback(
            INTERVIEW_SYSTEM_PROMPT,
            user_content,
            context_label="transcript"
        )