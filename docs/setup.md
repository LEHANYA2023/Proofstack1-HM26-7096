# Setup & Run Instructions

[← Back to README](../README.md)

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.10+ |

## 1. Clone

```bash
git clone <repo-url>
cd proofstack/src
```

## 2. Environment Variables

```bash
cp .env.example .env
```

| Variable | Required | Example | Purpose |
|---|---|---|---|
| `SECRET_KEY` | No (has a dev default) | `change-me` | Flask session secret |
| `JWT_SECRET_KEY` | No (has a dev default) | `change-me` | Signs auth tokens |
| `DATABASE_URL` | No (defaults to SQLite) | `postgresql://user:pass@host/db` | Swap DB for production |
| `OPENROUTER_API_KEY` | No | `sk-or-...` | Enables live Nemotron 3.5 Lightning calls; omit to run the AI analyzer in its deterministic stub mode |

> Never commit real secrets. Commit only `.env.example`.

## 3. Install & Seed Demo Data

```bash
pip install -r requirements.txt --break-system-packages
python seed.py          # loads 5 demo users, 3 challenges, 2 submissions
```

## 4. Run

```bash
python app.py
```

Open `http://127.0.0.1:5000`. Demo accounts:

| Role | Email | Password |
|---|---|---|
| Student | student@proofstack.dev | demo123 |
| Student 2 | priya@proofstack.dev | demo123 |
| Expert | expert@proofstack.dev | demo123 |
| Recruiter | recruiter@proofstack.dev | demo123 |
| Institution | institution@proofstack.dev | demo123 |

## Testing the Live AI Interview

1. Log in as a student and note a submission ID from the "My Submissions" tab.
2. Open `http://127.0.0.1:5000/interview`, paste the submission ID, click **Start interview**.
3. Answer the AI's questions — no verdict is ever issued by the AI; the transcript is what a human expert reviews.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` on `flask_sqlalchemy` etc. | Run `pip install -r requirements.txt --break-system-packages` (or use a venv) |
| Port already in use | `python app.py` on a different port: edit the `app.run()` call in `app.py`, or set `FLASK_RUN_PORT` |
| Empty candidate search results | Run `python seed.py` again — it drops and recreates all tables |
