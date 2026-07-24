"""Dify KB 客户端测试（mock http.client 而非真实的 urllib）"""
import json, unittest
from unittest.mock import patch
from src.dify_client import DifyClient, RetrievalResult


class TestDifyClient(unittest.TestCase):

    @patch("http.client.HTTPConnection")
    def test_retrieve_returns_parsed_results(self, mock_conn):
        """mock http.client → 验证解析结果正确"""
        inst = mock_conn.return_value
        resp = inst.getresponse.return_value
        resp.status = 200
        resp.read.return_value = json.dumps({
            "records": [
                {"segment": {"content": "变量与数据类型",
                             "document": {"name": "01-基础语法.md", "id": "d1"}},
                 "score": 0.92},
                {"segment": {"content": "条件判断",
                             "document": {"name": "02-条件判断.md", "id": "d2"}},
                 "score": 0.85},
            ]
        }).encode("utf-8")

        client = DifyClient(base_url="http://localhost/v1", api_key="mock_key", kb_id="mock_kb")
        results = client.retrieve("Python 基础", top_k=2)

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], RetrievalResult)
        self.assertEqual(results[0].title, "01-基础语法.md")
        self.assertEqual(results[0].score, 0.92)
        self.assertEqual(results[1].title, "02-条件判断.md")
        self.assertIn("变量", results[0].content)

    def test_retrieve_formatted_returns_text(self):
        """无真实 API → 优雅返回提示文本而非抛异常"""
        client = DifyClient(base_url="http://0.0.0.0:1/v1", api_key="mock_key", kb_id="mock_kb")
        text = client.retrieve_formatted("Python 循环", top_k=1)
        self.assertIn("未检索到相关内容", text)

    def test_retrieve_empty_list_on_network_error(self):
        """网络不可达时返回空列表"""
        client = DifyClient(base_url="http://0.0.0.0:1/v1", api_key="x", kb_id="x")
        self.assertEqual(client.retrieve("test"), [])

    def test_retrieve_empty_list_when_no_kb_id(self):
        """无 kb_id 时返回空列表"""
        client = DifyClient(base_url="http://localhost/v1", api_key="x", kb_id="")
        self.assertEqual(client.retrieve("test"), [])

    def test_constructor_reads_key_and_id(self):
        """不传参时从 key.txt + .env 自动读取"""
        client = DifyClient()
        self.assertTrue(client.api_key.startswith("dataset-"))
        self.assertEqual(len(client.kb_id), 36)  # UUID 长度


if __name__ == "__main__":
    unittest.main()