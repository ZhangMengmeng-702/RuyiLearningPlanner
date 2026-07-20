# -*- coding: utf-8 -*-
"""进度追踪 API — 打卡 + 统计"""
import json, os, sqlite3, time
from datetime import date
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "progress.db")

def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            plan_id TEXT NOT NULL,
            day INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            difficulty_rating INTEGER DEFAULT 0,
            completion_pct INTEGER DEFAULT 0,
            time_spent_hours REAL DEFAULT 0,
            feedback_text TEXT DEFAULT '',
            created_at REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_checkins_user_plan
        ON checkins(user_id, plan_id)
    """)
    conn.commit()
    return conn


class CheckinRequest(BaseModel):
    user_id: str
    plan_id: str
    day: int
    tasks_completed: list[str] = []
    difficulty_rating: int = 0
    completion_pct: int = 0
    time_spent_hours: float = 0
    feedback_text: str = ""


@router.post("/checkin")
async def checkin(req: CheckinRequest):
    conn = _get_db()
    conn.execute(
        "INSERT INTO checkins (user_id, plan_id, day, checkin_date, difficulty_rating, completion_pct, time_spent_hours, feedback_text, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (req.user_id, req.plan_id, req.day, date.today().isoformat(),
         req.difficulty_rating, req.completion_pct, req.time_spent_hours,
         req.feedback_text, time.time())
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "day": req.day, "checkin_date": date.today().isoformat()}


@router.get("/stats/{user_id}")
async def get_stats(user_id: str, plan_id: str = ""):
    conn = _get_db()
    if plan_id:
        rows = conn.execute(
            "SELECT * FROM checkins WHERE user_id=? AND plan_id=? ORDER BY day", (user_id, plan_id)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM checkins WHERE user_id=? ORDER BY day", (user_id,)
        ).fetchall()
    conn.close()

    total_days = len(rows)
    completed_days = sum(1 for r in rows if r[6] >= 80)  # completion_pct >= 80
    avg_completion = sum(r[6] for r in rows) / total_days if total_days else 0
    avg_difficulty = sum(r[5] for r in rows) / total_days if total_days else 0
    total_hours = sum(r[7] for r in rows)

    # 连续打卡天数
    streak = 0
    checkin_dates = sorted(set(r[4] for r in rows), reverse=True)
    from datetime import datetime, timedelta
    for i, d in enumerate(checkin_dates):
        expected = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        if d == expected:
            streak += 1
        else:
            break

    return {
        "user_id": user_id,
        "total_days": total_days,
        "completed_days": completed_days,
        "streak": streak,
        "avg_completion_pct": round(avg_completion, 1),
        "avg_difficulty": round(avg_difficulty, 1),
        "total_hours": round(total_hours, 1),
        "checkins": [
            {"day": r[3], "date": r[4], "difficulty": r[5], "completion": r[6],
             "hours": r[7], "feedback": r[8]}
            for r in rows
        ],
    }