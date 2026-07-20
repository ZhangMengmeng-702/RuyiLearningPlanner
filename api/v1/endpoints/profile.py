# -*- coding: utf-8 -*-
"""用户画像 API — CRUD 操作"""
import json
from fastapi import APIRouter
from pydantic import BaseModel
from src.profile_manager import ProfileManager

router = APIRouter()
pm = ProfileManager()


class ProfileUpdate(BaseModel):
    goal: str = ""
    current_level: str = ""
    hours_per_week: int = 0
    preference: str = ""
    known_topics: list[str] = []


@router.get("/{user_id}")
async def get_profile(user_id: str):
    profile = pm.get(user_id)
    if not profile:
        return {"user_id": user_id, "exists": False}
    return {"user_id": user_id, "exists": True, "profile": {
        "goal": profile.goal,
        "current_level": profile.current_level,
        "hours_per_week": profile.hours_per_week,
        "preference": profile.preference,
        "known_topics": profile.known_topics or [],
        "is_complete": profile.is_complete(),
    }}


@router.post("/{user_id}")
async def update_profile(user_id: str, body: ProfileUpdate):
    profile = pm.update(
        user_id,
        goal=body.goal,
        current_level=body.current_level,
        hours_per_week=body.hours_per_week,
        preference=body.preference,
        known_topics=body.known_topics,
    )
    return {"user_id": user_id, "status": "updated", "is_complete": profile.is_complete()}


@router.post("/{user_id}/init")
async def init_profile(user_id: str):
    profile = pm.create(user_id)
    return {"user_id": user_id, "status": "created"}