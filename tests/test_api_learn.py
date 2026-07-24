"""
Hermes 学习助手 API 端点测试

测试覆盖：
- 健康检查接口
- 学习对话接口（SSE）
- 会话管理接口
- 用户画像接口
- 学习进度接口

注意：运行前请确保后端服务已启动，或使用 TestClient（FastAPI）。
"""

import pytest
import json
import time


# ============================================================
# 配置
# ============================================================

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_ID = "test_user_001"


# ============================================================
# 辅助函数
# ============================================================

def _is_2xx(status_code: int) -> bool:
    """判断是否为 2xx 状态码"""
    return 200 <= status_code < 300


def _parse_sse_response(response_text: str) -> list:
    """解析 SSE 响应，返回事件列表
    
    每个事件是一个字典：{"event": str, "data": dict}
    """
    events = []
    current_event = "message"
    lines = response_text.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:"):
            data_str = line[5:].strip()
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                data = {"raw": data_str}
            events.append({
                "event": current_event,
                "data": data
            })
            current_event = "message"
    
    return events


# ============================================================
# 1. 健康检查
# ============================================================

class TestHealth:
    
    def test_health_check(self, api_client):
        """测试健康检查端点"""
        response = api_client.get("/health")
        assert _is_2xx(response.status_code)
        
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "healthy"
        assert "version" in body["data"]
        assert "components" in body["data"]


# ============================================================
# 2. 用户画像接口
# ============================================================

class TestProfile:
    
    def test_get_profile_not_exists(self, api_client):
        """获取不存在的用户画像"""
        response = api_client.get(f"/profile?user_id=nonexistent_{int(time.time())}")
        # 允许返回 404 或返回空对象
        assert response.status_code in (200, 404)
    
    def test_create_and_update_profile(self, api_client):
        """创建并更新用户画像"""
        user_id = f"test_profile_{int(time.time())}"
        
        # 1. 先创建（PUT）
        profile_data = {
            "user_id": user_id,
            "name": "测试用户",
            "age": 20,
            "level": "beginner",
            "learning_goal": "测试学习目标",
            "available_hours_per_week": 10,
            "preferred_learning_style": "project-based",
            "strengths": ["逻辑思维"],
            "weaknesses": ["动手能力"],
            "interests": ["Python"]
        }
        
        response = api_client.put("/profile", json=profile_data)
        assert _is_2xx(response.status_code)
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "测试用户"
        
        # 2. 读取验证
        response = api_client.get(f"/profile?user_id={user_id}")
        assert _is_2xx(response.status_code)
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["level"] == "beginner"
        assert len(body["data"]["strengths"]) == 1
        
        # 3. 更新部分字段
        update_data = {
            "user_id": user_id,
            "level": "intermediate",
            "age": 21
        }
        response = api_client.put("/profile", json=update_data)
        assert _is_2xx(response.status_code)
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["level"] == "intermediate"
        assert body["data"]["age"] == 21
        assert body["data"]["name"] == "测试用户"  # 旧字段保留
    
    def test_profile_missing_user_id(self, api_client):
        """缺少 user_id 参数的错误情况"""
        response = api_client.get("/profile")
        assert response.status_code in (400, 422)


# ============================================================
# 3. 学习对话接口
# ============================================================

class TestLearnChat:
    
    def test_chat_new_session(self, api_client):
        """测试新建会话的对话"""
        payload = {
            "user_id": TEST_USER_ID,
            "message": "你好"
        }
        
        response = api_client.post("/learn/chat", json=payload)
        assert _is_2xx(response.status_code)
        
        # 检查 Content-Type 是 SSE
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_chat_with_history(self, api_client):
        """测试带历史消息的对话"""
        payload = {
            "user_id": TEST_USER_ID,
            "session_id": "test_session_001",
            "message": "再讲一下变量",
            "history": [
                {"role": "user", "content": "什么是变量？"},
                {"role": "assistant", "content": "变量是存储数据的容器..."}
            ]
        }
        
        response = api_client.post("/learn/chat", json=payload)
        assert _is_2xx(response.status_code)
    
    def test_chat_sse_streaming(self, api_client):
        """测试 SSE 流式响应格式"""
        payload = {
            "user_id": TEST_USER_ID,
            "message": "讲一个简单的Python例子"
        }
        
        response = api_client.post("/learn/chat", json=payload)
        assert _is_2xx(response.status_code)
        
        events = _parse_sse_response(response.text)
        assert len(events) > 0
        
        # 应该有 done 事件
        event_types = [e["event"] for e in events]
        assert "done" in event_types
        
        # done 事件应该包含完整内容
        done_event = next(e for e in events if e["event"] == "done")
        assert "full_content" in done_event["data"]
        assert "session_id" in done_event["data"]
    
    def test_chat_empty_message(self, api_client):
        """空消息的错误处理"""
        payload = {
            "user_id": TEST_USER_ID,
            "message": ""
        }
        
        response = api_client.post("/learn/chat", json=payload)
        # 应该返回错误，不能崩溃
        assert response.status_code in (400, 422)
    
    def test_chat_missing_user_id(self, api_client):
        """缺少 user_id 的错误情况"""
        payload = {
            "message": "你好"
        }
        
        response = api_client.post("/learn/chat", json=payload)
        assert response.status_code in (400, 422)


