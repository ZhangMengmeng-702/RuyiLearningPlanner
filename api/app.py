# -*- coding: utf-8 -*-
"""FastAPI 主应用 — CORS + 认证中间件 + 路由注册"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from api.v1.endpoints import learn_chat, profile, progress, knowledge, auth
from api.middlewares.auth import add_auth_middleware

app = FastAPI(title="Ruyi Learning Planner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册认证中间件
add_auth_middleware(app)

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(learn_chat.router, prefix="/api/v1/learn")
app.include_router(profile.router, prefix="/api/v1/profile")
app.include_router(progress.router, prefix="/api/v1/progress")
app.include_router(knowledge.router, prefix="/api/v1/knowledge")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "learning-planner"}