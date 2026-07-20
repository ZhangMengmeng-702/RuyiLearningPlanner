# -*- coding: utf-8 -*-
"""FastAPI 主应用 — CORS + 路由注册"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.endpoints import learn_chat, profile, progress

app = FastAPI(title="Ruyi Learning Planner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(learn_chat.router, prefix="/api/v1/learn")
app.include_router(profile.router, prefix="/api/v1/profile")
app.include_router(progress.router, prefix="/api/v1/progress")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "learning-planner"}