# ============================================================
# 4. 会话管理接口
# ============================================================

class TestSessions:
    
    def test_list_sessions(self, api_client):
        """测试获取会话列表"""
        response = api_client.get(f"/learn/sessions?user_id={TEST_USER_ID}")
        assert _is_2xx(response.status_code)
        
        body = response.json()
        assert body["code"] == 0
        assert "sessions" in body["data"]
        assert "total" in body["data"]
        assert isinstance(body["data"]["sessions"], list)
    
    def test_list_sessions_pagination(self, api_client):
        """测试分页参数"""
        response = api_client.get(
            f"/learn/sessions?user_id={TEST_USER_ID}&limit=5&offset=0"
        )
        assert _is_2xx(response.status_code)
        
        body = response.json()
        assert body["code"] == 0
        assert len(body["data"]["sessions"]) <= 5
    
    def test_get_session_detail(self, api_client, test_session_id):
        """测试获取单个会话详情"""
        response = api_client.get(f"/learn/sessions/{test_session_id}")
        # 可能存在也可能不存在，只要不 500 就行
        assert response.status_code in (200, 404)
        
        if response.status_code == 200:
            body = response.json()
            assert body["code"] == 0
            assert "messages" in body["data"]
    
    def test_delete_session(self, api_client):
        """测试删除会话"""
        # 先发起一次对话创建会话
        payload = {
            "user_id": f"delete_test_{int(time.time())}",
            "message": "这是一个用于测试删除的会话"
        }
        response = api_client.post("/learn/chat", json=payload)
        
        # 从响应中提取 session_id
        events = _parse_sse_response(response.text)
        done_event = next((e for e in events if e["event"] == "done"), None)
        
        if done_event and "session_id" in done_event["data"]:
            session_id = done_event["data"]["session_id"]
            
            # 删除
            del_response = api_client.delete(f"/learn/sessions/{session_id}")
            assert _is_2xx(del_response.status_code)
            
            # 再次获取应该 404
            get_response = api_client.get(f"/learn/sessions/{session_id}")
            assert get_response.status_code == 404
    
    def test_list_sessions_missing_user_id(self, api_client):
        """缺少 user_id 的错误情况"""
        response = api_client.get("/learn/sessions")
        assert response.status_code in (400, 422)


# ============================================================
# 5. 学习进度接口
# ============================================================

class TestProgress:
    
    def test_get_overall_progress(self, api_client):
        """测试获取总体学习进度"""
        response = api_client.get(f"/progress?user_id={TEST_USER_ID}")
        assert _is_2xx(response.status_code)
        
        body = response.json()
        assert body["code"] == 0
        data = body["data"]
        
        # 检查关键字段是否存在
        assert "overall_progress" in data
        assert "total_chapters" in data
        assert "completed_chapters" in data
        assert "total_study_hours" in data
        
        # 进度应该在 0~1 之间
        assert 0 <= data["overall_progress"] <= 1
    
    def test_get_chapters_progress(self, api_client):
        """测试获取章节进度列表"""
        response = api_client.get(f"/progress/chapters?user_id={TEST_USER_ID}")
        assert _is_2xx(response.status_code)
        
        body = response.json()
        assert body["code"] == 0
        assert "chapters" in body["data"]
        assert isinstance(body["data"]["chapters"], list)
        
        # 检查每章的字段
        if body["data"]["chapters"]:
            chapter = body["data"]["chapters"][0]
            assert "chapter_id" in chapter
            assert "title" in chapter
            assert "status" in chapter
            assert chapter["status"] in ("not_started", "in_progress", "completed")
    
    def test_get_single_chapter_progress(self, api_client):
        """测试获取单章进度详情"""
        chapter_id = 1
        response = api_client.get(
            f"/progress/chapters/{chapter_id}?user_id={TEST_USER_ID}"
        )
        assert _is_2xx(response.status_code)
        
        body = response.json()
        assert body["code"] == 0
        data = body["data"]
        
        assert "chapter_id" in data
        assert data["chapter_id"] == chapter_id
        assert "status" in data
        assert "progress" in data
    
    def test_progress_missing_user_id(self, api_client):
        """缺少 user_id 的错误情况"""
        response = api_client.get("/progress")
        assert response.status_code in (400, 422)
        
        response = api_client.get("/progress/chapters")
        assert response.status_code in (400, 422)


