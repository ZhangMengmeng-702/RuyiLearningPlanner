# -*- coding: utf-8 -*-
"""知识库检索验证脚本

C 上传完文档后，运行此脚本检查检索是否能命中正确章节。

用法:
    python tests/test_kb_retrieval.py
    或指定 KB_ID: python tests/test_kb_retrieval.py 你的知识库ID
"""
import sys, json
sys.path.insert(0, ".")

from src.dify_client import DifyClient

# 测试用例：每个问题应该命中哪个章节
TEST_CASES = [
    # (query, 期望命中的章节关键词, 说明)
    ("Python 变量怎么赋值", "基础语法", "变量赋值 → 01章"),
    ("int 和 float 有什么区别", "基础语法", "数据类型 → 01章"),
    ("Python for 循环怎么写", "条件判断", "循环 → 02章"),
    ("if elif else 用法", "条件判断", "条件判断 → 02章"),
    ("如何定义一个函数", "函数", "函数定义 → 03章"),
    ("import random 怎么用", "模块", "模块导入 → 03章"),
    ("Python 列表怎么追加元素", "列表", "列表操作 → 04章"),
    ("字典如何遍历", "字典", "字典遍历 → 04章"),
    ("Python 读写文件", "文件", "文件操作 → 05章"),
    ("try except 异常处理", "异常", "异常处理 → 05章"),
    ("NumPy 创建数组", "NumPy", "NumPy → 06章"),
    ("numpy array 形状", "NumPy", "NumPy形状 → 06章"),
    ("Python 类和对象", "面向对象", "OOP → 07章"),
    ("class __init__", "面向对象", "类定义 → 07章"),
    ("Pandas 读取 CSV", "Pandas", "Pandas → 08章"),
    ("DataFrame 分组统计", "Pandas", "分组统计 → 08章"),
    ("Matplotlib 画折线图", "可视化", "Matplotlib → 09章"),
    ("plt.bar 柱状图", "可视化", "柱状图 → 09章"),
    ("数据分析完整流程", "实战", "综合实战 → 10章"),
    ("电商销售数据分析", "实战", "实战项目 → 10章"),
]

# 预期不应该命中的场景（负例）
NEGATIVE_CASES = [
    ("线性代数", "不应该命中 Python 学习路径"),
    ("量子计算", "不应该命中 Python 学习路径"),
]


def run_verification(kb_id: str = None):
    client = DifyClient(kb_id=kb_id)

    print("=" * 60)
    print("知识库检索验证")
    print(f"KB_ID: {client.kb_id}")
    print(f"Base URL: {client.base_url}")
    print("=" * 60)

    passed = 0
    failed = 0

    print("\n--- 正例测试（每个问题应命中对应章节）---\n")

    for query, expected_keyword, desc in TEST_CASES:
        results = client.retrieve(query, top_k=3, score_threshold=0.3)

        if not results:
            print(f"  ❌ [{desc}]  query='{query}'")
            print(f"     结果为空（检索未命中任何内容）")
            failed += 1
            continue

        top = results[0]
        title = top.title
        score = top.score

        if expected_keyword in title:
            print(f"  ✅ [{desc}] score={score:.2f} | → {title}")
            passed += 1
        else:
            print(f"  ⚠️  [{desc}] query='{query}'")
            print(f"     期望包含: '{expected_keyword}'")
            print(f"     实际返回: {title} (score={score:.2f})")
            # 展示全部返回结果供分析
            for i, r in enumerate(results):
                print(f"       [{i+1}] {r.title} (score={r.score:.2f})"
                      f" — {r.content[:60]}...")
            failed += 1

    print("\n--- 负例测试（无关问题应返回低分或无结果）---\n")
    for query, desc in NEGATIVE_CASES:
        results = client.retrieve(query, top_k=3, score_threshold=0.3)
        if results and results[0].score > 0.5:
            print(f"  ⚠️  [{desc}]")
            print(f"     却命中了: {results[0].title} (score={results[0].score:.2f})")
            failed += 1
        else:
            print(f"  ✅ [{desc}] → 正确排除")
            passed += 1

    # 统计
    total = len(TEST_CASES) + len(NEGATIVE_CASES)
    print("\n" + "=" * 60)
    print(f"结果: {passed}/{total} 通过  |  {failed}/{total} 失败")
    print("=" * 60)

    if failed > 0:
        print("\n📌 常见失败原因及修复：")
        print("  1. KB_ID 填错了 → 检查 .env 中的 DIFY_KB_ID")
        print("  2. 文档还没索引完 → Dify 界面查看状态是否为『可用』")
        print("  3. score_threshold 太高 → 降为 0.3 试试")
        print("  4. 关键词不匹配 → 调整文档的 keywords 字段")
        print("  5. Dify 服务没启动 → docker compose ps 检查")
        sys.exit(1)
    else:
        print("\n🎉 全部通过！知识库检索质量良好。")
        sys.exit(0)


if __name__ == "__main__":
    # 支持命令行传 KB_ID
    kb_id = sys.argv[1] if len(sys.argv) > 1 else None
    run_verification(kb_id)