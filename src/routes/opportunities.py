from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Invitation, Opportunity, User, db

bp = Blueprint("opportunities", __name__, url_prefix="/api")


def _require_role(role):
    user = User.query.get(get_jwt_identity())
    if not user or user.role != role:
        return None
    return user


# ---------------------------------------------------------------------------
# Recruiter side: create opportunities, invite candidates, track responses.
# ---------------------------------------------------------------------------

@bp.get("/recruiter/opportunities")
@jwt_required()
def list_opportunities():
    recruiter = _require_role("recruiter")
    if not recruiter:
        return jsonify({"error": "Recruiter role required"}), 403
    opps = (
        Opportunity.query.filter_by(recruiter_id=recruiter.id)
        .order_by(Opportunity.created_at.desc())
        .all()
    )
    return jsonify([o.to_dict(include_invitations=True) for o in opps])


@bp.post("/recruiter/opportunities")
@jwt_required()
def create_opportunity():
    recruiter = _require_role("recruiter")
    if not recruiter:
        return jsonify({"error": "Recruiter role required"}), 403
    body = request.get_json(force=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    opp = Opportunity(recruiter_id=recruiter.id, title=title, description=body.get("description", ""))
    db.session.add(opp)
    db.session.commit()
    return jsonify(opp.to_dict()), 201


@bp.post("/recruiter/candidates/<student_id>/invite")
@jwt_required()
def invite_candidate(student_id):
    """Directly initiate an opportunity with a candidate found through discovery.

    Accepts either an existing `opportunity_id`, or a `title` (+ optional
    `description`) to create a new opportunity in the same call, so a
    recruiter can invite straight from the candidate room without a
    separate trip to set up the opportunity first.
    """
    recruiter = _require_role("recruiter")
    if not recruiter:
        return jsonify({"error": "Recruiter role required"}), 403

    student = User.query.get_or_404(student_id)
    if student.role != "student":
        return jsonify({"error": "Invitations can only be sent to students"}), 400

    body = request.get_json(force=True) or {}
    opportunity_id = body.get("opportunity_id")

    if opportunity_id:
        opp = Opportunity.query.get_or_404(opportunity_id)
        if opp.recruiter_id != recruiter.id:
            return jsonify({"error": "You can only invite candidates to your own opportunities"}), 403
    else:
        title = (body.get("title") or "").strip()
        if not title:
            return jsonify({"error": "opportunity_id or title is required"}), 400
        opp = Opportunity(recruiter_id=recruiter.id, title=title, description=body.get("description", ""))
        db.session.add(opp)
        db.session.flush()

    existing = Invitation.query.filter_by(opportunity_id=opp.id, student_id=student.id).first()
    if existing:
        return jsonify({"error": "This candidate has already been invited to this opportunity"}), 409

    invite = Invitation(
        opportunity_id=opp.id,
        student_id=student.id,
        message=body.get("message", ""),
    )
    db.session.add(invite)
    db.session.commit()
    return jsonify(invite.to_dict()), 201


@bp.get("/recruiter/invitations")
@jwt_required()
def recruiter_sent_invitations():
    recruiter = _require_role("recruiter")
    if not recruiter:
        return jsonify({"error": "Recruiter role required"}), 403
    opp_ids = [o.id for o in Opportunity.query.filter_by(recruiter_id=recruiter.id).all()]
    invites = (
        Invitation.query.filter(Invitation.opportunity_id.in_(opp_ids))
        .order_by(Invitation.created_at.desc())
        .all()
        if opp_ids
        else []
    )
    return jsonify([i.to_dict() for i in invites])


# ---------------------------------------------------------------------------
# Student side: view invitations, accept or decline.
# ---------------------------------------------------------------------------

@bp.get("/student/invitations")
@jwt_required()
def student_invitations():
    uid = get_jwt_identity()
    invites = (
        Invitation.query.filter_by(student_id=uid)
        .order_by(Invitation.created_at.desc())
        .all()
    )
    return jsonify([i.to_dict() for i in invites])


@bp.post("/student/invitations/<invitation_id>/respond")
@jwt_required()
def respond_to_invitation(invitation_id):
    uid = get_jwt_identity()
    invite = Invitation.query.get_or_404(invitation_id)
    if invite.student_id != uid:
        return jsonify({"error": "This invitation does not belong to you"}), 403
    status = (request.get_json(force=True) or {}).get("status")
    if status not in ("accepted", "declined"):
        return jsonify({"error": "status must be 'accepted' or 'declined'"}), 400
    invite.status = status
    invite.responded_at = datetime.utcnow()
    db.session.commit()
    return jsonify(invite.to_dict())