# ============================================================
# 6. 集成测试：完整对话流程
# ============================================================

class TestIntegrationFlow:
    
    def test_full_learning_flow(self, api_client):
        """完整的学习流程集成测试
        
        流程：
        1. 创建用户画像
        2. 发起首次对话（获取学习计划）
        3. 检查学习进度
        4. 继续对话（询问具体问题）
        5. 查看会话列表
        """
        user_id = f"integration_test_{int(time.time())}"
        
        # 1. 创建用户画像
        profile_data = {
            "user_id": user_id,
            "level": "beginner",
            "learning_goal": "零基础入门Python",
            "available_hours_per_week": 5
        }
        response = api_client.put("/profile", json=profile_data)
        assert _is_2xx(response.status_code)
        
        # 2. 发起首次对话
        chat_payload = {
            "user_id": user_id,
            "message": "我是零基础，帮我制定一个Python学习计划"
        }
        response = api_client.post("/learn/chat", json=chat_payload)
        assert _is_2xx(response.status_code)
        
        events = _parse_sse_response(response.text)
        done_event = next((e for e in events if e["event"] == "done"), None)
        assert done_event is not None
        session_id = done_event["data"]["session_id"]
        assert session_id
        
        # 3. 检查学习进度
        response = api_client.get(f"/progress?user_id={user_id}")
        assert _is_2xx(response.status_code)
        body = response.json()
        assert body["code"] == 0
        
        # 4. 继续对话（同一会话）
        chat_payload2 = {
            "user_id": user_id,
            "session_id": session_id,
            "message": "第一章学什么？"
        }
        response = api_client.post("/learn/chat", json=chat_payload2)
        assert _is_2xx(response.status_code)
        
        # 5. 查看会话列表
        response = api_client.get(f"/learn/sessions?user_id={user_id}")
        assert _is_2xx(response.status_code)
        body = response.json()
        assert body["data"]["total"] >= 1


# ============================================================
# 7. SSE 事件解析测试
# ============================================================

