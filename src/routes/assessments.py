from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Assessment, AssessmentAttempt, User, db
from services.anti_gaming import (
    SEVERITY,
    check_single_active_session,
    score_attempt_integrity,
    score_keystroke_cadence,
)

bp = Blueprint("assessments", __name__, url_prefix="/api/assessments")


@bp.post("")
@jwt_required()
def create_assessment():
    body = request.get_json(force=True) or {}
    user = User.query.get(get_jwt_identity())
    if user.role not in ("recruiter", "institution"):
        return jsonify({"error": "Only recruiters/institutions can create assessments"}), 403
    a = Assessment(
        created_by=user.id,
        title=body.get("title", "Untitled"),
        description=body.get("description", ""),
        duration_minutes=body.get("duration_minutes", 60),
        sent_to=body.get("sent_to"),
    )
    db.session.add(a)
    db.session.commit()
    return jsonify({"id": a.id, "title": a.title}), 201


@bp.get("")
@jwt_required()
def list_assessments():
    user = User.query.get(get_jwt_identity())
    if user.role == "student":
        assessments = Assessment.query.filter(
            (Assessment.sent_to == None) | (Assessment.sent_to == user.id)
        ).all()
    else:
        assessments = Assessment.query.filter_by(created_by=user.id).all()
    return jsonify([{
        "id": a.id, "title": a.title, "description": a.description,
        "duration_minutes": a.duration_minutes, "status": a.status,
    } for a in assessments])


@bp.post("/<assessment_id>/start")
@jwt_required()
def start_attempt(assessment_id):
    student_id = get_jwt_identity()
    assessment = Assessment.query.get_or_404(assessment_id)

    # --- integrity: one live session per (assessment, student) ---
    existing = check_single_active_session(assessment_id, student_id)
    if existing:
        return jsonify({
            "attempt_id": existing.id,
            "session_token": existing.session_token,
            "status": existing.status,
            "resumed": True,
            "note": "An attempt is already in progress for this assessment. "
                    "Re-opening it here rather than starting a second, unmonitored copy.",
        }), 200

    device_label = request.headers.get("User-Agent", "unknown")[:180]
    attempt = AssessmentAttempt(
        assessment_id=assessment_id,
        student_id=student_id,
        device_label=device_label,
    )
    db.session.add(attempt)
    db.session.commit()
    return jsonify({
        "attempt_id": attempt.id,
        "session_token": attempt.session_token,
        "status": attempt.status,
        "title": assessment.title,
        "description": assessment.description,
        "duration_minutes": assessment.duration_minutes,
        "resumed": False,
    }), 201


@bp.post("/attempts/<attempt_id>/event")
@jwt_required()
def log_integrity_event(attempt_id):
    """
    Proctor.js posts one small JSON event at a time here:
      { "type": "focus_loss" | "paste_no_history" | "devtools_suspected" |
                "fullscreen_exit" | "context_menu_blocked" | "cadence_check",
        "detail": "free text", "session_token": "...",
        "intervals_ms": [..]  // only for type == "cadence_check"
      }
    Never trust the client's own severity/score -- only the event type is
    read, severity comes from the server-side table.
    """
    student_id = get_jwt_identity()
    attempt = AssessmentAttempt.query.get_or_404(attempt_id)
    if attempt.student_id != student_id:
        return jsonify({"error": "Not your attempt."}), 403

    body = request.get_json(force=True) or {}
    if body.get("session_token") and body["session_token"] != attempt.session_token:
        # Someone has this attempt open in a second tab/device with a stale token.
        attempt.add_flag("second_session_blocked", "stale session_token on event", 0)
        db.session.commit()
        return jsonify({"error": "Stale session. Reload the assessment."}), 409

    event_type = body.get("type", "")

    if event_type == "cadence_check":
        intervals = body.get("intervals_ms", [])
        is_anomalous, reason = score_keystroke_cadence(intervals)
        if is_anomalous:
            attempt.add_flag("cadence_anomaly", reason, SEVERITY["cadence_anomaly"])
    elif event_type in SEVERITY:
        attempt.add_flag(event_type, body.get("detail", ""), SEVERITY[event_type])
    else:
        return jsonify({"error": f"Unknown event type '{event_type}'"}), 400

    db.session.commit()
    return jsonify({"integrity_score": attempt.integrity_score}), 200


@bp.post("/attempts/<attempt_id>/submit")
@jwt_required()
def submit_attempt(attempt_id):
    from datetime import datetime

    body = request.get_json(force=True) or {}
    attempt = AssessmentAttempt.query.get_or_404(attempt_id)
    student_id = get_jwt_identity()
    if attempt.student_id != student_id:
        return jsonify({"error": "Not your attempt."}), 403

    attempt.answer_text = body.get("answer_text", "")
    attempt.score = body.get("score", 0)
    attempt.status = "completed"
    attempt.submitted_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "attempt_id": attempt.id,
        "score": attempt.score,
        "status": attempt.status,
        "integrity_score": attempt.integrity_score,
        "integrity_summary": score_attempt_integrity(attempt),
    })


@bp.get("/<assessment_id>/attempts")
@jwt_required()
def list_attempts(assessment_id):
    """Creator-only: every attempt on one assessment, with integrity trail."""
    user = User.query.get(get_jwt_identity())
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment.created_by != user.id:
        return jsonify({"error": "Only the creator can view attempts."}), 403
    attempts = AssessmentAttempt.query.filter_by(assessment_id=assessment_id).all()
    out = []
    for a in attempts:
        student = User.query.get(a.student_id)
        d = a.to_dict(include_flags=True)
        d["student_name"] = student.name if student else "Unknown"
        out.append(d)
    return jsonify(out)


@bp.get("/attempts/<attempt_id>")
@jwt_required()
def get_attempt(attempt_id):
    """Reviewer/recruiter/institution view of one attempt's integrity trail."""
    user = User.query.get(get_jwt_identity())
    attempt = AssessmentAttempt.query.get_or_404(attempt_id)
    if user.role == "student" and attempt.student_id != user.id:
        return jsonify({"error": "Not your attempt."}), 403
    d = attempt.to_dict(include_flags=(user.role != "student"))
    d["answer_text"] = attempt.answer_text if user.role != "student" else None
    return jsonify(d)
