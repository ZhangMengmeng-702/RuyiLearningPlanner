# -*- coding: utf-8 -*-
"""
知识库管理器

功能：
1. 加载本地 kb_docs 目录下的所有 Markdown 文档
2. 解析文档 front matter 和内容
3. 提取文档中的学习资源（视频、文档、在线练习等）
4. 支持按关键词检索文档
"""

import os
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional


_KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kb_docs")


@dataclass
class ResourceLink:
    title: str
    url: str
    type: str  # video / article / course / exercise / other
    description: str = ""


@dataclass
class KnowledgeDoc:
    doc_id: str
    title: str
    file_path: str
    category: str  # python_learning_path / exercises
    keywords: List[str] = field(default_factory=list)
    difficulty: int = 1
    estimated_hours: float = 0
    prerequisites: List[str] = field(default_factory=list)
    content: str = ""
    resources: List[ResourceLink] = field(default_factory=list)
    exercises: List[ResourceLink] = field(default_factory=list)


class KnowledgeBaseManager:
    _instance = None
    _docs: Dict[str, KnowledgeDoc] = {}
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_all(self):
        """加载所有知识库文档"""
        if self._loaded:
            return

        kb_dir = os.path.abspath(_KB_DIR)
        if not os.path.exists(kb_dir):
            print(f"[KnowledgeBaseManager] 知识库目录不存在: {kb_dir}")
            return

        categories = ["python_learning_path", "exercises"]
        for category in categories:
            cat_dir = os.path.join(kb_dir, category)
            if not os.path.exists(cat_dir):
                continue
            for filename in os.listdir(cat_dir):
                if not filename.endswith(".md"):
                    continue
                file_path = os.path.join(cat_dir, filename)
                doc = self._parse_doc(file_path, category, filename)
                if doc:
                    self._docs[doc.doc_id] = doc

        self._loaded = True
        print(f"[KnowledgeBaseManager] 已加载 {len(self._docs)} 个文档")

    def _parse_doc(self, file_path: str, category: str, filename: str) -> Optional[KnowledgeDoc]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            doc_id = f"{category}/{filename.replace('.md', '')}"

            # 解析 front matter
            front_matter = {}
            body = content
            if content.startswith("---"):
                end_idx = content.find("---", 3)
                if end_idx > 0:
                    fm_text = content[3:end_idx].strip()
                    body = content[end_idx + 3:].strip()
                    for line in fm_text.split("\n"):
                        if ":" in line:
                            key, val = line.split(":", 1)
                            key = key.strip()
                            val = val.strip()
                            if key == "keywords":
                                front_matter[key] = [k.strip() for k in val.split(",") if k.strip()]
                            elif key == "difficulty":
                                front_matter[key] = int(val) if val.isdigit() else 1
                            elif key == "estimated_hours":
                                front_matter[key] = float(val) if val else 0
                            elif key == "prerequisites":
                                front_matter[key] = [p.strip() for p in val.split(",") if p.strip()]
                            else:
                                front_matter[key] = val

            # 提取学习资源链接
            resources = self._extract_resources(body)

            # 提取练习题
            exercises = []
            if category == "exercises":
                exercises.append(ResourceLink(
                    title=front_matter.get("title", filename.replace(".md", "")),
                    url="",
                    type="exercise",
                    description=f"来自文档: {filename}",
                ))

            return KnowledgeDoc(
                doc_id=doc_id,
                title=front_matter.get("title", filename.replace(".md", "")),
                file_path=file_path,
                category=category,
                keywords=front_matter.get("keywords", []),
                difficulty=front_matter.get("difficulty", 1),
                estimated_hours=front_matter.get("estimated_hours", 0),
                prerequisites=front_matter.get("prerequisites", []),
                content=body,
                resources=resources,
                exercises=exercises,
            )
        except Exception as e:
            print(f"[KnowledgeBaseManager] 解析文档失败 {filename}: {e}")
            return None

    def _extract_resources(self, content: str) -> List[ResourceLink]:
        """从文档内容中提取学习资源链接"""
        resources = []
        current_section = None

        # 找到"学习资源"部分
        resource_section_match = re.search(r'##\s*学习资源\s*\n(.*?)(?=\n##\s|\Z)', content, re.DOTALL)
        if not resource_section_match:
            return resources

        section_content = resource_section_match.group(1)

        # 按子标题分类
        subsections = re.split(r'###\s*', section_content)
        for sub in subsections:
            sub = sub.strip()
            if not sub:
                continue

            lines = sub.split("\n")
            subtitle = lines[0].strip() if lines else ""
            body_lines = lines[1:] if len(lines) > 1 else []

            res_type = "other"
            if "视频" in subtitle:
                res_type = "video"
            elif "文档" in subtitle or "教程" in subtitle:
                res_type = "article"
            elif "在线练习" in subtitle or "练习" in subtitle:
                res_type = "exercise"
            elif "课程" in subtitle:
                res_type = "course"

            # 提取每个链接
            i = 0
            while i < len(body_lines):
                line = body_lines[i].strip()
                # 匹配 Markdown 链接: - 🎥 [标题](url)
                link_match = re.match(r'-\s*[^\s]*\s*\[([^\]]+)\]\(([^)]+)\)', line)
                if link_match:
                    title = link_match.group(1).strip()
                    url = link_match.group(2).strip()
                    desc = ""
                    # 下一行如果是缩进的描述
                    if i + 1 < len(body_lines) and body_lines[i + 1].strip().startswith("- "):
                        desc = body_lines[i + 1].strip()[2:].strip()
                        i += 1
                    elif i + 1 < len(body_lines) and body_lines[i + 1].strip().startswith("  - "):
                        desc = body_lines[i + 1].strip()[4:].strip()
                        i += 1
                    resources.append(ResourceLink(
                        title=title,
                        url=url,
                        type=res_type,
                        description=desc,
                    ))
                i += 1

        return resources

    def search(self, query: str, top_k: int = 10) -> List[KnowledgeDoc]:
        """按关键词检索文档"""
        self.load_all()
        if not self._docs:
            return []

        query_lower = query.lower()
        query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', query_lower))

        scored = []
        for doc in self._docs.values():
            score = 0.0

            # 标题匹配
            if query_lower in doc.title.lower():
                score += 5.0

            # 关键词匹配
            for kw in doc.keywords:
                if kw.lower() in query_lower or any(qw in kw.lower() for qw in query_words):
                    score += 3.0

            # 内容匹配
            content_lower = doc.content.lower()
            match_count = 0
            for qw in query_words:
                if len(qw) >= 2:
                    count = content_lower.count(qw)
                    if count > 0:
                        score += min(count * 0.5, 3.0)
                        match_count += 1

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    def get_doc(self, doc_id: str) -> Optional[KnowledgeDoc]:
        """根据 ID 获取文档"""
        self.load_all()
        return self._docs.get(doc_id)

    def get_all_docs(self) -> Dict[str, KnowledgeDoc]:
        """获取所有文档"""
        self.load_all()
        return self._docs


# 单例
kb_manager = KnowledgeBaseManager()
