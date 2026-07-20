# -*- coding: utf-8 -*-
"""学习对话 SSE 端点 — 接收前端消息，调 Hermes Agent，流式返回"""
import asyncio, json, logging, os, subprocess, time
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str = ""

@router.post("/chat")
async def chat_stream(req: ChatRequest):
    """SSE 流式聊天：前端发消息 → 后端调 Hermes CLI → 流式返回"""

    async def event_stream():
        # 1. 构造发送给 Hermes Agent 的请求 JSON
        payload = json.dumps({
            "action": "learning_plan",
            "user_id": req.user_id,
            "message": req.message,
            "session_id": req.session_id or f"session_{req.user_id}_{int(time.time())}",
        })

        # 2. 通过 subprocess 调 Hermes CLI
        # 注意：如果 Hermes CLI 不可用，此段会自动降级为 mock 模式
        try:
            proc = subprocess.Popen(
                ["hermes", "chat", "-s", "learning-planner", "-q", payload],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8",
            )
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                yield f"data: {line}\n\n"
            proc.wait(timeout=60)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            # 降级：Mock 模式（Hermes CLI 不存在时用）
            logger.warning(f"Hermes CLI 不可用，降级为 mock: {e}")
            mock_lines = [
                '{"event": "token", "data": "正在分析你的学习目标..."}',
                '{"event": "token", "data": "已检索到相关知识库内容。"}',
                json.dumps({
                    "event": "plan",
                    "data": {
                        "plan_id": f"plan_{req.user_id}_{int(time.time())}",
                        "goal": "学习Python数据分析",
                        "total_weeks": 12,
                        "milestones": [
                            {"week_start": 1, "week_end": 2, "phase": "Python基础语法",
                             "description": "变量、数据类型、条件判断、循环", "objectives": ["掌握基础语法", "能写简单脚本"],
                             "task_count": 10, "difficulty": 1},
                            {"week_start": 3, "week_end": 4, "phase": "NumPy与Pandas入门",
                             "description": "数组操作、DataFrame基础", "objectives": ["能处理CSV数据", "能做基础统计分析"],
                             "task_count": 8, "difficulty": 2},
                        ],
                        "daily_tasks": [
                            {"day": 1, "title": "安装Python + Hello World", "est_hours": 1.0},
                            {"day": 2, "title": "变量与数据类型练习", "est_hours": 1.5},
                        ],
                        "prerequisite_check": {"status": "passed", "details": [], "warnings": []},
                        "evaluation": {"score": 8, "issues": [], "suggestions": []}
                    }
                }),
                '{"event": "done", "data": {"session_id": "' + (req.session_id or f"session_{req.user_id}_{int(time.time())}") + '"}',
            ]
            for line in mock_lines:
                yield f"data: {line}\n\n"
                await asyncio.sleep(0.3)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/plan/{plan_id}")
async def get_plan(plan_id: str):
    """获取已生成的学习计划"""
    plan_path = os.path.join("data", "plans", f"{plan_id}.json")
    if not os.path.exists(plan_path):
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "计划不存在"}, status_code=404)
    with open(plan_path, encoding="utf-8") as f:
        return json.load(f)


@router.post("/plan/{plan_id}/adjust")
async def adjust_plan(plan_id: str, req: Request):
    """用户反馈后调整计划"""
    body = await req.json()
    feedback = body.get("feedback", {})
    # 将反馈 + 原计划发给 Hermes Agent 做调整
    # （当前返回模拟调整结果）
    plan_path = os.path.join("data", "plans", f"{plan_id}.json")
    if not os.path.exists(plan_path):
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "计划不存在"}, status_code=404)
    with open(plan_path, encoding="utf-8") as f:
        original = json.load(f)
    original["adjusted"] = True
    original["adjust_reason"] = feedback.get("text", "")
    return original