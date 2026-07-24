# -*- coding: utf-8 -*-
"""认证相关的依赖注入工具"""
from fastapi import Request, HTTPException
from src.auth import is_auth_enabled


async def get_current_user(request: Request) -> dict:
    """
    获取当前登录用户
    
    Returns:
        {"user_id": "...", "username": "..."}
    
    Raises:
        HTTPException: 401 未登录
    """
    if not is_auth_enabled():
        # 认证禁用时，返回默认用户（用于开发环境）
        return {"user_id": "demo_user", "username": "demo"}
    
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    
    return user


async def get_current_user_id(request: Request) -> str:
    """获取当前登录用户的 user_id"""
    user = await get_current_user(request)
    return user["user_id"]
