from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from models import Challenge, db

bp = Blueprint("challenges", __name__, url_prefix="/api/challenges")


@bp.get("")
def list_challenges():
    include_calibration = request.args.get("include_calibration", "false") == "true"
    query = Challenge.query
    if not include_calibration:
        query = query.filter_by(is_calibration=False)
    return jsonify([c.to_dict() for c in query.all()])


@bp.post("")
@jwt_required()
def create_challenge():
    body = request.get_json(force=True) or {}
    challenge = Challenge(
        title=body["title"],
        description=body.get("description", ""),
        tags=body.get("tags", ""),
        difficulty=body.get("difficulty", "medium"),
        is_calibration=body.get("is_calibration", False),
        track=body.get("track", "technical"),
    )
    db.session.add(challenge)
    db.session.commit()
    return jsonify(challenge.to_dict()), 201
