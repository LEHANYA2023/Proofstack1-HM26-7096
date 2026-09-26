# ProofStack — Final Pitch Deck (Team ZENITH · HM26-7096)

Slide-by-slide content, aligned to PS2's four "work out on paper" requirements
(User Types, Core Entities, Ranking Logic, Prevent Gaming). Copy into
PowerPoint/Google Slides/Canva using the official HM26-7096 template.

---

## Slide 1 — Title
**ProofStack** — *Work > Words — Evidence-First Hiring*
A verified track record of real engineering work — replacing resume claims
with build-tested, reviewed, and AI-defended proof of skill.
**TEAM ZENITH** · Team ID: HM26-7096
Aditya Jeevan Naik (Lead) · R V Lehanya · Rana Biswas · H S Amrutha

## Slide 2 — The Problem
**Hiring Runs on Claims, Not Proof.** A resume is a claim, not evidence.
Recruiters filter blind. Skilled-but-uncredentialed talent is invisible.
No way to tell real work from copied work. **73%** of technical hires fail
to match their self-reported skill level.
*Chosen sub-problem: verified proof-of-skill for technical hiring.*

## Slide 3 — Target Users
**Developer/Student** — builds and submits real projects.
**Recruiter** — screens fast, needs an explainable shortlist.
**Institution** — bulk-onboards and vouches for its own students.

## Slide 4 — Our Solution
**BuildProof: One Connected Loop** — Build → Document → Review → Rank →
Discover → Hire. Same data model across all user types, no disconnected
dashboards.

## Slide 5 — Core Entities
Seven entities, one data model: Organization, User, Challenge, Submission,
Review, Assessment, Ranking (derived). See table in `docs/architecture.md`.

## Slide 6 — Ranking Logic
```
Proof Score = Base × Difficulty × Recency × Breadth
Base = 0.35·Technical + 0.20·Architecture + 0.20·Review
     + 0.15·Integrity + 0.10·Explanation
```
Difficulty: Easy 1.0× / Medium 1.25× / Hard 1.5×. Recency: 0.5^(age/6mo).
Breadth: up to +30%. Failed builds are excluded from ranking entirely.

## Slide 7 — Preventing Gaming
Automated build check · anti-spoofing during live assessments · GitHub
mocking detection · reviewer collusion resistance · cold-start calibration.
Failed builds/flags never auto-reject — routed to human review.

## Slide 8 — Key Decision
**AI Pre-Screens. Humans Decide.** Live AI interview + mandatory
human-reviewed verdict, rejected the fully-automated pass/fail alternative
for accountability and recruiter trust.

## Slide 9 — Technical Architecture
Frontend: HTML/CSS/JS. AI: Nemotron 3.5 Lightning via OpenRouter (stub
fallback, zero API keys for demo). API: Python Flask. Data: SQLite/Postgres.
Build execution: simulated runner for MVP, gVisor/Docker in production.

## Slide 10 — Hard Constraints
Fake/plagiarized work → build check + mocking detection. Jurisdiction →
institution vouching. Priority → transparent weighted proof score. Bad
input → routed to human review, never auto-rejected. Offline → not yet
supported (see Limits & Scale).

## Slide 11 — Screenshots
Normal flow (build passes, live proof score) · Flagged input (spoofed
GitHub URL fails integrity check, routes to review) · Offline state (not
yet implemented).

## Slide 12 — Limits & Scale
Simulated build runner → move to isolated Docker/gVisor + job queue.
Reviewer bandwidth → ML-assisted calibration. Duplicate work → automated
dedup/similarity pipeline.

## Slide 13 — Roadmap
1. Pilot with one institution. 2. Real build runner. 3. Recruiter
marketplace expansion. AI disclosure: Nemotron 3.5 Lightning via
OpenRouter. Links: repo + live URL (add after deployment).

## Slide 14 — Thank You
**ProofStack** — *Work > Words* — Team ZENITH — HM26-7096 — Q&A
