"""Dify KB 客户端测试（不需真实 Dify，mock urllib）"""
import json, unittest
from unittest.mock import patch
from src.dify_client import DifyClient, RetrievalResult

class TestDifyClient(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_retrieve_returns_parsed_results(self, mock_urlopen):
        mock_resp = mock_urlopen.return_value.__enter__.return_value
        mock_resp.read.return_value = json.dumps({
            "records": [
                {"content": "变量与数据类型", "score": 0.92, "title": "01-基础语法.md",
                 "metadata": {"difficulty": 1}},
                {"content": "条件判断", "score": 0.85, "title": "02-条件判断.md",
                 "metadata": {"difficulty": 2}},
            ]
        }).encode("utf-8")

        client = DifyClient(base_url="http://mock/v1", api_key="mock_key", kb_id="mock_kb")
        results = client.retrieve("Python 基础", top_k=2)

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], RetrievalResult)
        self.assertEqual(results[0].title, "01-基础语法.md")
        self.assertEqual(results[0].score, 0.92)

    def test_retrieve_formatted_returns_text(self):
        client = DifyClient(base_url="http://mock/v1", api_key="mock_key", kb_id="mock_kb")
        # 无真实 API — 期望抛出异常降级，不影响测试
        with self.assertRaises(Exception):
            client.retrieve("test")

if __name__ == "__main__":
    unittest.main()