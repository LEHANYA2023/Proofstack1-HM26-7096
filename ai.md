# AI Usage Disclosure

[← Back to README](./README.md)

> AI tools are 100% permitted at HackMysuru 1.0. Disclosing them is mandatory.

---

## Summary

| Question | Answer |
|---|---|
| Did we use AI tools during development? | Yes |
| Does our product use AI/ML at runtime? | Yes |
| Roughly how much of the code was AI-assisted? | ~80% of the Flask backend and frontend scaffolding, 100% of the anti-gaming logic reviewed and adjusted by the team |
| Can every team member explain the AI-assisted code? | Yes |

---

## 1. AI Tools Used During Development

| Tool | Model / plan | Used by | What we used it for |
|---|---|---|---|
| Claude | Claude (Anthropic), web app | Team ZENITH | Backend scaffolding (Flask routes, SQLAlchemy models), proof-score formula implementation, frontend HTML/CSS/JS, repo structure and docs |

## 2. Where AI Helped in the Codebase

| Area / file | Level of AI help | What a human did |
|---|---|---|
| `src/models.py`, `src/routes/` | High: scaffolded by Claude | Team defined the entity relationships, the proof-score weights, and the anti-gaming thresholds |
| `src/services/anti_gaming.py` | Medium | Team decided which signals to check (repo age, commit count, reciprocal reviews) and the penalty values |
| `src/static/`, `src/templates/` | High: scaffolded by Claude | Team decided the tab-based UX flow per role and the HackMysuru gold/dark theme |
| `src/services/anti_gaming.py` (assessment integrity: session lock, focus/paste/devtools/cadence checks), `src/static/js/proctor.js`, `src/routes/assessments.py` | High: scaffolded by Claude | Team chose the explicit no-gaze-tracking / no-keystroke-identity-biometrics scope decision (see `docs/limitations.md`) and the severity weights per flag type |
| README / docs | Medium | Team filled in problem framing, target users, and decision log content |

**Commit convention:** commits containing substantial AI-generated code are tagged `[ai]` in the message, e.g. `feat: proof score engine [ai]`.

## 3. AI Inside the Product (runtime)

| Model / API | What it does in our product | Hosted where | Trained / fine-tuned by us? |
|---|---|---|---|
| NVIDIA Nemotron 3.5 Lightning | Powers the live AI interview (asks candidates about their own submission) and the candidate analyzer (role-fit, strengths, risk flags) | OpenRouter (provider API) | No, prompt-only |

- **Accuracy we measured:** not formally measured yet — MVP stage.
- **What happens when the model is wrong / unavailable?** The candidate analyzer falls back to a deterministic keyword-based stub (`services/candidate_analyzer.py::_stub_analysis`) with zero API calls, so the whole demo runs with no API key configured. The AI interview never issues a pass/fail verdict either way — a human expert always makes the final call.
- **Does it work offline?** No — requires connectivity when a live API key is set; the stub mode works without any network call.
- **Candidate data sent to third parties:** submission text (architecture doc, decisions, explanation) is sent to OpenRouter only when `OPENROUTER_API_KEY` is configured.
- **Cost at city scale:** unknown — not yet load-tested.

## 4. Key Prompts (max 5)

| # | Prompt (short) | What we kept | What we changed or rejected |
|---|---|---|---|
| 1 | "Design a proof score formula from difficulty, recency, breadth" | The multiplier structure (Base × Difficulty × Recency × Breadth) | Adjusted the recency half-life and difficulty multipliers to match team judgment |
| 2 | "Build anti-gaming checks for build verification, GitHub mocking, and reviewer collusion" | The three-check structure | Tuned the mocking heuristic thresholds (commit count, repo age) |

## 5. How We Verified AI Output

- Every AI-generated route was read line-by-line by the team before committing.
- Rejected an early version that auto-rejected failed builds — changed to "route to human review" per PS2's anti-gaming principle.
- Verified the proof-score formula against hand-calculated examples in `seed.py`.

## 6. What We Deliberately Did *Not* Use AI For

- The final proof-score weights and multiplier values — decided by the team.
- The decision to keep humans in the loop for every AI verdict — a team design choice, not an AI suggestion.

---

**Declaration:** We confirm this disclosure is complete, and every team member can explain the code listed above.
**Signed:** Aditya Jeevan Naik on behalf of Team ZENITH · HM26-7096
