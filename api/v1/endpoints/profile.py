# -*- coding: utf-8 -*-
"""用户画像 API — CRUD 操作"""
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.profile_manager import ProfileManager
from src.utils.path_security import safe_user_id, PathSecurityError
from api.deps import get_current_user_id

router = APIRouter()
pm = ProfileManager()


class ProfileUpdate(BaseModel):
    goal: str = ""
    current_level: str = ""
    hours_per_week: int = 0
    preference: str = ""
    known_topics: list[str] = []


@router.get("")
@router.get("/me")
async def get_my_profile(current_user_id: str = Depends(get_current_user_id)):
    """获取当前登录用户的画像"""
    profile = pm.get(current_user_id)
    if not profile:
        return {"user_id": current_user_id, "exists": False}
    return {"user_id": current_user_id, "exists": True, "profile": {
        "goal": profile.goal,
        "current_level": profile.current_level,
        "hours_per_week": profile.hours_per_week,
        "preference": profile.preference,
        "known_topics": profile.known_topics or [],
        "is_complete": profile.is_complete(),
    }}


@router.get("/{user_id}")
async def get_profile(user_id: str, current_user_id: str = Depends(get_current_user_id)):
    """获取指定用户的画像（只能查看自己的）"""
    try:
        safe_uid = safe_user_id(user_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的用户ID: {e}"}, status_code=400)
    
    # 权限校验：只能查看自己的
    if safe_uid != current_user_id:
        return JSONResponse({"error": "无权访问其他用户的数据"}, status_code=403)
    
    profile = pm.get(safe_uid)
    if not profile:
        return {"user_id": safe_uid, "exists": False}
    return {"user_id": safe_uid, "exists": True, "profile": {
        "goal": profile.goal,
        "current_level": profile.current_level,
        "hours_per_week": profile.hours_per_week,
        "preference": profile.preference,
        "known_topics": profile.known_topics or [],
        "is_complete": profile.is_complete(),
    }}


@router.post("")
@router.post("/me")
async def update_my_profile(body: ProfileUpdate, current_user_id: str = Depends(get_current_user_id)):
    """更新当前登录用户的画像"""
    profile = pm.update(
        current_user_id,
        goal=body.goal,
        current_level=body.current_level,
        hours_per_week=body.hours_per_week,
        preference=body.preference,
        known_topics=body.known_topics,
    )
    return {"user_id": current_user_id, "status": "updated", "is_complete": profile.is_complete()}


@router.post("/{user_id}")
async def update_profile(user_id: str, body: ProfileUpdate, current_user_id: str = Depends(get_current_user_id)):
    """更新指定用户的画像（只能修改自己的）"""
    try:
        safe_uid = safe_user_id(user_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的用户ID: {e}"}, status_code=400)
    
    # 权限校验：只能修改自己的
    if safe_uid != current_user_id:
        return JSONResponse({"error": "无权修改其他用户的数据"}, status_code=403)
    
    profile = pm.update(
        safe_uid,
        goal=body.goal,
        current_level=body.current_level,
        hours_per_week=body.hours_per_week,
        preference=body.preference,
        known_topics=body.known_topics,
    )
    return {"user_id": safe_uid, "status": "updated", "is_complete": profile.is_complete()}


@router.post("/{user_id}/init")
async def init_profile(user_id: str, current_user_id: str = Depends(get_current_user_id)):
    """初始化用户画像（只能初始化自己的）"""
    try:
        safe_uid = safe_user_id(user_id)
    except PathSecurityError as e:
        return JSONResponse({"error": f"无效的用户ID: {e}"}, status_code=400)
    
    # 权限校验：只能操作自己的
    if safe_uid != current_user_id:
        return JSONResponse({"error": "无权操作其他用户的数据"}, status_code=403)
    
    profile = pm.create(safe_uid)
    return {"user_id": safe_uid, "status": "created"}