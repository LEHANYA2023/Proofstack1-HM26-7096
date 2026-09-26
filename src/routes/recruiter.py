from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import Submission, User, Challenge, Review
from services.candidate_analyzer import analyze_submission
from models import db

bp = Blueprint("recruiter", __name__, url_prefix="/api/recruiter")

def candidate_item(candidate):
    subs = Submission.query.filter_by(student_id=candidate.id).order_by(Submission.proof_score.desc()).all()
    evidence = []
    for s in subs:
        ch = Challenge.query.get(s.challenge_id)
        evidence.append({
            "submission_id": s.id, "project": ch.title if ch else "Project", "track": ch.track if ch else candidate.track,
            "github_url": s.github_url, "demo_url": s.demo_url, "proof_score": s.proof_score,
            "build_passed": s.build_passed, "integrity_score": s.integrity_score,
            "ai_analysis": s.to_dict(include_analysis=True).get("ai_analysis"),
        })
    best = subs[0] if subs else None
    return {"candidate": candidate.to_dict(), "evidence": evidence, "summary": {
        "projects": len(subs), "best_proof_score": best.proof_score if best else 0,
        "verified": candidate.verified_by_institution, "calibrated": candidate.is_calibrated,
        "technical_score": best.technical_score if best else None, "track": candidate.track,
    }}

@bp.get("/candidates")
@jwt_required()
def search_candidates():
    viewer = User.query.get(get_jwt_identity())
    if viewer.role != "recruiter":
        return jsonify({"error": "Recruiter role required"}), 403
    min_proof = request.args.get("min_proof_score", type=float)
    skill = request.args.get("skill", "").strip().lower()
    track = request.args.get("track", "").strip().lower()
    query = User.query.filter_by(role="student")
    results = []
    for candidate in query.all():
        item = candidate_item(candidate)
        if min_proof is not None and item["summary"]["best_proof_score"] < min_proof: continue
        if skill and skill not in candidate.skills.lower(): continue
        if track and candidate.track.lower() != track: continue
        results.append(item)
    sort_by = request.args.get("sort_by", "evidence")
    if sort_by == "name": results.sort(key=lambda x: x["candidate"]["name"].lower())
    elif sort_by == "readiness": results.sort(key=lambda x: (x["summary"]["projects"], x["summary"]["verified"], x["summary"]["best_proof_score"]), reverse=True)
    else: results.sort(key=lambda x: (x["summary"]["best_proof_score"], x["summary"]["projects"]), reverse=True)
    return jsonify({"count": len(results), "candidates": results})

@bp.get("/candidates/<student_id>")
@jwt_required()
def candidate_detail(student_id):
    candidate = User.query.get_or_404(student_id)
    return jsonify(candidate_item(candidate))

@bp.post("/candidates/<submission_id>/analyze")
@jwt_required()
def rerun_analysis(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    analyze_submission(submission); db.session.commit()
    return jsonify(submission.to_dict(include_analysis=True))
