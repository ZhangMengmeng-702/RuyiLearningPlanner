# -*- coding: utf-8 -*-
"""Dify 知识库检索客户端（http.client，无第三方依赖）

自动双端点降级：先试 /retrieve，404 则回退 /hit-testing。
响应结构不同，代码内部自动适配。
"""
import http.client, json, os
from dataclasses import dataclass


_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class RetrievalResult:
    content: str
    score: float
    title: str
    metadata: dict


class DifyClient:
    """Dify 知识库检索客户端"""

    def __init__(self, base_url: str = None, api_key: str = None, kb_id: str = None):
        self.base_url = base_url or os.getenv("DIFY_BASE_URL", "http://localhost/v1")
        self.kb_id = kb_id if kb_id is not None else (os.getenv("DIFY_KB_ID") or self._read_env("DIFY_KB_ID", ""))
        self.api_key = api_key if api_key is not None else self._load_key()

    def _parse_base_url(self):
        """解析 base_url，返回 (host, port, path_prefix)"""
        from urllib.parse import urlparse
        parsed = urlparse(self.base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path.rstrip("/")
        return host, port, path

    @staticmethod
    def _find_project_file(name: str) -> str:
        """在项目目录下找文件（兼容任意 CWD 调用）"""
        path = os.path.join(_PROJECT_DIR, name)
        if os.path.exists(path):
            return path
        # 也检查 CWD
        if os.path.exists(name):
            return name
        return ""

    @staticmethod
    def _read_env(key: str, default: str = "") -> str:
        val = os.getenv(key)
        if val:
            return val
        env_path = DifyClient._find_project_file(".env")
        if env_path:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}="):
                        return line.split("=", 1)[1].strip()
        # 也试 ~/.env
        home_env = os.path.expanduser("~/.env")
        if os.path.exists(home_env):
            with open(home_env, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}="):
                        return line.split("=", 1)[1].strip()
        return default

    def _load_key(self, passed_key: str = None) -> str:
        if passed_key:
            return passed_key
        # 优先从环境变量读取
        env_key = os.getenv("DIFY_API_KEY")
        if env_key:
            return env_key
        # 从 key.txt 读取
        key_path = os.getenv("DIFY_KEY_PATH", "key.txt")
        if os.path.exists(key_path):
            with open(key_path, encoding="utf-8") as f:
                return f.read().strip()
        # fallback: 项目目录下的 key.txt
        proj_key = DifyClient._find_project_file("key.txt")
        if proj_key:
            with open(proj_key, encoding="utf-8") as f:
                return f.read().strip()
        raise ValueError("Dify API Key 未设置")

    # ── 公开方法 ──────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 5,
                 score_threshold: float = 0.5) -> list[RetrievalResult]:
        if not self.kb_id:
            print("[DifyClient] kb_id 未设置")
            return []

        host, port, path_prefix = self._parse_base_url()

        for endpoint, builder in [
            ("/retrieve", self._build_retrieve_payload),
            ("/hit-testing", self._build_hit_testing_payload),
        ]:
            try:
                conn = http.client.HTTPConnection(host, port, timeout=30)
                full_path = f"{path_prefix}/datasets/{self.kb_id}{endpoint}"
                conn.request(
                    "POST",
                    full_path,
                    body=builder(query, top_k, score_threshold),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                )
                resp = conn.getresponse()
                raw = resp.read().decode("utf-8")
                conn.close()

                if resp.status == 200:
                    data = json.loads(raw)
                    parser = (self._parse_retrieve_records if endpoint == "/retrieve"
                              else self._parse_hit_testing_records)
                    return parser(data)
                elif resp.status == 404:
                    continue
                else:
                    print(f"[DifyClient] {endpoint} HTTP {resp.status}: {raw[:200]}")
                    return []
            except Exception as e:
                print(f"[DifyClient] {endpoint} 请求失败: {e}")
                return []
        return []

    def retrieve_formatted(self, query: str, top_k: int = 5) -> str:
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return "(知识库未检索到相关内容)"
        return "\n\n".join(
            f"[{i}] {r.title} (score:{r.score:.2f})\n{r.content}"
            for i, r in enumerate(results, 1)
        )

    # ── Payload ────────────────────────────────────────────────

    @staticmethod
    def _build_retrieve_payload(query: str, top_k: int, threshold: float) -> bytes:
        return json.dumps({
            "query": query,
            "retrieval_setting": {
                "top_k": top_k,
                "score_threshold": threshold,
                "score_threshold_enabled": True,
            },
        }).encode("utf-8")

    @staticmethod
    def _build_hit_testing_payload(query: str, top_k: int, threshold: float) -> bytes:
        return json.dumps({
            "query": query,
            "retrieval_setting": {
                "top_k": top_k,
                "score_threshold": threshold,
                "score_threshold_enabled": True,
            },
        }).encode("utf-8")

    # ── 响应解析 ──────────────────────────────────────────────

    @staticmethod
    def _parse_retrieve_records(data: dict) -> list[RetrievalResult]:
        return [
            RetrievalResult(
                content=r.get("content", "") or seg.get("content", ""),
                score=r.get("score", 0),
                title=r.get("title", "") or doc.get("name", ""),
                metadata=r.get("metadata", {}),
            )
            for r in data.get("records", [])
            for seg in [r.get("segment", {})]
            for doc in [seg.get("document", {})]
        ]

    @staticmethod
    def _parse_hit_testing_records(data: dict) -> list[RetrievalResult]:
        return [
            RetrievalResult(
                content=seg.get("content", ""),
                score=r.get("score", 0),
                title=doc.get("name", ""),
                metadata={
                    "document_id": doc.get("id", ""),
                    "segment_id": seg.get("id", ""),
                },
            )
            for r in data.get("records", [])
            for seg in [r.get("segment", {})]
            for doc in [seg.get("document", {})]
        ]