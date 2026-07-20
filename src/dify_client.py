# -*- coding: utf-8 -*-
"""Dify 知识库检索客户端（纯 urllib，无第三方依赖）"""
import json, os, urllib.request
from dataclasses import dataclass

@dataclass
class RetrievalResult:
    content: str
    score: float
    title: str
    metadata: dict

class DifyClient:
    def __init__(self, base_url: str = None, api_key: str = None, kb_id: str = None):
        self.base_url = (base_url or os.getenv("DIFY_BASE_URL", "http://localhost/v1")).rstrip("/")
        self.api_key = api_key or self._load_key()
        self.kb_id = kb_id or os.getenv("DIFY_KB_ID", "")

    def _load_key(self) -> str:
        key_path = os.getenv("DIFY_KEY_PATH", "key.txt")
        if os.path.exists(key_path):
            with open(key_path, encoding="utf-8") as f:
                return f.read().strip()
        raise ValueError("Dify API Key 未设置")

    def retrieve(self, query: str, top_k: int = 5, score_threshold: float = 0.5) -> list[RetrievalResult]:
        url = f"{self.base_url}/datasets/{self.kb_id}/retrieve"
        payload = json.dumps({
            "query": query,
            "retrieval_setting": {
                "top_k": top_k,
                "score_threshold": score_threshold,
                "score_threshold_enabled": True,
            }
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [
            RetrievalResult(content=r.get("content",""), score=r.get("score",0),
                            title=r.get("title",""), metadata=r.get("metadata",{}))
            for r in data.get("records", [])
        ]

    def retrieve_formatted(self, query: str, top_k: int = 5) -> str:
        results = self.retrieve(query, top_k=top_k)
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] {r.title} (score:{r.score:.2f})\n{r.content}")
        return "\n\n".join(lines) if lines else "(知识库未检索到相关内容)"