# -*- coding: utf-8 -*-
"""
Manage Profile Tool — 用户画像管理工具

功能：创建、查询、更新用户学习画像数据
依赖：profile_manager 模块，JSON 文件存储
"""

import json
import logging
from typing import Any, Dict

from src.agent.tool_registry import tool
from src.profile_manager import ProfileManager, asdict

logger = logging.getLogger(__name__)


@tool(
    name="manage_profile",
    description="管理用户学习画像。支持创建、查询、更新操作。",
    toolset="learning",
    emoji="👤",
)
def manage_profile(action: str, user_id: str, **kwargs) -> str:
    pm = ProfileManager()

    if action == "create":
        profile = pm.create(user_id)
        profile_dict = asdict(profile)
        profile_dict["is_complete"] = profile.is_complete()
        return json.dumps({"success": True, "profile": profile_dict}, ensure_ascii=False)

    elif action == "get":
        profile = pm.get(user_id)
        if profile:
            profile_dict = asdict(profile)
            profile_dict["is_complete"] = profile.is_complete()
            return json.dumps({"success": True, "profile": profile_dict}, ensure_ascii=False)
        return json.dumps({"success": False, "error": "用户画像不存在"}, ensure_ascii=False)

    elif action == "update":
        updates = {k: v for k, v in kwargs.items() if v is not None}
        profile = pm.update(user_id, **updates)
        if profile:
            profile_dict = asdict(profile)
            profile_dict["is_complete"] = profile.is_complete()
            return json.dumps({"success": True, "profile": profile_dict}, ensure_ascii=False)
        return json.dumps({"success": False, "error": "更新失败"}, ensure_ascii=False)

    elif action == "delete":
        pm.delete(user_id)
        return json.dumps({"success": True}, ensure_ascii=False)

    return json.dumps({"success": False, "error": f"未知操作: {action}"}, ensure_ascii=False)