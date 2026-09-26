from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Review, Submission, db
from services.anti_gaming import check_reviewer_collusion

bp = Blueprint("reviews", __name__, url_prefix="/api/reviews")


@bp.post("/<submission_id>")
@jwt_required()
def submit_review(submission_id):
    body = request.get_json(force=True) or {}
    reviewer_id = get_jwt_identity()

    collusion = check_reviewer_collusion(reviewer_id, submission_id)
    if not collusion["passed"]:
        return jsonify({"error": collusion["reason"]}), 403

    submission = Submission.query.get_or_404(submission_id)

    review = Review(
        submission_id=submission.id,
        reviewer_id=reviewer_id,
        technical=body.get("technical", 0),
        architecture=body.get("architecture", 0),
        debugging=body.get("debugging", 0),
        explanation=body.get("explanation", 0),
        comments=body.get("comments", ""),
    )
    db.session.add(review)

    submission.technical_score = review.technical * 20
    submission.architecture_score = review.architecture * 20
    submission.review_score = ((review.technical + review.architecture + review.debugging) / 3) * 20
    submission.explanation_score = max(submission.explanation_score, review.explanation * 20)
    submission.recompute_proof_score()

    db.session.commit()
    return jsonify(submission.to_dict()), 201

@bp.get("/<submission_id>")
@jwt_required()
def get_reviews(submission_id):
    reviews = Review.query.filter_by(submission_id=submission_id).order_by(Review.created_at.desc()).all()
    out = []
    for r in reviews:
        reviewer = __import__('models').User.query.get(r.reviewer_id)
        out.append({
            "id": r.id, "reviewer": reviewer.name if reviewer else "Reviewer", "reviewer_role": reviewer.role if reviewer else "expert",
            "technical": r.technical, "architecture": r.architecture, "debugging": r.debugging, "explanation": r.explanation,
            "comments": r.comments, "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return jsonify(out)
