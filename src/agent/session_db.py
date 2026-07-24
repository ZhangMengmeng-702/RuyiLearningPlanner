# -*- coding: utf-8 -*-
"""
SessionDB — 会话持久化存储

参考 HermesAgent 的 SessionDB，提供：
- SQLite 数据库存储会话数据
- 系统提示缓存
- 会话压缩（摘要替代历史消息）
"""

import json
import logging
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


@dataclass
class SessionData:
    session_id: str
    user_id: str
    messages: List[Dict[str, Any]]
    plan_id: Optional[str] = None
    system_prompt: Optional[str] = None
    created_at: float = 0.0
    last_active_at: float = 0.0


class SessionDB:
    def __init__(self, db_path: str = ""):
        if not db_path:
            os.makedirs(DATA_DIR, exist_ok=True)
            db_path = os.path.join(DATA_DIR, "sessions.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    messages TEXT DEFAULT '[]',
                    plan_id TEXT,
                    system_prompt TEXT,
                    created_at REAL NOT NULL,
                    last_active_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_prompts (
                    session_id TEXT PRIMARY KEY,
                    system_prompt TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions(last_active_at)
            """)
            conn.commit()

    def create_session(self, user_id: str) -> str:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        now = time.time()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, messages, plan_id, 
                                     system_prompt, created_at, last_active_at)
                VALUES (?, ?, '[]', NULL, NULL, ?, ?)
            """, (session_id, user_id, now, now))
            conn.commit()

        logger.info(f"创建会话: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, user_id, messages, plan_id, 
                       system_prompt, created_at, last_active_at
                FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()

        if not row:
            return None

        session_id, user_id, messages_json, plan_id, system_prompt, created_at, last_active_at = row
        try:
            messages = json.loads(messages_json)
        except json.JSONDecodeError:
            messages = []

        return SessionData(
            session_id=session_id,
            user_id=user_id,
            messages=messages,
            plan_id=plan_id,
            system_prompt=system_prompt,
            created_at=created_at,
            last_active_at=last_active_at,
        )

    def update_session(self, session_id: str, **kwargs):
        now = time.time()
        updates = {"last_active_at": now}
        updates.update(kwargs)

        if "messages" in updates:
            updates["messages"] = json.dumps(updates["messages"], ensure_ascii=False)

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        params = list(updates.values()) + [session_id]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE sessions SET {set_clause} WHERE session_id = ?
            """, params)
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str):
        session = self.get_session(session_id)
        if not session:
            return

        session.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })

        self.update_session(session_id, messages=session.messages)

    def set_plan_id(self, session_id: str, plan_id: str):
        self.update_session(session_id, plan_id=plan_id)

    def update_system_prompt(self, session_id: str, system_prompt: str):
        self.update_session(session_id, system_prompt=system_prompt)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO system_prompts (session_id, system_prompt, created_at)
                VALUES (?, ?, ?)
            """, (session_id, system_prompt, time.time()))
            conn.commit()

    def get_system_prompt(self, session_id: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT system_prompt FROM system_prompts WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()

        return row[0] if row else None

    def cleanup_expired(self, max_age_hours: int = 24):
        cutoff = time.time() - max_age_hours * 3600

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id FROM sessions WHERE last_active_at < ?
            """, (cutoff,))
            expired = [row[0] for row in cursor.fetchall()]

            if expired:
                placeholders = ", ".join("?" * len(expired))
                cursor.execute(f"""
                    DELETE FROM sessions WHERE session_id IN ({placeholders})
                """, expired)
                cursor.execute(f"""
                    DELETE FROM system_prompts WHERE session_id IN ({placeholders})
                """, expired)
                conn.commit()

        logger.info(f"清理过期会话: {len(expired)} 个")

    def compress_session(self, session_id: str, max_messages: int = 20):
        session = self.get_session(session_id)
        if not session:
            return

        if len(session.messages) <= max_messages:
            return

        preserved = session.messages[-max_messages:]
        summary = self._generate_summary(session.messages[:-max_messages])

        if summary:
            compressed_messages = [{
                "role": "system",
                "content": f"[会话摘要]\n{summary}\n[以上是历史对话摘要]",
                "timestamp": time.time(),
            }] + preserved
        else:
            compressed_messages = preserved

        self.update_session(session_id, messages=compressed_messages)
        logger.info(f"压缩会话 {session_id}: {len(session.messages)} -> {len(compressed_messages)}")

    def _generate_summary(self, messages: List[Dict]) -> str:
        if len(messages) < 3:
            return ""

        try:
            user_messages = [m for m in messages if m.get("role") == "user"]
            assistant_messages = [m for m in messages if m.get("role") == "assistant"]

            summary_lines = []
            summary_lines.append(f"共有 {len(user_messages)} 条用户消息")

            if user_messages:
                recent_user = user_messages[-3:]
                summary_lines.append("用户最近问题：")
                for m in recent_user:
                    content = m.get("content", "")[:100]
                    summary_lines.append(f"- {content}")

            if assistant_messages:
                summary_lines.append("助手回复要点：")
                for m in assistant_messages[-2:]:
                    content = m.get("content", "")[:100]
                    summary_lines.append(f"- {content}")

            return "\n".join(summary_lines)

        except Exception as e:
            logger.error(f"生成会话摘要失败: {e}")
            return ""

    def get_user_sessions(self, user_id: str) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id FROM sessions WHERE user_id = ? ORDER BY last_active_at DESC
            """, (user_id,))
            return [row[0] for row in cursor.fetchall()]

    def get_messages(self, session_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return []
        messages = session.messages
        if offset > 0:
            messages = messages[offset:]
        if limit > 0:
            messages = messages[:limit]
        return messages

    def delete_session(self, session_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM system_prompts WHERE session_id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0