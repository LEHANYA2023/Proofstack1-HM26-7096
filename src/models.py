import json
import uuid
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _uid():
    return str(uuid.uuid4())


class Organization(db.Model):
    __tablename__ = "organizations"
    id = db.Column(db.String, primary_key=True, default=_uid)
    name = db.Column(db.String, nullable=False)
    type = db.Column(db.String, default="institution")  # institution | company
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String, primary_key=True, default=_uid)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)  # student | expert | recruiter | institution
    skills = db.Column(db.String, default="")
    institution_id = db.Column(db.String, db.ForeignKey("organizations.id"), nullable=True)
    verified_by_institution = db.Column(db.Boolean, default=False)
    is_calibrated = db.Column(db.Boolean, default=False)
    track = db.Column(db.String, default="technical")  # technical | non-technical | hybrid
    headline = db.Column(db.String, default="")
    bio = db.Column(db.Text, default="")
    resume_url = db.Column(db.String, default="")
    github_profile_url = db.Column(db.String, default="")
    portfolio_url = db.Column(db.String, default="")
    availability = db.Column(db.String, default="open_to_opportunities")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "skills": [s.strip() for s in self.skills.split(",") if s.strip()],
            "verified_by_institution": self.verified_by_institution,
            "is_calibrated": self.is_calibrated,
            "track": self.track,
            "headline": self.headline,
            "bio": self.bio,
            "resume_url": self.resume_url,
            "github_profile_url": self.github_profile_url,
            "portfolio_url": self.portfolio_url,
            "availability": self.availability,
        }


class Challenge(db.Model):
    __tablename__ = "challenges"
    id = db.Column(db.String, primary_key=True, default=_uid)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, default="")
    tags = db.Column(db.String, default="")
    difficulty = db.Column(db.String, default="medium")  # easy | medium | hard
    is_calibration = db.Column(db.Boolean, default=False)
    track = db.Column(db.String, default="technical")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": [t.strip() for t in self.tags.split(",") if t.strip()],
            "difficulty": self.difficulty,
            "is_calibration": self.is_calibration,
            "track": self.track,
        }


