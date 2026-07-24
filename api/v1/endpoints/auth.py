# -*- coding: utf-8 -*-
"""用户认证 API — 注册、登录、登出、状态查询"""
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.auth import (
    COOKIE_NAME,
    register_user,
    verify_user,
    verify_session,
    create_session,
    destroy_session,
    is_auth_enabled,
)

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/status")
async def auth_status(request: Request):
    """查询当前登录状态"""
    cookie_val = request.cookies.get(COOKIE_NAME)
    session = verify_session(cookie_val) if cookie_val else None
    
    return {
        "auth_enabled": is_auth_enabled(),
        "logged_in": session is not None,
        "user": {
            "user_id": session["user_id"],
            "username": session["username"],
        } if session else None,
    }


@router.post("/register")
async def register(body: RegisterRequest, response: Response):
    """用户注册"""
    username = body.username.strip()
    password = body.password
    
    # 简单验证
    if len(username) < 3:
        return JSONResponse(
            status_code=400,
            content={"error": "用户名至少需要3个字符"}
        )
    if len(password) < 6:
        return JSONResponse(
            status_code=400,
            content={"error": "密码至少需要6个字符"}
        )
    
    user = register_user(username, password)
    if not user:
        return JSONResponse(
            status_code=400,
            content={"error": "用户名已存在"}
        )
    
    # 注册成功自动登录
    token = create_session(user.user_id, user.username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=30 * 24 * 3600,
        samesite="lax",
    )
    
    return {
        "status": "ok",
        "message": "注册成功",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
        }
    }


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    """用户登录"""
    user = verify_user(body.username, body.password)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "用户名或密码错误"}
        )
    
    token = create_session(user.user_id, user.username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=30 * 24 * 3600,
        samesite="lax",
    )
    
    return {
        "status": "ok",
        "message": "登录成功",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
        }
    }


@router.post("/logout")
async def logout(request: Request, response: Response):
    """用户登出"""
    cookie_val = request.cookies.get(COOKIE_NAME)
    if cookie_val:
        destroy_session(cookie_val)
    
    response.delete_cookie(key=COOKIE_NAME)
    
    return {"status": "ok", "message": "已登出"}
