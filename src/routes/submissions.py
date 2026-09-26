from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Challenge, IntegrityEvent, Submission, User, db
from services.candidate_analyzer import analyze_submission
from services.anti_gaming import check_reproducibility, check_github_mocking

bp = Blueprint("submissions", __name__, url_prefix="/api/submissions")

INTEGRITY_PENALTY = {"tab_switch": 3, "paste_attempt": 5}


@bp.post("")
@jwt_required()
def create_submission():
    body = request.get_json(force=True) or {}
    submission = Submission(
        student_id=get_jwt_identity(),
        challenge_id=body["challenge_id"],
        github_url=body.get("github_url", ""),
        demo_url=body.get("demo_url", ""),
        architecture_doc=body.get("architecture_doc", ""),
        decisions=body.get("decisions", ""),
        explanation=body.get("explanation", ""),
        repo_age_days=body.get("repo_age_days", 0),
        commit_count=body.get("commit_count", 0),
    )
    db.session.add(submission)
    db.session.flush()

    # Anti-gaming: reproducibility
    repro = check_reproducibility(submission)
    submission.build_passed = repro["passed"]
    submission.build_log = repro["reason"]

    # Anti-gaming: GitHub mocking
    gh = check_github_mocking(submission)
    if not gh["passed"]:
        submission.github_flag = gh.get("flag", "")
        submission.integrity_score = max(0, submission.integrity_score - 20)

    # Cold-start calibration
    challenge = Challenge.query.get(submission.challenge_id)
    if challenge and challenge.is_calibration and submission.build_passed:
        user = User.query.get(submission.student_id)
        if user:
            user.is_calibrated = True

    # AI analyzer
    try:
        analyze_submission(submission)
    except Exception:
        pass

    submission.recompute_proof_score()
    db.session.commit()
    return jsonify(submission.to_dict(include_analysis=True)), 201


@bp.post("/<submission_id>/build-check")
@jwt_required()
def run_build_check(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    repro = check_reproducibility(submission)
    submission.build_passed = repro["passed"]
    submission.build_log = repro["reason"]
    submission.recompute_proof_score()
    db.session.commit()
    return jsonify({"build_passed": submission.build_passed, "log": submission.build_log})


@bp.post("/<submission_id>/integrity-event")
@jwt_required()
def log_integrity_event(submission_id):
    body = request.get_json(force=True) or {}
    event_type = body.get("event_type", "unknown")
    submission = Submission.query.get_or_404(submission_id)

    event = IntegrityEvent(
        submission_id=submission.id,
        event_type=event_type,
        severity=INTEGRITY_PENALTY.get(event_type, 1),
    )
    db.session.add(event)

    submission.integrity_score = max(0, submission.integrity_score - event.severity)
    submission.recompute_proof_score()
    db.session.commit()

    return jsonify({
        "logged": True,
        "integrity_score": submission.integrity_score,
        "note": "Routed for human review, not auto-rejected.",
    })


@bp.get("/<submission_id>")
def get_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    return jsonify(submission.to_dict(include_analysis=True))
