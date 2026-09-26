from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Challenge, Submission, User

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.get("/student")
@jwt_required()
def student_dashboard():
    student_id = get_jwt_identity()
    subs = Submission.query.filter_by(student_id=student_id).all()
    return jsonify([s.to_dict(include_analysis=True) for s in subs])


@bp.get("/submission/<submission_id>/explain")
@jwt_required()
def explain_score(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    challenge = Challenge.query.get(submission.challenge_id)
    user = User.query.get(submission.student_id)

    age_months = (datetime.utcnow() - submission.created_at).days / 30
    recency = 0.5 ** (age_months / 6)
    diff_mult = {"easy": 1.0, "medium": 1.25, "hard": 1.5}.get(
        challenge.difficulty if challenge else "medium", 1.0
    )

    user_subs = Submission.query.filter_by(student_id=user.id).all()
    all_tags = set()
    for s in user_subs:
        ch = Challenge.query.get(s.challenge_id)
        if ch and ch.tags:
            all_tags.update(t.strip() for t in ch.tags.split(",") if t.strip())
    breadth = min(1.0 + (len(all_tags) * 0.05), 1.3)

    base = round(
        submission.technical_score * 0.35
        + submission.architecture_score * 0.20
        + submission.review_score * 0.20
        + submission.integrity_score * 0.15
        + submission.explanation_score * 0.10,
        2,
    )

    return jsonify({
        "proof_score": submission.proof_score,
        "breakdown": {
            "base_score": base,
            "difficulty_multiplier": diff_mult,
            "difficulty_label": challenge.difficulty if challenge else "medium",
            "recency_factor": round(recency, 3),
            "age_months": round(age_months, 1),
            "breadth_bonus": round(breadth, 3),
            "distinct_domains": len(all_tags),
        },
        "trust_signals": {
            "institution_verified": user.verified_by_institution,
            "calibrated": user.is_calibrated,
            "build_passed": submission.build_passed,
            "github_flag": submission.github_flag,
            "integrity_score": submission.integrity_score,
        },
    })


@bp.get("/leaderboard")
@jwt_required()
def leaderboard():
    """
    Ranks every student by their single best proof_score. Available to any
    logged-in role: students use it to see their own position among peers,
    recruiters/experts/institutions use it as a quick talent ranking.
    """
    students = User.query.filter_by(role="student").all()
    rows = []
    for student in students:
        subs = Submission.query.filter_by(student_id=student.id).all()
        best = max((s.proof_score for s in subs), default=0)
        rows.append({
            "student_id": student.id,
            "name": student.name,
            "track": student.track,
            "headline": student.headline,
            "verified_by_institution": student.verified_by_institution,
            "is_calibrated": student.is_calibrated,
            "best_proof_score": round(best, 1),
            "projects": len(subs),
        })
    rows.sort(key=lambda r: r["best_proof_score"], reverse=True)
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return jsonify(rows)
