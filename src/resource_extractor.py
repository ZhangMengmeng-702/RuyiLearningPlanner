# -*- coding: utf-8 -*-
"""从文档内容中提取学习资源（视频、文档教程、在线练习）"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ExtractedResource:
    """提取出的学习资源"""
    title: str
    url: str
    type: str  # video, article, exercise, course, other
    description: str = ""
    source_doc: str = ""
    doc_id: str = ""


def extract_resources_from_content(content: str, source_doc: str = "", doc_id: str = "") -> List[ExtractedResource]:
    """从 Markdown 文档内容中提取学习资源

    识别以下格式的资源：
    - ## 学习资源 / ### 推荐视频 / ### 文档教程 / ### 在线练习 下的列表项
    - Markdown 链接：[标题](url)
    - 带 emoji 前缀：🎥 📖 💻 📚 等
    """
    resources: List[ExtractedResource] = []

    if not content:
        return resources

    # 找到 "学习资源" 章节及其后续内容
    resource_section_match = re.search(
        r'##\s*学习资源[^\n]*\n(.*?)(?=\n##\s|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )

    if resource_section_match:
        resource_content = resource_section_match.group(1)
    else:
        # 如果没有明确的学习资源章节，扫描整个文档中的链接
        resource_content = content

    # 按子章节分类提取
    sections = re.split(r'\n###\s+', resource_content)
    current_type = "other"

    for i, section in enumerate(sections):
        if i == 0:
            # 第一段可能包含子章节之前的内容
            pass
        else:
            # 判断子章节类型
            first_line = section.strip().split('\n')[0].lower()
            if '视频' in first_line or 'video' in first_line:
                current_type = "video"
            elif '文档' in first_line or '教程' in first_line or 'article' in first_line or 'doc' in first_line:
                current_type = "article"
            elif '练习' in first_line or '在线' in first_line or 'exercise' in first_line or 'practice' in first_line:
                current_type = "exercise"
            elif '课程' in first_line or 'course' in first_line:
                current_type = "course"
            else:
                current_type = "other"

        # 从 section 中提取所有 Markdown 链接
        links = re.findall(r'[-*]\s*(?:[\U0001F300-\U0001FAFF\u2600-\u27BF]\s*)?\[([^\]]+)\]\(([^)]+)\)([^\n]*)', section)

        for title, url, extra in links:
            # 跳过锚点链接和空链接
            if not url or url.startswith('#'):
                continue

            # 从 extra 行中提取描述
            description = ""
            extra = extra.strip()
            if extra:
                description = extra.lstrip(' -—:：')

            # 根据 URL 推断类型
            res_type = current_type
            if res_type == "other":
                if 'bilibili.com' in url or 'b23.tv' in url or 'youtube.com' in url or 'youtu.be' in url:
                    res_type = "video"
                elif 'runoob.com' in url or 'liaoxuefeng' in url or 'docs.python' in url:
                    res_type = "article"
                elif 'leetcode' in url or 'nowcoder' in url or 'pintia' in url:
                    res_type = "exercise"
                elif url.endswith('.pdf') or url.endswith('.md'):
                    res_type = "article"

            resources.append(ExtractedResource(
                title=title.strip(),
                url=url.strip(),
                type=res_type,
                description=description.strip(),
                source_doc=source_doc,
                doc_id=doc_id,
            ))

    # 如果上面的方法没找到，尝试全文搜索 Markdown 链接（在学习资源章节内）
    if not resources and resource_section_match:
        all_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', resource_content)
        for title, url in all_links:
            res_type = "other"
            if 'bilibili.com' in url or 'b23.tv' in url or 'youtube.com' in url:
                res_type = "video"
            elif 'leetcode' in url or 'nowcoder' in url:
                res_type = "exercise"
            else:
                res_type = "article"
            resources.append(ExtractedResource(
                title=title.strip(),
                url=url.strip(),
                type=res_type,
                description="",
                source_doc=source_doc,
                doc_id=doc_id,
            ))

    # 去重（按 URL）
    seen_urls = set()
    unique_resources = []
    for r in resources:
        if r.url not in seen_urls:
            seen_urls.add(r.url)
            unique_resources.append(r)

    return unique_resources


def extract_exercises_from_content(content: str, source_doc: str = "", doc_id: str = "") -> List[ExtractedResource]:
    """从文档内容中提取练习题资源

    识别 ## 练习题 / ### 练习题 章节下的内容
    """
    exercises: List[ExtractedResource] = []

    if not content:
        return exercises

    # 找到练习题章节
    exercise_section_match = re.search(
        r'##\s*练习题[^\n]*\n(.*?)(?=\n##\s|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )

    if not exercise_section_match:
        # 也试试 ### 练习题
        exercise_section_match = re.search(
            r'###\s*练习题[^\n]*\n(.*?)(?=\n###\s|\n##\s|\Z)',
            content, re.DOTALL | re.IGNORECASE
        )

    if not exercise_section_match:
        return exercises

    section_content = exercise_section_match.group(1)

    # 提取练习题链接
    links = re.findall(r'[-*]\s*(?:[\U0001F300-\U0001FAFF\u2600-\u27BF]\s*)?\[([^\]]+)\]\(([^)]+)\)([^\n]*)', section_content)

    if links:
        for title, url, extra in links:
            if not url or url.startswith('#'):
                continue
            description = extra.strip().lstrip(' -—:：')
            exercises.append(ExtractedResource(
                title=title.strip(),
                url=url.strip(),
                type="exercise",
                description=description,
                source_doc=source_doc,
                doc_id=doc_id,
            ))
    else:
        # 如果没有链接，用章节本身作为练习题
        first_line = section_content.strip().split('\n')[0]
        if first_line and len(first_line) < 100:
            exercises.append(ExtractedResource(
                title=source_doc or "练习题",
                url=f"/learn/kb/{doc_id}" if doc_id else "",
                type="exercise",
                description=first_line[:100],
                source_doc=source_doc,
                doc_id=doc_id,
            ))

    return exercises


def resource_to_dict(resource: ExtractedResource) -> Dict[str, Any]:
    """将资源对象转为字典"""
    return {
        "title": resource.title,
        "url": resource.url,
        "type": resource.type,
        "description": resource.description,
        "source_doc": resource.source_doc,
        "doc_id": resource.doc_id,
    }
