# -*- coding: utf-8 -*-
"""学习对话 SSE 端点 — 接收前端消息，调 AgentOrchestrator，流式返回"""
import asyncio
import json
import logging
import os
import time
from typing import Generator

from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from src.utils.path_security import safe_plan_id, safe_session_id, safe_user_id, PathSecurityError
from api.deps import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

PLANS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "plans"))


class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str = ""


def _get_orchestrator():
    """获取 AgentOrchestrator 实例（懒加载）"""
    from src.agent.orchestrator import AgentOrchestrator
    return AgentOrchestrator()


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


def _generate_events(user_id: str, message: str, session_id: str) -> Generator[str, None, None]:
    """生成 SSE 事件流"""
    from src.agent.session_db import SessionDB
    
    orchestrator = _get_orchestrator()
    db = SessionDB()

    # 创建或获取会话
    if not session_id:
        session_id = db.create_session(user_id)
    else:
        # 验证会话是否存在且属于该用户
        session = db.get_session(session_id)
        if not session or session.user_id != user_id:
            session_id = db.create_session(user_id)
    
    yield json.dumps({"event": "session_created", "data": {"session_id": session_id}}, ensure_ascii=False)

    # 保存用户消息
    db.add_message(session_id, "user", message)

    assistant_text = ""
    plan_data = None
    plan_id = None
    last_save_time = 0.0
    last_save_text_len = 0
    SAVE_INTERVAL_SEC = 0.5  # 每0.5秒保存一次
    SAVE_TOKEN_THRESHOLD = 50  # 每50个token保存一次
    token_count = 0
    message_created = False  # 是否已创建assistant消息

    def _save_assistant_message():
        """保存或更新 assistant 消息"""
        nonlocal message_created
        session = db.get_session(session_id)
        if not session:
            return
        if not message_created:
            # 第一次保存：添加新消息
            db.add_message(session_id, "assistant", assistant_text)
            message_created = True
        else:
            # 后续保存：更新最后一条消息
            for i in range(len(session.messages) - 1, -1, -1):
                if session.messages[i].get("role") == "assistant":
                    session.messages[i]["content"] = assistant_text
                    break
            db.update_session(session_id, messages=session.messages)

    try:
        # 调用 orchestrator.generate_plan（结构化流程）
        for event_str in orchestrator.generate_plan(user_id, message):
            yield event_str
            
            # 收集文本和计划数据用于持久化
            try:
                event = json.loads(event_str)
                event_type = event.get("event")
                data = event.get("data", {})
                
                if event_type == "token":
                    token_text = data if isinstance(data, str) else ""
                    if not token_text:
                        continue
                    assistant_text += token_text
                    token_count += 1
                    
                    # 节流保存：满足时间间隔或token数量阈值时保存
                    now = time.time()
                    if (now - last_save_time >= SAVE_INTERVAL_SEC and 
                        len(assistant_text) > last_save_text_len) or \
                       token_count >= SAVE_TOKEN_THRESHOLD:
                        _save_assistant_message()
                        last_save_time = now
                        last_save_text_len = len(assistant_text)
                        token_count = 0
                        
                elif event_type == "plan":
                    plan_data = data if isinstance(data, dict) else None
                    plan_id = plan_data.get("plan_id") if plan_data else None
                elif event_type == "done":
                    pass
            except (json.JSONDecodeError, AttributeError):
                pass
    except Exception as e:
        logger.error(f"对话生成失败: {e}", exc_info=True)
        error_msg = str(e)
        assistant_text += f"\n[错误] {error_msg}"
        yield json.dumps({"event": "error", "data": {"message": error_msg}}, ensure_ascii=False)
    finally:
        # 最终保存：只有有内容才保存
        if assistant_text and len(assistant_text) > last_save_text_len:
            _save_assistant_message()
        
        # 如果生成了计划但没有任何token文本，也要确保有一条进度消息
        if plan_data and plan_id and not assistant_text:
            db.add_message(session_id, "assistant", "计划生成完成。")
        
        # 如果生成了计划，保存一条结果消息
        if plan_data and plan_id:
            total_weeks = plan_data.get("total_weeks", 0)
            phases = len(plan_data.get("milestones", []))
            result_msg = (
                f"✅ 学习计划已生成！共 **{total_weeks} 周**，{phases} 个阶段。\n\n"
                f"👉 [切换到「计划看板」查看详情](/learn/plan/{plan_id})"
            )
            db.add_message(session_id, "assistant", result_msg)
        
        # 保存关联的计划ID
        if plan_id:
            db.set_plan_id(session_id, plan_id)


