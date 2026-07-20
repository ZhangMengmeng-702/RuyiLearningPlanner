# -*- coding: utf-8 -*-
"""用户画像管理器（JSON 文件存储）"""
import json, os, time
from dataclasses import dataclass, asdict
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "profiles")

@dataclass
class Profile:
    user_id: str
    goal: str = ""
    current_level: str = ""          # beginner / intermediate / advanced
    hours_per_week: int = 0
    preference: str = ""             # video / reading / hands-on
    known_topics: list[str] = None   # 已掌握的知识点
    created_at: float = 0.0
    updated_at: float = 0.0

    def is_complete(self) -> bool:
        return all([self.goal, self.current_level, self.hours_per_week > 0, self.preference])


class ProfileManager:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _path(self, user_id: str) -> str:
        return os.path.join(self.data_dir, f"{user_id}.json")

    def get(self, user_id: str) -> Optional[Profile]:
        path = self._path(user_id)
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return Profile(**data)

    def create(self, user_id: str) -> Profile:
        profile = Profile(user_id=user_id, created_at=time.time(), updated_at=time.time())
        self.save(profile)
        return profile

    def save(self, profile: Profile) -> None:
        profile.updated_at = time.time()
        with open(self._path(profile.user_id), "w", encoding="utf-8") as f:
            json.dump(asdict(profile), f, ensure_ascii=False, indent=2)

    def update(self, user_id: str, **kwargs) -> Profile:
        profile = self.get(user_id) or self.create(user_id)
        for k, v in kwargs.items():
            if hasattr(profile, k) and v is not None:
                setattr(profile, k, v)
        self.save(profile)
        return profile