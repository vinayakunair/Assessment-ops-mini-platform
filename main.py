from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from db import SessionLocal, Base, engine
from models import Attempt, AttemptScore
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import logging, json, uuid, time, re



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

def log_event(channel: str, level: str, message: str, context=None, extra=None):
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
        "channel": channel,
        "context": context or {},
        "extra": extra or {}
    }
    logger.info(json.dumps(payload))



def parse_dt(s: str | None):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        logger.warning(f"Invalid datetime format received: {s}")
        return None

def normalize_email(email: str | None):
    if not email:
        return None
    email = email.lower().strip()
    if email.endswith("@gmail.com"):
        local, domain = email.split("@")
        local = local.split("+")[0].replace(".", "")
        return f"{local}@{domain}"
    return email

def normalize_phone(phone: str | None):
    if not phone:
        return None
    return re.sub(r"\D", "", phone)

def answer_similarity(a1: dict, a2: dict):
    keys = set(a1.keys()) & set(a2.keys())
    if not keys:
        return 0
    same = sum(1 for k in keys if a1[k] == a2[k])
    return same / len(keys)

def is_duplicate(db, new_attempt: Attempt, threshold=0.92):
    if not new_attempt.started_at:
        return None, None

    candidates = db.query(Attempt).filter(
        Attempt.status != "DEDUPED",
        Attempt.started_at >= new_attempt.started_at - timedelta(minutes=7),
        Attempt.started_at <= new_attempt.started_at + timedelta(minutes=7),
    ).all()

    for old in candidates:
        if new_attempt.source_event_id == old.source_event_id:
            continue

        s1 = new_attempt.student.get("email_normalized") or new_attempt.student.get("phone_normalized")
        s2 = old.student.get("email_normalized") or old.student.get("phone_normalized")

        if not s1 or not s2 or s1 != s2:
            continue

        if new_attempt.test.get("name") != old.test.get("name"):
            continue

        sim = answer_similarity(new_attempt.answers or {}, old.answers or {})
        if sim >= threshold:
            return old, sim

    return None, None

def compute_score(test: dict, answers: dict):
    config = test.get("negative_marking", {"correct": 4, "wrong": -1, "skip": 0})
    correct = wrong = skipped = 0

    for _, ans in (answers or {}).items():
        if ans == "SKIP":
            skipped += 1
        elif ans == "A":  
            correct += 1
        else:
            wrong += 1

    accuracy = (correct / (correct + wrong) * 100) if (correct + wrong) > 0 else 0
    net_correct = correct - wrong
    score = correct * config["correct"] + wrong * config["wrong"] + skipped * config["skip"]

    return {
        "correct": correct,
        "wrong": wrong,
        "skipped": skipped,
        "accuracy": accuracy,
        "net_correct": net_correct,
        "score": score,
        "explanation": {
            "config": config,
            "counts": {"correct": correct, "wrong": wrong, "skipped": skipped}
        }
    }



@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.time()

    log_event("http", "INFO", "request_started", {"request_id": request_id, "path": request.url.path})

    response = await call_next(request)
    duration = int((time.time() - start) * 1000)

    log_event("http", "INFO", "request_completed", {"request_id": request_id}, {"latency_ms": duration})
    return response



@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/api/ingest/attempts")
def ingest_attempts(payload: List[Dict[str, Any]]):
    log_event("http", "INFO", "ingest_started", {"count": len(payload)})

    db = SessionLocal()
    saved, skipped = 0, 0

    for item in payload:
        student = item.get("student") or {}
        student["email_normalized"] = normalize_email(student.get("email"))
        student["phone_normalized"] = normalize_phone(student.get("phone"))

        attempt = Attempt(
            source_event_id=item.get("source_event_id"),
            student=student,
            test=item.get("test"),
            answers=item.get("answers"),
            raw_payload=item,
            channel=item.get("channel"),
            status="INGESTED",
            started_at=parse_dt(item.get("started_at")),
            submitted_at=parse_dt(item.get("submitted_at")),
        )

        try:
            dup, sim = is_duplicate(db, attempt)
            if dup:
                attempt.status = "DEDUPED"
                attempt.duplicate_of_attempt_id = dup.id

            db.add(attempt)
            db.commit()
            saved += 1
        except IntegrityError:
            db.rollback()
            skipped += 1
        except Exception as e:
            db.rollback()
            log_event("db", "ERROR", "db_error", extra={"error": str(e)})

    db.close()
    return {"saved": saved, "skipped": skipped}


@app.get("/api/attempts")
def list_attempts(limit: int = 50):
    db = SessionLocal()
    rows = db.query(Attempt).order_by(Attempt.started_at.desc()).limit(limit).all()
    db.close()

    return [
        {
            "id": a.id,
            "source_event_id": a.source_event_id,
            "status": a.status,
            "duplicate_of_attempt_id": a.duplicate_of_attempt_id
        }
        for a in rows
    ]

@app.get("/api/attempts")
def list_attempts(limit: int = 50):
    db = SessionLocal()
    rows = db.query(Attempt).order_by(Attempt.started_at.desc()).limit(limit).all()
    db.close()

    return [
        {
            "id": a.id,
            "source_event_id": a.source_event_id,
            "status": a.status,
            "duplicate_of_attempt_id": a.duplicate_of_attempt_id
        }
        for a in rows
    ]







@app.post("/api/attempts/recompute-all")
def recompute_all():
    db = SessionLocal()
    attempts = db.query(Attempt).filter(Attempt.status.in_(["INGESTED", "DEDUPED"])).all()
    count = 0

    for attempt in attempts:
        result = compute_score(attempt.test, attempt.answers)

        score_row = db.query(AttemptScore).filter(AttemptScore.attempt_id == attempt.id).first()
        if score_row:
            score_row.correct = result["correct"]
            score_row.wrong = result["wrong"]
            score_row.skipped = result["skipped"]
            score_row.accuracy = result["accuracy"]
            score_row.net_correct = result["net_correct"]
            score_row.score = result["score"]
            score_row.explanation = result["explanation"]
        else:
            db.add(AttemptScore(attempt_id=attempt.id, **result))

        attempt.status = "SCORED"
        count += 1

    db.commit()
    db.close()
    return {"scored": count}

@app.get("/api/leaderboard")
def leaderboard(test_name: str):
    db = SessionLocal()

    rows = (
        db.query(Attempt, AttemptScore)
        .join(AttemptScore, AttemptScore.attempt_id == Attempt.id)
        .filter(
            Attempt.status == "SCORED",
            Attempt.duplicate_of_attempt_id == None 
        )
        .all()
    )

    best_by_student = {}

    for attempt, score in rows:
        if not attempt.test:
            continue

        if test_name.lower() not in attempt.test.get("name", "").lower():
            continue 


        key = attempt.student.get("email_normalized") or attempt.student.get("phone_normalized")
        if not key:
            continue

        prev = best_by_student.get(key)
        if not prev or score.score > prev["score"]:
            best_by_student[key] = {
                "student": attempt.student,
                "score": score.score,
                "accuracy": score.accuracy,
                "net_correct": score.net_correct,
                "submitted_at": attempt.submitted_at,
            }

    ranked = sorted(
        best_by_student.values(),
        key=lambda x: (
            -x["score"],
            -x["accuracy"],
            -x["net_correct"],
            x["submitted_at"] or datetime.max
        )
    )

    db.close()
    return ranked