@router.post("/chat")
async def chat_stream(req: ChatRequest, current_user_id: str = Depends(get_current_user_id)):
    """SSE 流式聊天：前端发消息 → AgentOrchestrator 编排 → 流式返回"""
    # 权限校验：只能用自己的 user_id
    try:
        req_user_id = safe_user_id(req.user_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的用户ID: {e}"}, status_code=400)
    
    if req_user_id != current_user_id:
        return JSONResponse({"error": "无权使用其他用户的身份"}, status_code=403)

    def event_generator():
        for event in _generate_events(current_user_id, req.message, req.session_id):
            yield f"data: {event}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/plan/{plan_id}")
async def get_plan(plan_id: str, user_id: str = "", current_user_id: str = Depends(get_current_user_id)):
    """获取已生成的学习计划"""
    if plan_id == "latest":
        return await get_latest_plan(current_user_id)
    
    try:
        safe_id = safe_plan_id(plan_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的计划ID: {e}"}, status_code=400)
    
    # 权限校验：只能查看自己的计划
    if not _plan_belongs_to_user(safe_id, current_user_id):
        return JSONResponse({"error": "无权访问其他用户的计划"}, status_code=403)
    
    plan_path = os.path.join(PLANS_DIR, f"{safe_id}.json")
    if not os.path.exists(plan_path):
        return JSONResponse({"error": "计划不存在"}, status_code=404)
    with open(plan_path, encoding="utf-8") as f:
        return json.load(f)


async def get_latest_plan(user_id: str):
    """获取用户最新的学习计划"""
    if not os.path.exists(PLANS_DIR):
        return JSONResponse({"error": "计划不存在"}, status_code=404)

    plan_files = [f for f in os.listdir(PLANS_DIR) if f.endswith(".json") and f.startswith("plan_")]
    if not plan_files:
        return JSONResponse({"error": "计划不存在"}, status_code=404)

    plan_files.sort(reverse=True)

    for plan_file in plan_files:
        plan_path = os.path.join(PLANS_DIR, plan_file)
        try:
            with open(plan_path, encoding="utf-8") as f:
                plan = json.load(f)
            if not user_id or plan.get("user_id") == user_id:
                return plan
        except Exception:
            continue

    return JSONResponse({"error": "计划不存在"}, status_code=404)


@router.post("/plan/{plan_id}/adjust")
async def adjust_plan(plan_id: str, request: Request, current_user_id: str = Depends(get_current_user_id)):
    """用户反馈后调整计划（SSE 流式）"""
    try:
        safe_id = safe_plan_id(plan_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的计划ID: {e}"}, status_code=400)
    
    # 权限校验：只能调整自己的计划
    if not _plan_belongs_to_user(safe_id, current_user_id):
        return JSONResponse({"error": "无权调整其他用户的计划"}, status_code=403)
    
    body = await request.json()
    feedback = body.get("feedback", {})

    def event_generator():
        from src.agent.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator()
        try:
            for event in orchestrator.adjust_plan(safe_id, feedback):
                yield f"data: {event}\n\n"
        except Exception as e:
            logger.error(f"计划调整失败: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'data': {'message': str(e)}}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/plan/{plan_id}/ics")
async def get_plan_ics(plan_id: str, current_user_id: str = Depends(get_current_user_id)):
    """获取计划的日历文件（ICS）"""
    try:
        safe_id = safe_plan_id(plan_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的计划ID: {e}"}, status_code=400)
    
    # 权限校验：只能下载自己的计划
    if not _plan_belongs_to_user(safe_id, current_user_id):
        return JSONResponse({"error": "无权访问其他用户的计划"}, status_code=403)
    
    ics_path = os.path.join(PLANS_DIR, f"{safe_id}.ics")
    if not os.path.exists(ics_path):
        return JSONResponse({"error": "日历文件不存在"}, status_code=404)
    from fastapi.responses import FileResponse
    return FileResponse(ics_path, media_type="text/calendar", filename=f"{safe_id}.ics")


@router.get("/session/list")
async def list_user_sessions(current_user_id: str = Depends(get_current_user_id)):
    """获取当前用户的会话列表"""
    from src.agent.session_db import SessionDB
    db = SessionDB()
    session_ids = db.get_user_sessions(current_user_id)
    sessions = []
    for sid in session_ids:
        session = db.get_session(sid)
        if session:
            sessions.append({
                "session_id": session.session_id,
                "plan_id": session.plan_id,
                "created_at": session.created_at,
                "last_active_at": session.last_active_at,
                "message_count": len(session.messages),
                "first_message": session.messages[0]["content"][:50] if session.messages else "",
            })
    return {"sessions": sessions}


@router.get("/session/{session_id}")
async def get_session(session_id: str, current_user_id: str = Depends(get_current_user_id)):
    """获取会话信息"""
    try:
        safe_sid = safe_session_id(session_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的会话ID: {e}"}, status_code=400)
    
    from src.agent.session_db import SessionDB
    db = SessionDB()
    session = db.get_session(safe_sid)
    if not session:
        return JSONResponse({"error": "会话不存在"}, status_code=404)
    
    # 权限校验：只能访问自己的会话
    if session.user_id != current_user_id:
        return JSONResponse({"error": "无权访问其他用户的会话"}, status_code=403)
    
    return session


@router.get("/session/{session_id}/messages")
async def get_session_messages(session_id: str, limit: int = 50, offset: int = 0, current_user_id: str = Depends(get_current_user_id)):
    """获取会话消息历史"""
    try:
        safe_sid = safe_session_id(session_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的会话ID: {e}"}, status_code=400)
    
    from src.agent.session_db import SessionDB
    db = SessionDB()
    session = db.get_session(safe_sid)
    if not session:
        return JSONResponse({"error": "会话不存在"}, status_code=404)
    
    # 权限校验：只能访问自己的会话
    if session.user_id != current_user_id:
        return JSONResponse({"error": "无权访问其他用户的会话"}, status_code=403)
    
    messages = db.get_messages(safe_sid, limit=limit, offset=offset)
    return {"session_id": safe_sid, "messages": messages, "limit": limit, "offset": offset}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, current_user_id: str = Depends(get_current_user_id)):
    """删除会话"""
    try:
        safe_sid = safe_session_id(session_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的会话ID: {e}"}, status_code=400)
    
    from src.agent.session_db import SessionDB
    db = SessionDB()
    session = db.get_session(safe_sid)
    if not session:
        return JSONResponse({"error": "会话不存在"}, status_code=404)
    
    # 权限校验：只能删除自己的会话
    if session.user_id != current_user_id:
        return JSONResponse({"error": "无权删除其他用户的会话"}, status_code=403)
    
    result = db.delete_session(safe_sid)
    return {"status": "ok" if result else "not_found"}


@router.post("/cleanup")
async def cleanup_sessions():
    """清理过期会话"""
    from src.agent.session_db import SessionDB
    db = SessionDB()
    count = db.cleanup_expired()
    return {"status": "ok", "cleaned_count": count}


@router.post("/chat/stream")
async def chat_stream_direct(req: ChatRequest):
    """直接流式 LLM 对话（token 级推送）"""
    from tools.call_llm import call_llm_stream

    def event_generator():
        for chunk in call_llm_stream(
            system_prompt="你是一个学习规划助手",
            user_message=req.message,
            temperature=0.7,
        ):
            yield f"data: {json.dumps({'event': 'stream_chunk', 'data': {'content': chunk}}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'event': 'done', 'data': {}}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat/hermes")
async def chat_hermes(req: ChatRequest):
    """直接调用 Hermes Agent（HTTP 连接）"""
    import os
    from src.llm.hermes_client import HermesClient

    hermes_enabled = os.getenv("HERMES_ENABLED", "false").lower() == "true"
    if not hermes_enabled:
        return JSONResponse(
            {"error": "Hermes Agent 未启用，请设置 HERMES_ENABLED=true"},
            status_code=503,
        )

    try:
        client = HermesClient()
        stream = client.chat_completion(
            messages=[{"role": "user", "content": req.message}],
            stream=True,
        )

        def event_generator():
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'event': 'stream_chunk', 'data': {'content': delta.content}}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'event': 'done', 'data': {'provider': 'hermes'}}, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Hermes 调用失败: {e}", exc_info=True)
        return JSONResponse(
            {"error": f"Hermes 调用失败: {str(e)}"},
            status_code=500,
        )