class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.String, primary_key=True, default=_uid)
    student_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    challenge_id = db.Column(db.String, db.ForeignKey("challenges.id"), nullable=False)

    github_url = db.Column(db.String, default="")
    demo_url = db.Column(db.String, default="")
    architecture_doc = db.Column(db.Text, default="")
    decisions = db.Column(db.Text, default="")
    explanation = db.Column(db.Text, default="")

    technical_score = db.Column(db.Float, default=0)
    architecture_score = db.Column(db.Float, default=0)
    review_score = db.Column(db.Float, default=0)
    integrity_score = db.Column(db.Float, default=100)
    explanation_score = db.Column(db.Float, default=0)
    proof_score = db.Column(db.Float, default=0)

    build_passed = db.Column(db.Boolean, default=False)
    build_log = db.Column(db.Text, default="")
    repo_age_days = db.Column(db.Integer, default=0)
    commit_count = db.Column(db.Integer, default=0)
    github_flag = db.Column(db.String, default="")

    ai_analysis = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def recompute_proof_score(self):
        base = (
            self.technical_score * 0.35
            + self.architecture_score * 0.20
            + self.review_score * 0.20
            + self.integrity_score * 0.15
            + self.explanation_score * 0.10
        )

        challenge = Challenge.query.get(self.challenge_id)
        diff_mult = {"easy": 1.0, "medium": 1.25, "hard": 1.5}.get(
            challenge.difficulty if challenge else "medium", 1.0
        )

        # created_at is only populated by SQLAlchemy once this row is
        # flushed to the DB, so fall back to "now" (0 months old) if
        # recompute_proof_score() is called before that flush happens.
        reference_time = self.created_at or datetime.utcnow()
        age_months = (datetime.utcnow() - reference_time).days / 30
        recency = 0.5 ** (age_months / 6)

        user_subs = Submission.query.filter_by(student_id=self.student_id).all()
        all_tags = set()
        for s in user_subs:
            ch = Challenge.query.get(s.challenge_id)
            if ch and ch.tags:
                all_tags.update(t.strip() for t in ch.tags.split(",") if t.strip())
        breadth = min(1.0 + (len(all_tags) * 0.05), 1.3)

        if not self.build_passed:
            self.proof_score = 0.0
            return self.proof_score

        self.proof_score = round(base * diff_mult * recency * breadth, 2)
        return self.proof_score

    def to_dict(self, include_analysis=False):
        d = {
            "id": self.id,
            "student_id": self.student_id,
            "challenge_id": self.challenge_id,
            "github_url": self.github_url,
            "demo_url": self.demo_url,
            "architecture_doc": self.architecture_doc,
            "decisions": self.decisions,
            "explanation": self.explanation,
            "build_passed": self.build_passed,
            "github_flag": self.github_flag,
            "scores": {
                "technical": self.technical_score,
                "architecture": self.architecture_score,
                "review": self.review_score,
                "integrity": self.integrity_score,
                "explanation": self.explanation_score,
                "proof_score": self.proof_score,
            },
        }
        if include_analysis and self.ai_analysis:
            try:
                d["ai_analysis"] = json.loads(self.ai_analysis)
            except ValueError:
                d["ai_analysis"] = self.ai_analysis
        return d


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.String, primary_key=True, default=_uid)
    submission_id = db.Column(db.String, db.ForeignKey("submissions.id"), nullable=False)
    reviewer_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    technical = db.Column(db.Integer)
    architecture = db.Column(db.Integer)
    debugging = db.Column(db.Integer)
    explanation = db.Column(db.Integer)
    comments = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class IntegrityEvent(db.Model):
    __tablename__ = "integrity_events"
    id = db.Column(db.String, primary_key=True, default=_uid)
    submission_id = db.Column(db.String, db.ForeignKey("submissions.id"), nullable=False)
    event_type = db.Column(db.String)
    severity = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Assessment(db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.String, primary_key=True, default=_uid)
    created_by = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, default="")
    duration_minutes = db.Column(db.Integer, default=60)
    sent_to = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AssessmentAttempt(db.Model):
    __tablename__ = "assessment_attempts"
    id = db.Column(db.String, primary_key=True, default=_uid)
    assessment_id = db.Column(db.String, db.ForeignKey("assessments.id"), nullable=False)
    student_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    score = db.Column(db.Float, default=0)
    status = db.Column(db.String, default="in_progress")

    # --- integrity layer -------------------------------------------------
    # session_token binds this attempt to ONE browser tab on ONE device.
    # A second "start" call for the same assessment+student cannot mint a
    # second token while this one is in_progress (see check_single_active_session),
    # which is what actually stops "open it on my phone too" — no camera needed.
    session_token = db.Column(db.String, default=_uid)
    device_label = db.Column(db.String, default="")  # coarse UA string, not a fingerprint/identity signal
    integrity_score = db.Column(db.Float, default=100.0)
    flags = db.Column(db.Text, default="[]")  # JSON list of {type, detail, at}
    answer_text = db.Column(db.Text, default="")
    keystroke_log = db.Column(db.Text, default="[]")  # JSON list of inter-key intervals (ms), no content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)

    def get_flags(self):
        return json.loads(self.flags or "[]")

    def add_flag(self, event_type, detail="", severity=0.0):
        flags = self.get_flags()
        flags.append({
            "type": event_type,
            "detail": detail,
            "severity": severity,
            "at": datetime.utcnow().isoformat(),
        })
        self.flags = json.dumps(flags)
        self.integrity_score = max(0.0, round(self.integrity_score - severity, 1))

    def to_dict(self, include_flags=False):
        d = {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "student_id": self.student_id,
            "score": self.score,
            "status": self.status,
            "integrity_score": self.integrity_score,
        }
        if include_flags:
            d["flags"] = self.get_flags()
        return d


class Opportunity(db.Model):
    __tablename__ = "opportunities"
    id = db.Column(db.String, primary_key=True, default=_uid)
    recruiter_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Invitation(db.Model):
    __tablename__ = "invitations"
    id = db.Column(db.String, primary_key=True, default=_uid)
    opportunity_id = db.Column(db.String, db.ForeignKey("opportunities.id"), nullable=False)
    student_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String, default="sent")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InterviewSession(db.Model):
    __tablename__ = "interview_sessions"
    id = db.Column(db.String, primary_key=True, default=_uid)
    submission_id = db.Column(db.String, db.ForeignKey("submissions.id"), nullable=False)
    candidate_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    transcript = db.Column(db.Text, default="[]")
    status = db.Column(db.String, default="in_progress")
    ai_summary = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_transcript(self):
        return json.loads(self.transcript or "[]")

    def append_turn(self, role, content):
        t = self.get_transcript()
        t.append({"role": role, "content": content})
        self.transcript = json.dumps(t)

    def to_dict(self):
        d = {
            "id": self.id,
            "submission_id": self.submission_id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "transcript": self.get_transcript(),
        }
        if self.ai_summary:
            try:
                d["ai_summary"] = json.loads(self.ai_summary)
            except ValueError:
                d["ai_summary"] = self.ai_summary
        return d


class MentorMessage(db.Model):
    __tablename__ = "mentor_messages"
    id = db.Column(db.String, primary_key=True, default=_uid)
    student_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    expert_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    sender_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        sender = User.query.get(self.sender_id)
        return {
            "id": self.id,
            "student_id": self.student_id,
            "expert_id": self.expert_id,
            "sender_id": self.sender_id,
            "sender_name": sender.name if sender else "User",
            "message": self.message,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
