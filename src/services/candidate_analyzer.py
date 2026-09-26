"""
AI candidate analyzer.

Uses NVIDIA Nemotron 3.5 Lightning via OpenRouter when OPENROUTER_API_KEY is
set. Falls back to a deterministic local "stub" analysis with zero API calls
so the whole demo runs offline with no keys configured.
"""
import json
import os

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nvidia/nemotron-3.5-lightning"


def _stub_analysis(submission):
    """Deterministic, keyword-based fallback analysis. No network calls."""
    text = f"{submission.architecture_doc} {submission.decisions} {submission.explanation}".lower()

    role_fit = "Backend"
    if any(k in text for k in ["react", "frontend", "ui", "css"]):
        role_fit = "Frontend"
    if any(k in text for k in ["ml", "model", "tensorflow", "pytorch", "gradient"]):
        role_fit = "ML / AI"

    strengths = []
    if "trade-off" in text or "tradeoff" in text or "considered" in text:
        strengths.append("Shows explicit trade-off reasoning")
    if "debug" in text or "race condition" in text or "fixed" in text:
        strengths.append("Demonstrates real debugging experience")
    if not strengths:
        strengths.append("Submission includes an architecture writeup")

    summary = (
        f"Candidate appears strongest in {role_fit.lower()} work based on their "
        f"submission writeup. {strengths[0]}."
    )

    return {
        "summary": summary,
        "role_fit": role_fit,
        "strengths": strengths,
        "risk_flags": [] if submission.build_passed else ["Build did not pass"],
        "source": "stub",
    }


def analyze_submission(submission):
    """
    Populates submission.ai_analysis (JSON string) in place.
    Tries the live model first; falls back to the stub on any failure or
    when no API key is configured, so the app never hard-fails a submission
    because the AI call didn't work.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        submission.ai_analysis = json.dumps(_stub_analysis(submission))
        return

    prompt = (
        "You are a technical hiring analyst. Given this project submission, "
        "return ONLY a JSON object with keys: summary (1-2 sentences), "
        "role_fit (Backend/Frontend/ML/Full-stack), strengths (list of "
        "short strings), risk_flags (list of short strings).\n\n"
        f"Architecture: {submission.architecture_doc}\n"
        f"Decisions: {submission.decisions}\n"
        f"Explanation: {submission.explanation}\n"
    )

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
            },
            timeout=15,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        cleaned = content.strip().strip("`").replace("json\n", "", 1)
        parsed = json.loads(cleaned)
        parsed["source"] = "nemotron-3.5-lightning"
        submission.ai_analysis = json.dumps(parsed)
    except Exception:
        submission.ai_analysis = json.dumps(_stub_analysis(submission))
