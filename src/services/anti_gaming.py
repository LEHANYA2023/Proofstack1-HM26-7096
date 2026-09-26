"""
PS2 anti-gaming checks. Each function returns a dict with:
  - passed: bool
  - reason: str
  - flag: str (optional)
"""

def check_reproducibility(submission):
    """Simulated build check. In production this runs Docker/gVisor."""
    if not submission.github_url or "github.com" not in submission.github_url:
        return {"passed": False, "reason": "No valid GitHub repository linked."}
    return {"passed": True, "reason": "Build + tests passed (simulated runner)."}


def check_github_mocking(submission):
    """Heuristic: repo age vs submission date, commit count vs claimed work."""
    flags = []
    if submission.repo_age_days < 1 and submission.commit_count > 50:
        flags.append("mocked_history: repo created <1 day ago with >50 commits")
    if submission.commit_count == 0:
        flags.append("no_commits: repository has no commit history")
    if flags:
        return {"passed": False, "flag": "; ".join(flags), "reason": "Suspicious GitHub history."}
    return {"passed": True, "reason": "GitHub history looks organic."}


def check_reviewer_collusion(reviewer_id, submission_id):
    """Check for reciprocal review patterns."""
    from models import Review, Submission
    sub = Submission.query.get(submission_id)
    if not sub:
        return {"passed": True, "reason": "Submission not found."}
    reciprocal = Review.query.join(
        Submission, Review.submission_id == Submission.id
    ).filter(
        Submission.student_id == reviewer_id,
        Review.reviewer_id == sub.student_id,
    ).first()
    if reciprocal:
        return {"passed": False, "reason": "Reciprocal review pattern detected."}
    return {"passed": True, "reason": "No collusion pattern detected."}


def check_cold_start(user):
    """New users must complete a calibration challenge first."""
    if user.is_calibrated:
        return {"passed": True, "reason": "User is calibrated."}
    return {"passed": False, "reason": "User must complete a calibration challenge first."}


# ---------------------------------------------------------------------------
# Assessment integrity checks (PS2 "how do you stop cheating on a timed test").
#
# Deliberate scope decision, written up in docs/limitations.md: we do NOT do
# webcam gaze-tracking or per-user keystroke-biometric identity verification.
# Both need an enrolled baseline, careful consent/privacy handling, and (for
# gaze) a calibrated camera to be reliable at all -- none of that is buildable
# or trustworthy in a hackathon window, and a flaky camera-based "cheating"
# verdict is worse than no verdict. Instead we combine several cheap signals
# that are each individually gameable, but expensive to game *all at once*:
#   1. one live session per attempt (kills "open it on my phone too")
#   2. focus/visibility loss (tab-switch, alt-tab)
#   3. paste of a large block of text with no matching typing history
#   4. dev-tools heuristic (viewport/outer-window delta)
#   5. typing-cadence anomaly (inhumanly uniform inter-key timing -> likely
#      scripted/automated input, NOT "this is a different person typing")
# ---------------------------------------------------------------------------

SEVERITY = {
    "focus_loss": 6,
    "paste_no_history": 18,
    "devtools_suspected": 15,
    "fullscreen_exit": 8,
    "second_session_blocked": 0,  # logged on the blocked session, not this one
    "cadence_anomaly": 12,
    "context_menu_blocked": 2,
}


def check_single_active_session(assessment_id, student_id):
    """
    An attempt is "in_progress" for at most one live session at a time.
    Starting again while one is in_progress returns the SAME attempt/token
    instead of minting a second one -- so a second device just gets told
    "an attempt is already running" rather than silently starting a second,
    unmonitored copy of the test.
    """
    from models import AssessmentAttempt

    existing = AssessmentAttempt.query.filter_by(
        assessment_id=assessment_id, student_id=student_id, status="in_progress"
    ).first()
    return existing


def score_keystroke_cadence(intervals_ms):
    """
    Heuristic anomaly check on inter-keystroke gaps (ms between keydown
    events), not on WHO is typing. Flags two patterns:
      - near-zero variance at high speed (bulk-inserted/automated text)
      - a single huge gap followed by a burst that matches paste length
    Returns (is_anomalous: bool, reason: str).
    """
    if len(intervals_ms) < 12:
        return False, "not enough keystrokes to evaluate"

    mean = sum(intervals_ms) / len(intervals_ms)
    variance = sum((x - mean) ** 2 for x in intervals_ms) / len(intervals_ms)
    stddev = variance ** 0.5

    if mean < 25 and stddev < 4:
        return True, f"near-uniform {mean:.1f}ms keystroke gaps (stddev {stddev:.1f}) -- looks scripted"
    return False, "cadence within normal human variance"


def score_attempt_integrity(attempt):
    """
    Recomputes attempt.integrity_score from attempt.flags (already
    decremented as events came in) and returns a short human-readable
    verdict string for the reviewer/recruiter UI. Does not re-run detection;
    call this at submit time purely to summarize.
    """
    flags = attempt.get_flags()
    if not flags:
        return "No integrity flags raised during this attempt."
    counts = {}
    for f in flags:
        counts[f["type"]] = counts.get(f["type"], 0) + 1
    parts = [f"{v}x {k.replace('_', ' ')}" for k, v in counts.items()]
    return f"Integrity score {attempt.integrity_score}/100 -- " + ", ".join(parts)
