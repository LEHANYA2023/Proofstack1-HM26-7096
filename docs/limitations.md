# Known Limitations & Future Scope

[← Back to README](../README.md)

## What Doesn't Work Yet

| Limitation | Why it exists | What we'd do next |
|---|---|---|
| No offline submission mode | Out of scope for a 3-day build; platform assumes connectivity end-to-end | Add an offline-first client queue that syncs on reconnect |
| Simulated build runner | Real isolated execution (Docker/gVisor) needs infra we didn't have time to stand up | Move to isolated Docker/gVisor execution behind a job queue |
| GitHub-mocking detection is heuristic only | Repo age vs. commit count is a proxy signal, not a forensic audit | Add commit-timestamp-distribution and diff-size analysis |
| No webcam gaze-tracking or per-user keystroke-identity biometrics in assessments | Deliberately out of scope, not just unbuilt — see below | See "Why we didn't build gaze/biometric proctoring" |

## Assessment integrity: what we built, and what we deliberately didn't

A recruiter/institution "sends a test" and a student takes it in the browser (`src/static/js/proctor.js` + `services/anti_gaming.py`). Instead of one camera-based "cheating score," we combine several cheap, disclosed signals that are individually gameable but expensive to fake all at once:

1. **One live session per attempt** — the server (not the browser) refuses to start a second attempt while one is `in_progress` for the same assessment+student, so opening the test on a second device doesn't spawn an unmonitored second copy.
2. **Focus/visibility loss** — tab switch or alt-tab is logged.
3. **Paste with no matching typing history** — a large pasted block with little prior local typing on that answer is logged (not blocked — a false positive shouldn't fail someone outright).
4. **Dev-tools heuristic** — outer/inner window size delta above a generous threshold.
5. **Fullscreen exit**, if fullscreen was requested.
6. **Keystroke-cadence anomaly** — inter-keystroke timing that's inhumanly uniform (script/automation-shaped), computed server-side from intervals only, never from keystroke content.

Every flag lands as a soft signal with a severity weight on `AssessmentAttempt.integrity_score` (starts at 100) — a human reviewer sees the full trail and decides, exactly like the human-in-the-loop principle used for submission reviews. Nothing here auto-fails a candidate.

### Why we didn't build gaze-tracking or keystroke-identity biometrics

A reviewer may reasonably ask "what about someone using a second device off-camera?" We considered webcam gaze tracking and per-user keystroke-identity verification and chose not to build either, for reasons worth stating explicitly rather than quietly shipping something unreliable:

- **Gaze tracking** needs a calibrated camera and a per-user baseline to mean anything; without it, "looked away" is mostly noise (screen glare, second monitor, note-taking, a disability). A flaky camera-based cheating verdict is worse than no verdict, and it's not something we could validate in a hackathon window.
- **Keystroke-identity biometrics** ("prove this is still the same person typing") needs an enrolled typing profile collected with informed consent over multiple prior sessions — we have neither the enrollment flow nor the time to validate a false-positive rate we'd be comfortable putting in front of a candidate.
- Both raise real privacy/consent questions (always-on camera, biometric data retention) that deserve more care than a 3-day build can give them.
- The signals we did build catch the same practical problem — "the answer isn't really theirs" — via session control, paste/focus/timing patterns, without needing a camera or an identity baseline at all.

If this were pursued post-hackathon, the honest next step is *disclosed, opt-in* browser-only liveness checks (e.g. periodic click-to-continue prompts) before anything camera-based, plus a proper consent and data-retention story.

## Edge Cases We Don't Handle

- A student forking a real repo just before the deadline to fake commit history depth.
- Two reviewers colluding through a side channel outside the platform (only in-platform reciprocal reviews are detected).
- A second physical monitor / second person reading questions aloud off-screen — no proctoring signal here catches purely physical-world collaboration.
- A determined candidate typing at deliberately irregular (human-like) intervals to defeat the cadence check — it's a soft signal for a reviewer, not a hard gate.

## Scaling to All of Mysuru

| What breaks first | Rough numbers | Fix |
|---|---|---|
| Simulated build runner | Any real concurrent load | Isolated Docker/gVisor execution + job queue |
| Reviewer bandwidth | Doesn't scale linearly with submission volume | ML-assisted reviewer calibration and weighting |
| Duplicate/near-duplicate work | Manual GitHub heuristics get harder to police at scale | Automated dedup + similarity pipeline across all submissions |

## Roadmap

1. Pilot with one institution — onboard one college's cohort end-to-end to stress-test the vouching flow.
2. Real build runner — replace the simulated flag with isolated Docker/gVisor execution.
3. Recruiter marketplace expansion — open verified-talent search to more hiring partners beyond the pilot.