class TestSSEEventParsing:
    """测试 SSE 事件解析，验证 10 种事件类型都能正确解析"""

    def test_parse_session_created_event(self):
        """测试解析 session_created 事件"""
        sse_text = 'data: {"event":"session_created","data":{"session_id":"sess_123"}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["event"] == "message"
        assert events[0]["data"]["event"] == "session_created"
        assert events[0]["data"]["data"]["session_id"] == "sess_123"

    def test_parse_token_event(self):
        """测试解析 token 事件"""
        sse_text = 'data: {"event":"token","data":{"message":"正在分析..."}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["data"]["event"] == "token"
        assert "message" in events[0]["data"]["data"]

    def test_parse_profile_event(self):
        """测试解析 profile 事件"""
        sse_text = 'data: {"event":"profile","data":{"success":true,"profile":{"goal":"学习Python"}}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["data"]["event"] == "profile"
        assert events[0]["data"]["data"]["success"] is True
        assert events[0]["data"]["data"]["profile"]["goal"] == "学习Python"

    def test_parse_knowledge_event(self):
        """测试解析 knowledge 事件"""
        sse_text = 'data: {"event":"knowledge","data":{"success":true,"results":[],"count":0}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["data"]["event"] == "knowledge"
        assert events[0]["data"]["data"]["success"] is True
        assert isinstance(events[0]["data"]["data"]["results"], list)
        assert isinstance(events[0]["data"]["data"]["count"], int)

    def test_parse_prerequisite_event(self):
        """测试解析 prerequisite 事件"""
        sse_text = 'data: {"event":"prerequisite","data":{"status":"passed","details":[],"warnings":[]}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["data"]["event"] == "prerequisite"
        assert events[0]["data"]["data"]["status"] in ("passed", "warning", "failed")

    def test_parse_evaluation_event(self):
        """测试解析 evaluation 事件"""
        sse_text = 'data: {"event":"evaluation","data":{"score":8,"issues":[],"suggestions":["建议增加实践"]}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["data"]["event"] == "evaluation"
        assert isinstance(events[0]["data"]["data"]["score"], int)
        assert isinstance(events[0]["data"]["data"]["issues"], list)
        assert isinstance(events[0]["data"]["data"]["suggestions"], list)

    def test_parse_schedule_event(self):
        """测试解析 schedule 事件"""
        sse_text = 'data: {"event":"schedule","data":{"success":true,"output_path":"data/plans/test.ics"}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["data"]["event"] == "schedule"
        assert events[0]["data"]["data"]["success"] is True
        assert "output_path" in events[0]["data"]["data"]

    def test_parse_plan_event(self):
        """测试解析 plan 事件"""
        sse_text = 'data: {"event":"plan","data":{"plan_id":"plan_123","goal":"学习Python","total_weeks":4}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["data"]["event"] == "plan"
        assert "plan_id" in events[0]["data"]["data"]
        assert "goal" in events[0]["data"]["data"]

    def test_parse_done_event(self):
        """测试解析 done 事件"""
        sse_text = 'data: {"event":"done","data":{"plan_id":"plan_123","ics_path":"/api/v1/learn/plan/plan_123/ics"}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["data"]["event"] == "done"
        assert "plan_id" in events[0]["data"]["data"]
        assert "ics_path" in events[0]["data"]["data"]

    def test_parse_error_event(self):
        """测试解析 error 事件"""
        sse_text = 'data: {"event":"error","data":{"message":"测试错误信息"}}\n\n'
        events = _parse_sse_response(sse_text)
        assert len(events) == 1
        assert events[0]["data"]["event"] == "error"
        assert "message" in events[0]["data"]["data"]

    def test_parse_all_ten_events(self):
        """测试一次性解析全部 10 种事件类型"""
        all_events_sse = """
data: {"event":"session_created","data":{"session_id":"sess_123"}}

data: {"event":"token","data":{"message":"正在检查用户画像..."}}

data: {"event":"profile","data":{"success":true,"profile":{}}}

data: {"event":"knowledge","data":{"success":true,"results":[],"count":0}}

data: {"event":"prerequisite","data":{"status":"passed","details":[],"warnings":[]}}

data: {"event":"evaluation","data":{"score":8,"issues":[],"suggestions":[]}}

data: {"event":"schedule","data":{"success":true,"output_path":"test.ics"}}

data: {"event":"plan","data":{"plan_id":"plan_123","goal":"test"}}

data: {"event":"done","data":{"plan_id":"plan_123","ics_path":"test.ics"}}

data: {"event":"error","data":{"message":"test error"}}
"""
        events = _parse_sse_response(all_events_sse)
        assert len(events) == 10
        event_types = [e["data"]["event"] for e in events]
        expected_events = [
            "session_created", "token", "profile", "knowledge",
            "prerequisite", "evaluation", "schedule", "plan",
            "done", "error"
        ]
        for expected in expected_events:
            assert expected in event_types, f"缺少事件类型: {expected}"


# ============================================================
# 8. 新端点测试（待实现端点，标记为预期失败）
# ============================================================

