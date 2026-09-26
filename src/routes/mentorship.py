from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import User, MentorMessage, db

bp = Blueprint("mentorship", __name__, url_prefix="/api/mentorship")

@bp.get("/experts")
@jwt_required()
def experts():
    return jsonify([u.to_dict() for u in User.query.filter_by(role="expert").order_by(User.name).all()])

@bp.get("/threads")
@jwt_required()
def threads():
    uid = get_jwt_identity()
    user = User.query.get_or_404(uid)
    if user.role == "student":
        msgs = MentorMessage.query.filter_by(student_id=uid).order_by(MentorMessage.created_at.asc()).all()
    elif user.role == "expert":
        msgs = MentorMessage.query.filter_by(expert_id=uid).order_by(MentorMessage.created_at.asc()).all()
    else:
        return jsonify({"error": "Mentorship is available to students and experts."}), 403
    return jsonify([m.to_dict() for m in msgs])

@bp.get("/thread/<other_id>")
@jwt_required()
def thread(other_id):
    uid = get_jwt_identity()
    user = User.query.get_or_404(uid)
    other = User.query.get_or_404(other_id)
    if user.role == "student" and other.role == "expert":
        student_id, expert_id = uid, other_id
    elif user.role == "expert" and other.role == "student":
        student_id, expert_id = other_id, uid
    else:
        return jsonify({"error": "A private thread must be between a student and an expert."}), 400
    msgs = MentorMessage.query.filter_by(student_id=student_id, expert_id=expert_id).order_by(MentorMessage.created_at.asc()).all()
    return jsonify([m.to_dict() for m in msgs])

@bp.post("/message")
@jwt_required()
def message():
    uid = get_jwt_identity()
    body = request.get_json(force=True) or {}
    other_id = body.get("other_id")
    text = (body.get("message") or "").strip()
    if not text or not other_id:
        return jsonify({"error": "other_id and message are required"}), 400
    user = User.query.get_or_404(uid)
    other = User.query.get_or_404(other_id)
    if user.role == "student" and other.role == "expert":
        student_id, expert_id = uid, other_id
    elif user.role == "expert" and other.role == "student":
        student_id, expert_id = other_id, uid
    else:
        return jsonify({"error": "A private thread must be between a student and an expert."}), 400
    msg = MentorMessage(student_id=student_id, expert_id=expert_id, sender_id=uid, message=text, is_private=True)
    db.session.add(msg)
    db.session.commit()
    return jsonify(msg.to_dict()), 201
