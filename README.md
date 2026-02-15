

# Assessment Ops Mini Platform

Mini backend platform to ingest assessment attempts, deduplicate noisy events, compute scores, and provide leaderboards for a Vite + React dashboard.

**Stack:** FastAPI · SQLAlchemy · SQLite · Vite + React
**Logging:** Structured JSON (Monolog-style)

---

## Setup

```bash
pip install fastapi uvicorn sqlalchemy
```

## Run

```bash
uvicorn main:app --reload
```


---

## Frontend – How to Run (React + Vite)

### Prerequisites

* Node.js v18+ installed
* npm (comes with Node)

### Steps to run frontend

```bash
cd assessment-frontend
npm install
npm run dev
```

### Open in browser

```
http://localhost:5173
```

### Notes

* Make sure the backend API is running at:

  ```
  http://localhost:8000
  ```




Then restart terminal and run:

```bash
(goto cd assessment-frontend )

npm run dev
```



API runs at:
`http://localhost:8000`

---

## Endpoints

```
GET  /                            -> Health check
POST /api/ingest/attempts         -> Bulk ingest + dedup
GET  /api/attempts                -> List attempts (filters + pagination)
POST /api/attempts/{id}/recompute -> Recompute score (single)
POST /api/attempts/recompute-all  -> Recompute scores (batch)
POST /api/attempts/{id}/flag      -> Flag attempt
GET  /api/leaderboard?test_name=  -> Leaderboard per test
GET  /api/stats                   -> Stats
```

---

## Features

* Bulk ingestion of attempts
* Student identity normalization (email/phone)
* Deduplication (same student + test + time window + answer similarity)
* Persistent score computation
* Manual + batch recompute
* Flagging suspicious attempts
* Leaderboard (best attempt per student)
* Structured JSON logging with request IDs
* CORS enabled for Vite + React frontend

---

## Scoring

Uses `test.negative_marking` config:

```json
{ "correct": 4, "wrong": -1, "skip": 0 }
```

Metrics: correct, wrong, skipped, accuracy, net_correct, score
Scores are stored in DB and used by leaderboard.

---

## Notes

* Demo scoring assumes `"A"` is the correct answer
* SQLite is used for local development
* Tables are auto-created on startup

---