class TestNewEndpoints:
    """测试新增的端点（待实现的端点标记为 expectedFailure 或 skip）"""

    @pytest.mark.skip(reason="端点待实现: POST /learn/chat/stream")
    def test_chat_stream_endpoint(self, api_client):
        """测试直接流式 LLM 对话端点"""
        payload = {
            "user_id": TEST_USER_ID,
            "message": "你好"
        }
        response = api_client.post("/learn/chat/stream", json=payload)
        assert _is_2xx(response.status_code)
        assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.skip(reason="端点待实现: POST /learn/chat/hermes")
    def test_chat_hermes_endpoint(self, api_client):
        """测试直接调用 Hermes Agent 端点"""
        payload = {
            "user_id": TEST_USER_ID,
            "message": "你好"
        }
        response = api_client.post("/learn/chat/hermes", json=payload)
        assert _is_2xx(response.status_code)
        assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.skip(reason="端点待实现: GET /learn/plan/{plan_id}/ics")
    def test_plan_ics_export(self, api_client):
        """测试 ICS 日历导出端点"""
        plan_id = "test_plan_001"
        response = api_client.get(f"/learn/plan/{plan_id}/ics")
        assert _is_2xx(response.status_code)
        assert "text/calendar" in response.headers.get("content-type", "")
        assert "BEGIN:VCALENDAR" in response.text

    @pytest.mark.skip(reason="端点待实现: GET /learn/session/{session_id}")
    def test_get_session_info(self, api_client):
        """测试获取会话信息端点"""
        session_id = "test_session_001"
        response = api_client.get(f"/learn/session/{session_id}")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            body = response.json()
            assert "session_id" in body
            assert "user_id" in body
            assert "created_at" in body

    @pytest.mark.skip(reason="端点待实现: GET /learn/session/{session_id}/messages")
    def test_get_session_messages(self, api_client):
        """测试获取会话消息历史端点"""
        session_id = "test_session_001"
        response = api_client.get(f"/learn/session/{session_id}/messages?limit=10&offset=0")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            body = response.json()
            assert "session_id" in body
            assert "messages" in body
            assert "total" in body
            assert isinstance(body["messages"], list)

    @pytest.mark.skip(reason="端点待实现: DELETE /learn/session/{session_id}")
    def test_delete_session(self, api_client):
        """测试删除会话端点"""
        session_id = "test_session_delete"
        response = api_client.delete(f"/learn/session/{session_id}")
        assert _is_2xx(response.status_code)
        body = response.json()
        assert body["status"] == "deleted"

    @pytest.mark.skip(reason="端点待实现: POST /learn/cleanup")
    def test_cleanup_sessions(self, api_client):
        """测试清理过期会话端点"""
        response = api_client.post("/learn/cleanup")
        assert _is_2xx(response.status_code)
        body = response.json()
        assert "status" in body
        assert "cleaned_count" in body
        assert isinstance(body["cleaned_count"], int)


# ============================================================
# 9. ICS 日历导出测试
# ============================================================

class TestICSExport:
    """测试 ICS 日历导出功能"""

    @pytest.mark.skip(reason="ICS 导出功能待实现")
    def test_ics_file_format(self, api_client):
        """测试 ICS 文件格式是否正确"""
        plan_id = "test_plan_ics"
        response = api_client.get(f"/learn/plan/{plan_id}/ics")
        assert _is_2xx(response.status_code)
        
        content = response.text
        # 验证 ICS 基本格式
        assert content.startswith("BEGIN:VCALENDAR")
        assert content.strip().endswith("END:VCALENDAR")
        assert "VERSION:2.0" in content
        assert "PRODID:" in content

    @pytest.mark.skip(reason="ICS 导出功能待实现")
    def test_ics_contains_events(self, api_client):
        """测试 ICS 文件包含日历事件"""
        plan_id = "test_plan_ics"
        response = api_client.get(f"/learn/plan/{plan_id}/ics")
        assert _is_2xx(response.status_code)
        
        content = response.text
        # 验证包含 VEVENT
        assert "BEGIN:VEVENT" in content
        assert "END:VEVENT" in content
        assert "SUMMARY:" in content
        assert "DTSTART:" in content
        assert "DTEND:" in content

    @pytest.mark.skip(reason="ICS 导出功能待实现")
    def test_ics_content_disposition(self, api_client):
        """测试 ICS 响应的 Content-Disposition 头"""
        plan_id = "test_plan_ics"
        response = api_client.get(f"/learn/plan/{plan_id}/ics")
        assert _is_2xx(response.status_code)
        
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert ".ics" in content_disposition


# ============================================================
# 10. 会话管理测试（新架构）
# ============================================================

