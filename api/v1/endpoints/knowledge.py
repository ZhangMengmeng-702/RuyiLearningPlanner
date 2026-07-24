# -*- coding: utf-8 -*-
"""知识库 API — 文档列表、详情、搜索"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.knowledge_base_manager import kb_manager
from src.utils.path_security import safe_doc_id, PathSecurityError

router = APIRouter()


@router.get("/list")
def list_docs(category: str = ""):
    """获取文档列表"""
    kb_manager.load_all()
    docs = kb_manager.get_all_docs()

    result = []
    for doc_id, doc in docs.items():
        if category and doc.category != category:
            continue
        result.append({
            "doc_id": doc.doc_id,
            "title": doc.title,
            "category": doc.category,
            "keywords": doc.keywords,
            "difficulty": doc.difficulty,
            "estimated_hours": doc.estimated_hours,
            "resource_count": len(doc.resources),
        })

    return {"success": True, "docs": result, "count": len(result)}


@router.get("/search")
def search_docs(query: str, top_k: int = 10):
    """搜索文档"""
    results = kb_manager.search(query, top_k=top_k)

    docs = []
    for doc in results:
        docs.append({
            "doc_id": doc.doc_id,
            "title": doc.title,
            "category": doc.category,
            "keywords": doc.keywords,
            "difficulty": doc.difficulty,
            "estimated_hours": doc.estimated_hours,
            "resource_count": len(doc.resources),
            "resources": [
                {"title": r.title, "url": r.url, "type": r.type, "description": r.description}
                for r in doc.resources
            ],
        })

    return {"success": True, "docs": docs, "count": len(docs)}


@router.get("/doc/{doc_id:path}")
def get_doc(doc_id: str):
    """获取文档详情"""
    try:
        safe_id = safe_doc_id(doc_id)
    except PathSecurityError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"无效的文档ID: {e}"}
        )
    doc = kb_manager.get_doc(safe_id)
    if not doc:
        return {"success": False, "message": "文档不存在"}

    return {
        "success": True,
        "doc": {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "category": doc.category,
            "keywords": doc.keywords,
            "difficulty": doc.difficulty,
            "estimated_hours": doc.estimated_hours,
            "prerequisites": doc.prerequisites,
            "content": doc.content,
            "resources": [
                {"title": r.title, "url": r.url, "type": r.type, "description": r.description}
                for r in doc.resources
            ],
        },
    }
