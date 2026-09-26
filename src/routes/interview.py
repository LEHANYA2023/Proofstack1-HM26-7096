from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import InterviewSession, Submission, db

bp = Blueprint("interview", __name__, url_prefix="/api/interview")

# Fixed, rubric-driven prompts the AI interviewer asks the candidate about
# their own submission. The AI never issues a pass/fail verdict itself --
# it only produces a summary that a human reviewer reads alongside the score.
QUESTION_BANK = [
    "Walk me through the architecture decision you're proudest of in this submission.",
    "What was the hardest bug you hit, and how did you track it down?",
    "If you had another week, what would you change about this design?",
    "What alternative approach did you consider and reject? Why?",
]


@bp.post("/<submission_id>/start")
@jwt_required()
def start_interview(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    session = InterviewSession(
        submission_id=submission.id,
        candidate_id=get_jwt_identity(),
    )
    session.append_turn("interviewer", QUESTION_BANK[0])
    db.session.add(session)
    db.session.commit()
    return jsonify(session.to_dict()), 201


@bp.post("/<session_id>/respond")
@jwt_required()
def respond(session_id):
    body = request.get_json(force=True) or {}
    session = InterviewSession.query.get_or_404(session_id)
    session.append_turn("candidate", body.get("message", ""))

    answered = len([t for t in session.get_transcript() if t["role"] == "interviewer"])
    if answered < len(QUESTION_BANK):
        session.append_turn("interviewer", QUESTION_BANK[answered])
    else:
        session.status = "awaiting_human_review"

    db.session.commit()
    return jsonify(session.to_dict())


@bp.get("/<session_id>")
@jwt_required()
def get_session(session_id):
    session = InterviewSession.query.get_or_404(session_id)
    return jsonify(session.to_dict())


@bp.get("/for-submission/<submission_id>")
@jwt_required()
def get_session_for_submission(submission_id):
    """Latest interview session tied to a submission, or an empty stub if none started yet."""
    session = (
        InterviewSession.query.filter_by(submission_id=submission_id)
        .order_by(InterviewSession.created_at.desc())
        .first()
    )
    if not session:
        return jsonify({"exists": False})
    d = session.to_dict()
    d["exists"] = True
    return jsonify(d)
