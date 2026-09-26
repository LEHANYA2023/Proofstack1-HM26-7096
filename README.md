# ProofStack — ZENITH / HM26

ProofStack is an early-career hiring and evidence platform designed around one idea: **freshers should be discoverable for what they can actually prove, not only for how technical their resume looks.**

## What changed in this rebuild

- Four completely separate stakeholder portals:
  - `/student` — profile/evidence, transparent reviews, private mentor chat, AI career coach
  - `/expert` — evidence review queue, honest rubric feedback, private mentor inbox
  - `/recruiter` — candidate evidence room with resume, GitHub, portfolio/projects and trust signals
  - `/institution` — student verification and campus evidence readiness
- Separate role-specific login pages: `/login/student`, `/login/expert`, `/login/recruiter`, `/login/institution`
- Technical, hybrid and non-technical fresher tracks
- Non-technical evidence examples: research briefs, communication, operations, content, case studies and presentations
- Candidate profile fields for resume, GitHub profile, portfolio/projects, headline, bio and availability
- Recruiter discovery includes students who have **zero projects**, so lack of technical proof does not silently remove a fresher from discovery
- Recruiters can **directly invite** a candidate to a named opportunity straight from the candidate room; the student sees it in a new `Opportunities` tab and accepts/declines — closes the "discover → hire" step of the connected loop
- Data visualizations on the Student `Ranking` tab (proof-score breakdown, leaderboard, ranking-formula weights) and the Recruiter `Talent map` tab (track mix, proof-score bands, top skills), via Chart.js
- Transparent reviews with reviewer identity, rubric scores and comments
- Private student ↔ senior expert mentorship threads
- Role-aware AI career chatbot with offline fallback; OpenRouter/Nemotron can be enabled through `OPENROUTER_API_KEY`
- AI candidate analysis remains an assistive signal rather than a hiring verdict

## Demo accounts

All demo passwords are `demo123`.

| Portal | Email |
|---|---|
| Student | `student@proofstack.dev` |
| Expert | `expert@proofstack.dev` |
| Recruiter | `recruiter@proofstack.dev` |
| Institution | `institution@proofstack.dev` |

Additional student demos: `priya@proofstack.dev`, `nandini@proofstack.dev`, `rohan@proofstack.dev`.

## Run locally

```bash
cd proofstack/src
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

Open `http://127.0.0.1:5000/`.

## AI configuration

The app works without an AI key using deterministic local guidance/analysis. To enable the live model path, copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`.

## Product principle

Scores are not presented as an automatic hiring verdict. Recruiters can inspect evidence, context, human reviews, institution verification and AI notes and make their own decision.
