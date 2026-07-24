# -*- coding: utf-8 -*-
"""
路径安全工具 — 防止路径遍历攻击
提供安全的路径拼接、验证和规范化函数
"""
import os
import re
from typing import Optional

# 允许的文件名字符：字母、数字、下划线、连字符、点
# 但不允许以点开头（隐藏文件）或包含路径分隔符
_SAFE_FILENAME_RE = re.compile(r'^[a-zA-Z0-9_-][a-zA-Z0-9._-]*$')

# 常见的 plan_id 格式：plan_YYYYMMDD_NNN 或 UUID 格式
_PLAN_ID_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$')

# user_id 格式
_USER_ID_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')

# session_id 格式
_SESSION_ID_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')

# doc_id 格式：category/filename，允许中文、字母、数字、下划线、连字符
_DOC_ID_RE = re.compile(r'^[a-zA-Z0-9_\u4e00-\u9fa5][a-zA-Z0-9._\-\u4e00-\u9fa5]*/[a-zA-Z0-9_\u4e00-\u9fa5][a-zA-Z0-9._\-\u4e00-\u9fa5]*$')


class PathSecurityError(ValueError):
    """路径安全错误"""
    pass


def safe_filename(filename: str, pattern: Optional[re.Pattern] = None) -> str:
    """
    验证文件名是否安全，返回安全的 basename
    
    Args:
        filename: 要验证的文件名
        pattern: 自定义验证正则，默认使用 _SAFE_FILENAME_RE
        
    Returns:
        安全的文件名（basename）
        
    Raises:
        PathSecurityError: 文件名不安全
    """
    if not filename:
        raise PathSecurityError("文件名不能为空")
    
    # 提前检查：不允许任何路径分隔符（在 basename 之前检查）
    if '/' in filename or '\\' in filename:
        raise PathSecurityError(f"文件名不能包含路径分隔符: {filename}")
    
    # 只取 basename，去除路径部分
    basename = os.path.basename(filename)
    
    if not basename or basename in ('.', '..'):
        raise PathSecurityError(f"非法文件名: {filename}")
    
    # 二次检查：basename 应该等于原始文件名（否则说明包含路径）
    if basename != filename:
        raise PathSecurityError(f"文件名不能包含路径: {filename}")
    
    # 检查是否包含路径分隔符
    if '/' in basename or '\\' in basename:
        raise PathSecurityError(f"文件名不能包含路径分隔符: {filename}")
    
    # 正则验证
    pat = pattern or _SAFE_FILENAME_RE
    if not pat.match(basename):
        raise PathSecurityError(f"文件名包含非法字符: {filename}")
    
    return basename


def safe_join(base_dir: str, *paths: str, pattern: Optional[re.Pattern] = None) -> str:
    """
    安全地拼接路径，确保最终路径在 base_dir 内
    
    Args:
        base_dir: 基础目录（必须是绝对路径）
        *paths: 要拼接的路径组件
        pattern: 文件名验证正则
        
    Returns:
        安全的完整路径
        
    Raises:
        PathSecurityError: 路径不安全
    """
    if not os.path.isabs(base_dir):
        raise PathSecurityError(f"base_dir 必须是绝对路径: {base_dir}")
    
    # 规范化 base_dir
    base_dir = os.path.realpath(base_dir)
    
    # 验证每个路径组件
    safe_paths = []
    for p in paths:
        # 对于多级路径，逐段验证
        parts = p.replace('\\', '/').split('/')
        for part in parts:
            if not part or part == '.':
                continue
            if part == '..':
                raise PathSecurityError(f"路径不能包含 '..': {p}")
            safe_paths.append(safe_filename(part, pattern))
    
    # 拼接并规范化
    full_path = os.path.realpath(os.path.join(base_dir, *safe_paths))
    
    # 验证最终路径在 base_dir 内
    if not full_path.startswith(base_dir + os.sep) and full_path != base_dir:
        raise PathSecurityError(f"路径越界: {full_path} 不在 {base_dir} 内")
    
    return full_path


def safe_plan_id(plan_id: str) -> str:
    """验证 plan_id 是否安全"""
    try:
        return safe_filename(plan_id, _PLAN_ID_RE)
    except PathSecurityError as e:
        raise PathSecurityError(f"无效的 plan_id: {e}")


def safe_user_id(user_id: str) -> str:
    """验证 user_id 是否安全"""
    try:
        return safe_filename(user_id, _USER_ID_RE)
    except PathSecurityError as e:
        raise PathSecurityError(f"无效的 user_id: {e}")


def safe_session_id(session_id: str) -> str:
    """验证 session_id 是否安全"""
    try:
        return safe_filename(session_id, _SESSION_ID_RE)
    except PathSecurityError as e:
        raise PathSecurityError(f"无效的 session_id: {e}")


def is_safe_plan_id(plan_id: str) -> bool:
    """检查 plan_id 是否安全（不抛异常）"""
    try:
        safe_plan_id(plan_id)
        return True
    except PathSecurityError:
        return False


def safe_doc_id(doc_id: str) -> str:
    """验证 doc_id 是否安全（格式：category/filename，允许中文）"""
    if not doc_id:
        raise PathSecurityError("doc_id 不能为空")
    # 禁止路径遍历
    if '..' in doc_id:
        raise PathSecurityError(f"doc_id 不能包含 '..': {doc_id}")
    # 禁止多个连续斜杠
    if '//' in doc_id:
        raise PathSecurityError(f"doc_id 不能包含连续斜杠: {doc_id}")
    # 正则验证
    if not _DOC_ID_RE.match(doc_id):
        raise PathSecurityError(f"无效的 doc_id 格式: {doc_id}")
    return doc_id
