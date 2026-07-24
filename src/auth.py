# -*- coding: utf-8 -*-
"""
用户认证系统
- 用户注册、登录、会话管理
- 密码安全存储（PBKDF2-HMAC-SHA256）
"""
import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, asdict
from typing import Optional

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")

COOKIE_NAME = "rlp_session"
SESSION_TTL_DAYS = 30  # 会话有效期 30 天


def _hash_password(password: str, salt: str) -> str:
    """使用 PBKDF2-HMAC-SHA256 哈希密码"""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100000,
        dklen=32,
    )
    return dk.hex()


def _load_users() -> dict:
    """加载用户数据"""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_users(users: dict):
    """保存用户数据"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _load_sessions() -> dict:
    """加载会话数据"""
    if not os.path.exists(SESSIONS_FILE):
        return {}
    try:
        with open(SESSIONS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_sessions(sessions: dict):
    """保存会话数据"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


@dataclass
class User:
    user_id: str
    username: str
    password_hash: str
    salt: str
    created_at: float
    last_login: float = 0.0


def register_user(username: str, password: str) -> Optional[User]:
    """
    注册新用户
    
    Returns:
        成功返回 User 对象，用户名已存在返回 None
    """
    users = _load_users()
    
    if username in users:
        return None
    
    # 生成 user_id 和 salt
    user_id = f"user_{int(time.time())}_{secrets.token_hex(4)}"
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    
    user = User(
        user_id=user_id,
        username=username,
        password_hash=password_hash,
        salt=salt,
        created_at=time.time(),
        last_login=time.time(),
    )
    
    users[username] = asdict(user)
    _save_users(users)
    
    return user


def verify_user(username: str, password: str) -> Optional[User]:
    """
    验证用户名密码
    
    Returns:
        验证成功返回 User 对象，失败返回 None
    """
    users = _load_users()
    
    if username not in users:
        return None
    
    user_data = users[username]
    password_hash = _hash_password(password, user_data["salt"])
    
    if password_hash != user_data["password_hash"]:
        return None
    
    # 更新最后登录时间
    user_data["last_login"] = time.time()
    users[username] = user_data
    _save_users(users)
    
    return User(**user_data)


def get_user_by_username(username: str) -> Optional[User]:
    """根据用户名获取用户"""
    users = _load_users()
    if username not in users:
        return None
    return User(**users[username])


def get_user_by_id(user_id: str) -> Optional[User]:
    """根据 user_id 获取用户"""
    users = _load_users()
    for user_data in users.values():
        if user_data["user_id"] == user_id:
            return User(**user_data)
    return None


def create_session(user_id: str, username: str) -> str:
    """创建会话，返回 session token"""
    sessions = _load_sessions()
    
    # 清理过期会话
    now = time.time()
    expired = []
    for token, sess in sessions.items():
        if sess.get("expires_at", 0) < now:
            expired.append(token)
    for token in expired:
        del sessions[token]
    
    # 创建新会话
    token = secrets.token_hex(32)
    expires_at = now + SESSION_TTL_DAYS * 24 * 3600
    
    sessions[token] = {
        "user_id": user_id,
        "username": username,
        "created_at": now,
        "expires_at": expires_at,
    }
    
    _save_sessions(sessions)
    return token


def verify_session(token: str) -> Optional[dict]:
    """
    验证会话 token
    
    Returns:
        有效返回会话数据（包含 user_id, username），无效返回 None
    """
    if not token:
        return None
    
    sessions = _load_sessions()
    
    if token not in sessions:
        return None
    
    session = sessions[token]
    
    # 检查是否过期
    if session.get("expires_at", 0) < time.time():
        del sessions[token]
        _save_sessions(sessions)
        return None
    
    return session


def destroy_session(token: str) -> bool:
    """销毁会话（登出）"""
    sessions = _load_sessions()
    
    if token in sessions:
        del sessions[token]
        _save_sessions(sessions)
        return True
    
    return False


def is_auth_enabled() -> bool:
    """检查是否启用认证（默认启用）"""
    # 可以通过环境变量控制
    return os.environ.get("DISABLE_AUTH", "").lower() not in ("1", "true", "yes")