class TestSessionManagement:
    """会话管理相关测试（基于新架构的会话 API）"""

    @pytest.mark.skip(reason="端点待实现: GET /learn/session/{session_id}")
    def test_get_session_not_found(self, api_client):
        """测试获取不存在的会话返回 404"""
        session_id = f"nonexistent_{int(time.time())}"
        response = api_client.get(f"/learn/session/{session_id}")
        assert response.status_code == 404

    @pytest.mark.skip(reason="端点待实现: GET /learn/session/{session_id}/messages")
    def test_get_session_messages_pagination(self, api_client):
        """测试会话消息分页"""
        session_id = "test_session_pagination"
        # 测试 limit 参数
        response = api_client.get(f"/learn/session/{session_id}/messages?limit=5")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            body = response.json()
            assert len(body["messages"]) <= 5

        # 测试 offset 参数
        response = api_client.get(f"/learn/session/{session_id}/messages?limit=5&offset=5")
        assert response.status_code in (200, 404)

    @pytest.mark.skip(reason="端点待实现: DELETE /learn/session/{session_id}")
    def test_delete_nonexistent_session(self, api_client):
        """测试删除不存在的会话"""
        session_id = f"nonexistent_delete_{int(time.time())}"
        response = api_client.delete(f"/learn/session/{session_id}")
        # 允许 200（幂等）或 404
        assert response.status_code in (200, 404)

    @pytest.mark.skip(reason="端点待实现: POST /learn/cleanup")
    def test_cleanup_returns_count(self, api_client):
        """测试清理接口返回清理数量"""
        response = api_client.post("/learn/cleanup")
        assert _is_2xx(response.status_code)
        body = response.json()
        assert body["status"] == "ok"
        assert isinstance(body["cleaned_count"], int)
        assert body["cleaned_count"] >= 0

    @pytest.mark.skip(reason="完整会话流程待实现")
    def test_full_session_lifecycle(self, api_client):
        """测试完整的会话生命周期：创建 → 获取消息 → 删除"""
        user_id = f"lifecycle_test_{int(time.time())}"
        
        # 1. 创建会话（通过对话）
        payload = {"user_id": user_id, "message": "你好"}
        response = api_client.post("/learn/chat", json=payload)
        assert _is_2xx(response.status_code)
        
        events = _parse_sse_response(response.text)
        done_event = next((e for e in events if e["data"].get("event") == "done"), None)
        session_id = done_event["data"]["data"].get("session_id") if done_event else None
        assert session_id, "未能从响应中获取 session_id"
        
        # 2. 获取会话信息
        response = api_client.get(f"/learn/session/{session_id}")
        assert _is_2xx(response.status_code)
        body = response.json()
        assert body["session_id"] == session_id
        assert body["user_id"] == user_id
        
        # 3. 获取会话消息
        response = api_client.get(f"/learn/session/{session_id}/messages")
        assert _is_2xx(response.status_code)
        body = response.json()
        assert len(body["messages"]) > 0
        
        # 4. 删除会话
        response = api_client.delete(f"/learn/session/{session_id}")
        assert _is_2xx(response.status_code)
        
        # 5. 验证已删除
        response = api_client.get(f"/learn/session/{session_id}")
        assert response.status_code == 404


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="session")
def api_client():
    """创建 API 客户端
    
    如果项目使用 FastAPI 且有 app 实例，用 TestClient；
    否则用 requests 调真实服务。
    """
    try:
        # 尝试用 FastAPI TestClient
        from fastapi.testclient import TestClient
        import sys
        import os
        
        # 尝试导入 app
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from main import app  # 假设主入口是 main.py
        
        client = TestClient(app)
        yield client
        
    except ImportError:
        # 回退到 requests 调用真实服务
        import requests
        
        class RequestsClient:
            """封装 requests，接口类似 TestClient"""
            def __init__(self, base_url):
                self.base_url = base_url
                self.session = requests.Session()
            
            def get(self, url, **kwargs):
                return self.session.get(self.base_url + url, **kwargs)
            
            def put(self, url, json=None, **kwargs):
                return self.session.put(self.base_url + url, json=json, **kwargs)
            
            def post(self, url, json=None, **kwargs):
                return self.session.post(self.base_url + url, json=json, **kwargs)
            
            def delete(self, url, **kwargs):
                return self.session.delete(self.base_url + url, **kwargs)
        
        client = RequestsClient(BASE_URL)
        yield client


@pytest.fixture
def test_session_id(api_client):
    """创建一个测试会话并返回 session_id"""
    payload = {
        "user_id": f"fixture_test_{int(time.time())}",
        "message": "测试消息"
    }
    response = api_client.post("/learn/chat", json=payload)
    
    if _is_2xx(response.status_code):
        events = _parse_sse_response(response.text)
        done_event = next((e for e in events if e["event"] == "done"), None)
        if done_event:
            return done_event["data"].get("session_id", "test_session")
    
    return "test_session"


# ============================================================
# 主入口：直接运行
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Hermes Learning Assistant — API 端点测试")
    print("=" * 60)
    print()
    print("使用方法：")
    print("  pytest tests/test_api_learn.py -v")
    print()
    print("或者指定标记运行：")
    print("  pytest tests/test_api_learn.py -v -k health")
    print("  pytest tests/test_api_learn.py -v -k chat")
    print("  pytest tests/test_api_learn.py -v -k profile")
    print("  pytest tests/test_api_learn.py -v -k progress")
    print("  pytest tests/test_api_learn.py -v -k integration")
