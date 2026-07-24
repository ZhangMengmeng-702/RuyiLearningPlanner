# -*- coding: utf-8 -*-
"""进度追踪 API — 打卡 + 统计 + 自适应调整"""
import json, os, sqlite3, time
from datetime import date
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.utils.path_security import safe_plan_id, safe_user_id, PathSecurityError
from api.deps import get_current_user_id

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "progress.db")
PLANS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "plans"))


def _get_latest_plan_id(user_id: str) -> str:
    """获取用户最新的计划ID"""
    if not os.path.exists(PLANS_DIR):
        return ""
    plan_files = [f for f in os.listdir(PLANS_DIR) if f.endswith(".json") and f.startswith("plan_")]
    if not plan_files:
        return ""
    plan_files.sort(reverse=True)
    for plan_file in plan_files:
        plan_path = os.path.join(PLANS_DIR, plan_file)
        try:
            with open(plan_path, encoding="utf-8") as f:
                plan = json.load(f)
            if not user_id or plan.get("user_id") == user_id:
                return plan.get("plan_id", "")
        except Exception:
            continue
    return ""


def _plan_belongs_to_user(plan_id: str, user_id: str) -> bool:
    """检查计划是否属于指定用户"""
    try:
        safe_id = safe_plan_id(plan_id)
    except PathSecurityError:
        return False
    plan_path = os.path.join(PLANS_DIR, f"{safe_id}.json")
    if not os.path.exists(plan_path):
        return False
    try:
        with open(plan_path, encoding="utf-8") as f:
            plan = json.load(f)
        return plan.get("user_id") == user_id
    except Exception:
        return False

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
            tasks_completed TEXT DEFAULT '[]',
            created_at REAL NOT NULL
        )
    """)
    try:
        conn.execute("ALTER TABLE checkins ADD COLUMN tasks_completed TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass
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


def _should_auto_adjust(completion_pct: int, difficulty_rating: int, unfinished_count: int) -> bool:
    """判断是否需要自动调整计划"""
    # 有未完成任务需要顺延
    if unfinished_count > 0:
        return True
    # 完成率过低需要调整任务量
    if completion_pct < 70:
        return True
    # 难度反馈过高或过低
    if difficulty_rating >= 4 or difficulty_rating <= 1:
        return True
    return False


@router.post("/checkin")
async def checkin(req: CheckinRequest, current_user_id: str = Depends(get_current_user_id)):
    # 权限校验：只能给自己打卡
    try:
        req_user_id = safe_user_id(req.user_id)
    except PathSecurityError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={"error": f"无效的用户ID: {e}"}
        )
    
    if req_user_id != current_user_id:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=403,
            content={"error": "无权为其他用户打卡"}
        )
    
    actual_plan_id = req.plan_id
    if actual_plan_id == "latest":
        actual_plan_id = _get_latest_plan_id(current_user_id) or "latest"
    else:
        try:
            actual_plan_id = safe_plan_id(actual_plan_id)
        except PathSecurityError as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={"error": f"无效的计划ID: {e}"}
            )
        # 权限校验：plan_id 必须属于当前用户
        if actual_plan_id != "latest" and not _plan_belongs_to_user(actual_plan_id, current_user_id):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={"error": "无权操作其他用户的计划"}
            )
    
    today_str = date.today().isoformat()
    conn = _get_db()
    
    existing = conn.execute(
        "SELECT id FROM checkins WHERE user_id=? AND plan_id=? AND checkin_date=?",
        (req.user_id, actual_plan_id, today_str)
    ).fetchone()
    
    if existing:
        conn.close()
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={"error": "今天已经打过卡了，明天再来吧！", "checkin_date": today_str}
        )
    
    conn.execute(
        "INSERT INTO checkins (user_id, plan_id, day, checkin_date, difficulty_rating, completion_pct, time_spent_hours, feedback_text, tasks_completed, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (req.user_id, actual_plan_id, req.day, today_str,
         req.difficulty_rating, req.completion_pct, req.time_spent_hours,
         req.feedback_text, json.dumps(req.tasks_completed), time.time())
    )
    conn.commit()
    conn.close()

    # 自动调整计划
    adjusted = False
    adjust_reason = ""
    unfinished_count = 0

    # 加载当天任务数，计算未完成数量
    try:
        if actual_plan_id != "latest":
            plan_path = os.path.join(PLANS_DIR, f"{actual_plan_id}.json")
            if os.path.exists(plan_path):
                with open(plan_path, encoding="utf-8") as f:
                    plan_data = json.load(f)
                today_tasks = [t for t in plan_data.get("daily_tasks", []) if t.get("day") == req.day]
                unfinished_count = len(today_tasks) - len(req.tasks_completed)
    except Exception:
        pass

    if _should_auto_adjust(req.completion_pct, req.difficulty_rating, unfinished_count):
        try:
            from src.learner.plan_adjuster import auto_adjust_plan_after_checkin
            checkin_data = {
                "user_id": req.user_id,
                "plan_id": actual_plan_id,
                "day": req.day,
                "tasks_completed": req.tasks_completed,
                "difficulty_rating": req.difficulty_rating,
                "completion_pct": req.completion_pct,
                "time_spent_hours": req.time_spent_hours,
                "feedback_text": req.feedback_text,
            }
            adjusted_plan = auto_adjust_plan_after_checkin(actual_plan_id, checkin_data)
            if adjusted_plan:
                adjusted = True
                adjust_reason = adjusted_plan.get("adjust_reason", "")
        except Exception as e:
            # 自动调整失败不影响打卡结果
            import logging
            logging.getLogger(__name__).warning(f"自动调整计划失败: {e}")

    result = {
        "status": "ok",
        "day": req.day,
        "checkin_date": today_str,
        "adjusted": adjusted,
        "adjust_reason": adjust_reason,
        "unfinished_count": unfinished_count,
    }
    return result


@router.get("/checkin/today/{user_id}")
async def get_today_checkin(user_id: str, plan_id: str = "", current_user_id: str = Depends(get_current_user_id)):
    try:
        uid = safe_user_id(user_id)
    except PathSecurityError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={"error": f"无效的用户ID: {e}"}
        )
    
    # 权限校验：只能查看自己的
    if uid != current_user_id:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=403,
            content={"error": "无权查看其他用户的数据"}
        )
    
    actual_plan_id = plan_id
    if plan_id == "latest":
        actual_plan_id = _get_latest_plan_id(uid)
    elif plan_id:
        try:
            actual_plan_id = safe_plan_id(plan_id)
        except PathSecurityError as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={"error": f"无效的计划ID: {e}"}
            )
    
    today_str = date.today().isoformat()
    conn = _get_db()
    
    try:
        if actual_plan_id:
            row = conn.execute(
                "SELECT * FROM checkins WHERE user_id=? AND plan_id=? AND checkin_date=? ORDER BY created_at DESC LIMIT 1",
                (uid, actual_plan_id, today_str)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM checkins WHERE user_id=? AND checkin_date=? ORDER BY created_at DESC LIMIT 1",
                (uid, today_str)
            ).fetchone()
    except Exception as e:
        conn.close()
        return {"checked_in": False, "date": today_str, "error": str(e)}
    
    conn.close()
    
    if not row:
        return {"checked_in": False, "date": today_str}
    
    return {
        "checked_in": True,
        "date": row[4],
        "day": row[3],
        "difficulty": row[5],
        "completion": row[6],
        "hours": row[7],
        "feedback": row[8],
        "tasks_completed": json.loads(row[9]) if row[9] else [],
    }


@router.get("/stats/{user_id}")
async def get_stats(user_id: str, plan_id: str = "", current_user_id: str = Depends(get_current_user_id)):
    try:
        uid = safe_user_id(user_id)
    except PathSecurityError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={"error": f"无效的用户ID: {e}"}
        )
    
    # 权限校验：只能查看自己的
    if uid != current_user_id:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=403,
            content={"error": "无权查看其他用户的数据"}
        )
    
    actual_plan_id = plan_id
    if plan_id == "latest":
        actual_plan_id = _get_latest_plan_id(uid)
    elif plan_id:
        try:
            actual_plan_id = safe_plan_id(plan_id)
        except PathSecurityError as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={"error": f"无效的计划ID: {e}"}
            )
    
    conn = _get_db()
    if actual_plan_id:
        rows = conn.execute(
            "SELECT * FROM checkins WHERE user_id=? AND plan_id=? ORDER BY day", (uid, actual_plan_id)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM checkins WHERE user_id=? ORDER BY day", (uid,)
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
        "user_id": uid,
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