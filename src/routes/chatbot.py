import json, os
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
import requests
from models import User, Submission, db

bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nvidia/nemotron-3.5-lightning"

def local_reply(user, message):
    msg = message.lower()
    if any(k in msg for k in ["resume", "cv"]):
        return "For a fresher resume, lead with skills, proof of work, internships or coursework, measurable outcomes, and links to your strongest evidence. Keep claims specific and verifiable."
    if any(k in msg for k in ["non technical", "non-technical", "hr", "marketing", "design"]):
        return "ProofStack supports non-technical freshers too. Build evidence through case studies, writing, research, presentations, design work, event leadership, operations, communication, or domain projects—not only code repositories."
    if any(k in msg for k in ["github", "project"]):
        return "A strong project entry explains the problem, your exact contribution, decisions, evidence, and what you learned. A repository link is useful, but the quality and traceability of the work matter more than a link alone."
    if any(k in msg for k in ["interview", "skills"]):
        return "Pick one target role, identify 3 skill gaps, then create small evidence-backed tasks for each gap. Use mentor feedback before repeating the task."
    return f"I can help you improve your profile, evidence, skills, interview readiness, or role fit. Tell me what you want to strengthen, {user.name.split()[0]}."

@bp.post("")
@jwt_required()
def chat():
    user = User.query.get_or_404(get_jwt_identity())
    body = request.get_json(force=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"reply": local_reply(user, message), "source": "local"})
    prompt = f"You are ProofStack's career coach for a fresher. Role: {user.role}. Track: {user.track}. Skills: {user.skills}. Answer honestly, avoid inventing achievements, and give actionable advice. User: {message}"
    try:
        r = requests.post(OPENROUTER_URL, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 450}, timeout=15)
        r.raise_for_status()
        return jsonify({"reply": r.json()["choices"][0]["message"]["content"], "source": "ai"})
    except Exception:
        return jsonify({"reply": local_reply(user, message), "source": "local-fallback"})
