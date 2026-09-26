from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Assessment, User, db

bp = Blueprint("institution", __name__, url_prefix="/api/institution")


@bp.get("/students")
@jwt_required()
def list_students():
    user = User.query.get(get_jwt_identity())
    if user.role != "institution":
        return jsonify({"error": "Institution role required"}), 403
    students = User.query.filter_by(institution_id=user.institution_id, role="student").all()
    return jsonify([s.to_dict() for s in students])


@bp.post("/students/<student_id>/verify")
@jwt_required()
def verify_student(student_id):
    user = User.query.get(get_jwt_identity())
    if user.role != "institution":
        return jsonify({"error": "Institution role required"}), 403
    student = User.query.get_or_404(student_id)
    student.verified_by_institution = True
    db.session.commit()
    return jsonify({"verified": True, "student": student.to_dict()})


@bp.post("/assessments")
@jwt_required()
def create_assessment():
    body = request.get_json(force=True) or {}
    user = User.query.get(get_jwt_identity())
    assessment = Assessment(
        created_by=user.id,
        title=body.get("title", "Untitled assessment"),
        description=body.get("description", ""),
        duration_minutes=body.get("duration_minutes", 60),
    )
    db.session.add(assessment)
    db.session.commit()
    return jsonify({"id": assessment.id, "title": assessment.title}), 201


@bp.get("/assessments")
@jwt_required()
def list_assessments():
    user = User.query.get(get_jwt_identity())
    assessments = Assessment.query.filter_by(created_by=user.id).all()
    return jsonify([{"id": a.id, "title": a.title, "status": a.status} for a in assessments])
