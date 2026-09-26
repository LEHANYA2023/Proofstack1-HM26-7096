# The Four Hard Constraints (PS2 "Work Out on Paper")

[← Back to README](../README.md)

| # | Constraint | Status | Video |
|---|---|---|---|
| 1 | User Types | ✅ | `<mm:ss>` |
| 2 | Core Entities | ✅ | `<mm:ss>` |
| 3 | Ranking Logic | ✅ | `<mm:ss>` |
| 4 | Prevent Gaming | ✅ | `<mm:ss>` |

---

## 1. User Types

Three roles, each defined end-to-end: **Developer/Student** (builds and submits), **Recruiter** (discovers and hires), **Institution** (onboards and vouches for its own students under an authorized org account).

- **Code:** `src/models.py` (`User.role`), `src/routes/institution.py`

## 2. Core Entities

Seven entities, one data model: `Organization`, `User`, `Challenge`, `Submission`, `Review`, `Assessment`/`AssessmentAttempt`, and the derived `Ranking` (computed, not stored redundantly).

- **Code:** `src/models.py`

## 3. Ranking Logic

```
Proof Score = Base × Difficulty × Recency × Breadth

Base = 0.35·Technical + 0.20·Architecture + 0.20·Review
     + 0.15·Integrity + 0.10·Explanation
```

| Factor | Value | Why |
|---|---|---|
| Difficulty | Easy 1.0× / Medium 1.25× / Hard 1.5× | Harder work counts more |
| Recency | 0.5^(age_months / 6) | 6-month half-life; current ability matters |
| Breadth | up to +30% | Rewards range across domains |

A failed build zeroes the proof score outright — it never counts toward ranking. Every score is explainable via `GET /api/dashboard/submission/<id>/explain` ("Why this rank?").

- **Code:** `Submission.recompute_proof_score()` in `src/models.py`, `src/routes/dashboard.py`

## 4. Prevent Gaming

Five mechanisms, not just one:

| Mechanism | What it catches | Code |
|---|---|---|
| Automated build check | Work that doesn't run doesn't count | `services/anti_gaming.py::check_reproducibility` |
| GitHub-mocking detection | Repo age vs. commit history mismatches | `services/anti_gaming.py::check_github_mocking` |
| Reviewer collusion resistance | Reciprocal review patterns | `services/anti_gaming.py::check_reviewer_collusion` |
| Cold-start calibration | New users placed via a ground-truth challenge | `services/anti_gaming.py::check_cold_start` |
| Integrity event routing | Flagged tab-switches/paste events during live assessments | `routes/submissions.py::log_integrity_event` |

**Key principle:** failed builds and integrity flags never auto-reject — they route to human review. The system assumes innocence but flags everything.
