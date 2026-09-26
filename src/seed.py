from werkzeug.security import generate_password_hash

from models import (
    Assessment, Challenge, MentorMessage, Organization, Review, Submission, User, db
)


def seed(drop_first=True):
    """
    Populates demo data: 4 portals, 5 demo accounts, challenges, submissions,
    reviews, a mentor thread, an assessment. Call inside an app context.
    Used by `python seed.py` (drop_first=True) and by app.py on first run
    (drop_first=False, only if users table is empty).
    """
    if drop_first:
        db.drop_all()
        db.create_all()

    org = Organization(
        name="Mysuru Institute of Technology",
        type="institution",
        verified=True,
    )
    db.session.add(org)
    db.session.flush()

    # ---- Students ----
    students = [
        User(
            name="Aarav Menon",
            email="student@proofstack.dev",
            password_hash=generate_password_hash("demo123"),
            role="student",
            skills="Python, Flask, ML, APIs",
            track="technical",
            headline="Backend & AI fresher",
            bio="Builds small, explainable systems and documents trade-offs.",
            resume_url="https://example.com/resumes/aarav.pdf",
            github_profile_url="https://github.com/aarav-menon",
            portfolio_url="https://aarav.example.com",
            institution_id=org.id,
            is_calibrated=True,
            verified_by_institution=True,
        ),
        User(
            name="Priya Sharma",
            email="priya@proofstack.dev",
            password_hash=generate_password_hash("demo123"),
            role="student",
            skills="React, JavaScript, UX research",
            track="hybrid",
            headline="Product-minded frontend fresher",
            bio="Combines interface work with user research and usability evidence.",
            resume_url="https://example.com/resumes/priya.pdf",
            github_profile_url="https://github.com/priya-sharma",
            portfolio_url="https://priya.example.com",
            institution_id=org.id,
            is_calibrated=True,
            verified_by_institution=True,
        ),
        User(
            name="Nandini Rao",
            email="nandini@proofstack.dev",
            password_hash=generate_password_hash("demo123"),
            role="student",
            skills="Research, communication, presentations, Excel",
            track="non-technical",
            headline="Research & operations fresher",
            bio="Builds evidence through research briefs, presentations, process maps.",
            resume_url="https://example.com/resumes/nandini.pdf",
            portfolio_url="https://nandini.example.com",
            institution_id=org.id,
            verified_by_institution=True,
        ),
        User(
            name="Rohan Das",
            email="rohan@proofstack.dev",
            password_hash=generate_password_hash("demo123"),
            role="student",
            skills="Content, SEO, storytelling, Canva",
            track="non-technical",
            headline="Content & growth fresher",
            bio="Interested in content strategy, communication and growth experiments.",
            resume_url="https://example.com/resumes/rohan.pdf",
            portfolio_url="https://rohan.example.com",
            institution_id=org.id,
            verified_by_institution=False,
        ),
    ]

    # ---- Other roles ----
    expert = User(
        name="Dr. Ananya Rao",
        email="expert@proofstack.dev",
        password_hash=generate_password_hash("demo123"),
        role="expert",
        skills="Engineering leadership, mentoring, product systems",
        track="hybrid",
        headline="Senior Industry Mentor",
        bio="Helps early-career candidates turn vague claims into evidence-backed portfolios.",
    )
    recruiter = User(
        name="Meera Iyer",
        email="recruiter@proofstack.dev",
        password_hash=generate_password_hash("demo123"),
        role="recruiter",
        skills="Talent acquisition, early careers",
        track="hybrid",
        headline="Early Careers Recruiter",
    )
    institution = User(
        name="Mysuru Institute of Technology",
        email="institution@proofstack.dev",
        password_hash=generate_password_hash("demo123"),
        role="institution",
        skills="Student success, verification",
        track="hybrid",
        institution_id=org.id,
        headline="Institution Partner",
    )

    db.session.add_all(students + [expert, recruiter, institution])
    db.session.flush()

    # ---- Challenges ----
    challenges = [
        Challenge(
            title="Real-time fraud alert service",
            description="Build a small service that flags suspicious transactions and explain the design.",
            tags="backend, ml, fraud-detection",
            difficulty="medium",
            track="technical",
        ),
        Challenge(
            title="Realtime chat backend",
            description="Design a chat service with presence, history and a short architecture note.",
            tags="backend, websockets, realtime",
            difficulty="hard",
            track="technical",
        ),
        Challenge(
            title="Campus engagement research brief",
            description="Study a campus problem, synthesize evidence, propose an intervention.",
            tags="research, communication, operations",
            difficulty="medium",
            track="non-technical",
        ),
        Challenge(
            title="Product launch content plan",
            description="Create a launch narrative, audience map, calendar and measurement plan.",
            tags="content, marketing, storytelling",
            difficulty="medium",
            track="non-technical",
        ),
        Challenge(
            title="Calibration: FizzBuzz API",
            description="Ground-truth calibration challenge.",
            tags="calibration, backend",
            difficulty="easy",
            is_calibration=True,
            track="technical",
        ),
    ]
    db.session.add_all(challenges)
    db.session.flush()
    c1, c2, c3, c4, _cal = challenges

    # ---- Submissions ----
    subs = [
        Submission(
            student_id=students[0].id,
            challenge_id=c1.id,
            github_url="https://github.com/aarav-menon/fraud-alert",
            demo_url="https://demo.example.com/fraud",
            architecture_doc="Flask API with a queue and scoring service. Chose asynchronous scoring to keep burst traffic from blocking requests.",
            decisions="Compared rules-only and ML scoring; selected a hybrid approach and documented the false-positive trade-off.",
            explanation="Fixed a duplicate alert race by making the transaction key idempotent.",
            technical_score=84, architecture_score=82, review_score=80,
            integrity_score=97, explanation_score=85,
            build_passed=True, commit_count=42, repo_age_days=90,
        ),
        Submission(
            student_id=students[1].id,
            challenge_id=c2.id,
            github_url="https://github.com/priya-sharma/chat-ui",
            demo_url="https://demo.example.com/chat",
            architecture_doc="React client with a small realtime service and clear state boundaries.",
            decisions="Prioritized recoverable UI states and accessibility over visual complexity.",
            explanation="Tracked an intermittent message ordering issue and added sequence identifiers.",
            technical_score=78, architecture_score=76, review_score=79,
            integrity_score=100, explanation_score=88,
            build_passed=True, commit_count=31, repo_age_days=120,
        ),
        Submission(
            student_id=students[1].id,
            challenge_id=c3.id,
            demo_url="https://portfolio.example.com/campus-study",
            architecture_doc="Interview synthesis, journey map and intervention plan.",
            decisions="Used evidence from student interviews and grouped recurring friction points before proposing changes.",
            explanation="Documented what evidence was weak and what would need validation next.",
            technical_score=58, architecture_score=74, review_score=81,
            integrity_score=100, explanation_score=90,
            build_passed=True,
        ),
        Submission(
            student_id=students[2].id,
            challenge_id=c3.id,
            demo_url="https://portfolio.example.com/research-brief",
            architecture_doc="Research brief with stakeholder map, evidence table, recommendation and implementation steps.",
            decisions="Separated observed evidence from assumptions and marked open questions.",
            explanation="Explained methodology, limitations and how a future study could reduce uncertainty.",
            technical_score=62, architecture_score=82, review_score=86,
            integrity_score=100, explanation_score=94,
            build_passed=True,
        ),
        Submission(
            student_id=students[3].id,
            challenge_id=c4.id,
            demo_url="https://portfolio.example.com/content-plan",
            architecture_doc="Audience segmentation, messaging pillars, content calendar and measurement framework.",
            decisions="Chose a small test-and-learn launch instead of assuming one message would work.",
            explanation="Defined what success would mean and what evidence would trigger a content change.",
            technical_score=55, architecture_score=78, review_score=84,
            integrity_score=100, explanation_score=91,
            build_passed=True,
        ),
    ]
    db.session.add_all(subs)
    db.session.flush()
    for s in subs:
        s.recompute_proof_score()

    # ---- Reviews ----
    reviews = [
        Review(submission_id=subs[0].id, reviewer_id=expert.id,
               technical=4, architecture=4, debugging=4, explanation=4,
               comments="Strong evidence of ownership. Trade-offs are explicit. Add a load-test result so the latency claim can be verified."),
        Review(submission_id=subs[1].id, reviewer_id=expert.id,
               technical=4, architecture=4, debugging=4, explanation=5,
               comments="Good product thinking and clear explanation. Add a concise setup path and one accessibility test result."),
        Review(submission_id=subs[2].id, reviewer_id=expert.id,
               technical=3, architecture=4, debugging=4, explanation=5,
               comments="Not a coding submission and should not be judged as one. Evidence quality, reasoning and communication are the relevant signals. Add two more primary-source interviews."),
        Review(submission_id=subs[3].id, reviewer_id=expert.id,
               technical=3, architecture=4, debugging=4, explanation=5,
               comments="Strong research structure for a fresher. Next step: show how the recommendation changed after stakeholder feedback."),
        Review(submission_id=subs[4].id, reviewer_id=expert.id,
               technical=3, architecture=4, debugging=4, explanation=5,
               comments="Clear audience logic and measurable plan. Add one worked example of actual content."),
    ]
    db.session.add_all(reviews)

    # ---- Mentor thread ----
    db.session.add_all([
        MentorMessage(student_id=students[2].id, expert_id=expert.id,
                      sender_id=students[2].id,
                      message="How can I make a research portfolio stronger as a fresher?"),
        MentorMessage(student_id=students[2].id, expert_id=expert.id,
                      sender_id=expert.id,
                      message="Show your method, evidence, limitations and what changed after feedback. You do not need a technical project to prove those skills."),
    ])

    # ---- Assessment ----
    assessment = Assessment(
        created_by=recruiter.id,
        title="Early Career Reasoning — Round 1",
        description="A 45-minute evidence-based reasoning assessment.",
        duration_minutes=45,
    )
    db.session.add(assessment)
    db.session.commit()

    print("=" * 60)
    print("Seeded 4 portals — password for all: demo123")
    for u in students + [expert, recruiter, institution]:
        print(f"  {u.role:12s} {u.email}")
    print("=" * 60)


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        seed(drop_first=True)
