# -*- coding: utf-8 -*-
"""
Manage Profile Tool — 用户画像管理工具

功能：创建/读取/更新用户学习画像
依赖：src/profile_manager.py 中的 ProfileManager
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from src.profile_manager import ProfileManager
    _profile_mgr = ProfileManager()
except ImportError:
    logger.warning("ProfileManager 导入失败，将使用 mock 模式")

    class MockProfile:
        def __init__(self, user_id: str, **kwargs):
            self.user_id = user_id
            self.goal = kwargs.get("goal", "")
            self.current_level = kwargs.get("current_level", "")
            self.hours_per_week = kwargs.get("hours_per_week", 0)
            self.preference = kwargs.get("preference", "")
            self.known_topics = kwargs.get("known_topics", [])

        def is_complete(self) -> bool:
            return all([self.goal, self.current_level, self.hours_per_week > 0, self.preference])

    class MockProfileManager:
        def __init__(self):
            self._profiles = {}

        def get(self, user_id: str):
            return self._profiles.get(user_id)

        def create(self, user_id: str):
            profile = MockProfile(user_id=user_id)
            self._profiles[user_id] = profile
            return profile

        def update(self, user_id: str, **kwargs):
            profile = self.get(user_id) or self.create(user_id)
            for k, v in kwargs.items():
                if hasattr(profile, k) and v is not None:
                    setattr(profile, k, v)
            return profile

    _profile_mgr = MockProfileManager()


def check_manage_profile_requirements() -> bool:
    return True


MANAGE_PROFILE_SCHEMA = {
    "name": "manage_profile",
    "description": "管理用户学习画像（创建/读取/更新）。用于采集和管理用户的学习目标、当前水平、每周学习时间、学习偏好等信息。",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get", "create", "update"],
                "description": "操作类型：get(读取画像), create(创建新画像), update(更新画像)",
            },
            "user_id": {"type": "string", "description": "用户ID"},
            "goal": {"type": "string", "description": "学习目标（如：学习Python数据分析）"},
            "current_level": {"type": "string", "description": "当前水平：beginner(零基础)/intermediate(有经验)/advanced(进阶)"},
            "hours_per_week": {"type": "integer", "description": "每周可投入学习小时数（默认0）", "minimum": 0, "maximum": 100},
            "preference": {"type": "string", "description": "学习偏好：video(视频)/reading(文档)/hands-on(实战)"},
            "known_topics": {"type": "array", "items": {"type": "string"}, "description": "已掌握的知识点列表"},
        },
        "required": ["action", "user_id"]
    }
}


def _handle_manage_profile(args: Dict[str, Any]) -> str:
    action = args.get("action", "")
    user_id = args.get("user_id", "")

    if not action or not user_id:
        return json.dumps({"success": False, "error": "action 和 user_id 参数不能为空"}, ensure_ascii=False)

    try:
        if action == "get":
            profile = _profile_mgr.get(user_id)
            if not profile:
                return json.dumps({
                    "success": True,
                    "user_id": user_id,
                    "exists": False,
                }, ensure_ascii=False)
            return json.dumps({
                "success": True,
                "user_id": user_id,
                "exists": True,
                "profile": {
                    "goal": profile.goal,
                    "current_level": profile.current_level,
                    "hours_per_week": profile.hours_per_week,
                    "preference": profile.preference,
                    "known_topics": profile.known_topics or [],
                    "is_complete": profile.is_complete(),
                },
            }, ensure_ascii=False, indent=2)

        elif action == "create":
            profile = _profile_mgr.create(user_id)
            return json.dumps({
                "success": True,
                "user_id": user_id,
                "message": "画像已创建",
                "is_complete": profile.is_complete(),
            }, ensure_ascii=False)

        elif action == "update":
            update_data = {}
            for key in ["goal", "current_level", "hours_per_week", "preference", "known_topics"]:
                if key in args:
                    update_data[key] = args[key]

            if not update_data:
                return json.dumps({"success": False, "error": "没有提供任何更新数据"}, ensure_ascii=False)

            profile = _profile_mgr.update(user_id, **update_data)
            return json.dumps({
                "success": True,
                "user_id": user_id,
                "message": "画像已更新",
                "is_complete": profile.is_complete(),
                "updated_fields": list(update_data.keys()),
            }, ensure_ascii=False, indent=2)

        else:
            return json.dumps({"success": False, "error": f"不支持的 action: {action}"}, ensure_ascii=False)

    except Exception as e:
        logger.error(f"manage_profile 调用失败: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "action": action,
            "user_id": user_id,
        }, ensure_ascii=False)


try:
    from src.agent.tool_registry import registry
    registry.register(
        name="manage_profile",
        toolset="learning",
        schema=MANAGE_PROFILE_SCHEMA,
        handler=_handle_manage_profile,
        check_fn=check_manage_profile_requirements,
        emoji="👤",
    )
except ImportError:
    pass
