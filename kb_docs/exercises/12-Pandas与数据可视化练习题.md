---
title: Pandas与数据可视化练习题
chapter: 12-Pandas与数据可视化
difficulty: 3
keywords: Pandas, DataFrame, 数据清洗, 分组, Matplotlib, 可视化
---

# 第十二章：Pandas与数据可视化练习题

## 题目

### 题1：DataFrame创建与基本操作（难度：⭐）

**题目**：完成以下操作：
1. 用字典创建一个 DataFrame，包含 5 个学生的姓名、年龄、语文分数、数学分数
2. 打印前 3 行
3. 打印列名
4. 打印形状（行数、列数）
5. 打印描述性统计信息（describe）
6. 新增一列「总分」= 语文 + 数学
7. 按总分降序排序

**提示**：
- `pd.DataFrame(字典)`
- `.head(n)` 看前 n 行
- `.columns` 列名
- `.shape` 形状
- `.describe()` 统计描述
- `.sort_values(by=列名, ascending=False)` 排序

**参考解答**：
```python
import pandas as pd

data = {
    "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
    "年龄": [18, 19, 17, 18, 20],
    "语文": [85, 92, 78, 88, 90],
    "数学": [92, 88, 85, 79, 95]
}

df = pd.DataFrame(data)
print("原始数据：")
print(df)

# 2. 前3行
print("\n前3行：")
print(df.head(3))

# 3. 列名
print("\n列名：", df.columns.tolist())

# 4. 形状
print("\n形状：", df.shape)

# 5. 描述统计
print("\n描述统计：")
print(df.describe())

# 6. 新增总分列
df["总分"] = df["语文"] + df["数学"]
print("\n新增总分列：")
print(df)

# 7. 按总分降序
df_sorted = df.sort_values(by="总分", ascending=False)
print("\n按总分降序：")
print(df_sorted)
```

---

### 题2：数据选择与筛选（难度：⭐⭐）

**题目**：使用上一题的 DataFrame，完成以下操作：
1. 选出「姓名」列
2. 选出「姓名」和「总分」两列
3. 选出第 2 行（索引为1）
4. 用 `loc` 选出姓名为「张三」的行
5. 用 `iloc` 选出第 1-3 行，第 0-2 列
6. 筛选出语文 > 85 分的学生
7. 筛选出总分 > 170 且 数学 > 90 的学生

**提示**：
- `df["列名"]` 选列
- `df.loc[行标签, 列名]` 按标签选
- `df.iloc[行号, 列号]` 按位置选
- 布尔索引：`df[df["列名"] > 值]`
- 多条件：`(cond1) & (cond2)`

**参考解答**：
```python
import pandas as pd

data = {
    "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
    "年龄": [18, 19, 17, 18, 20],
    "语文": [85, 92, 78, 88, 90],
    "数学": [92, 88, 85, 79, 95]
}
df = pd.DataFrame(data)
df["总分"] = df["语文"] + df["数学"]

# 1. 选一列
print("姓名列：")
print(df["姓名"])

# 2. 选两列
print("\n姓名和总分：")
print(df[["姓名", "总分"]])

# 3. 选第2行（索引1）
print("\n第2行：")
print(df.iloc[1])

# 4. loc 按标签选
print("\n张三的信息：")
print(df.loc[df["姓名"] == "张三"])

# 5. iloc 按位置选
print("\n第1-3行，第0-2列：")
print(df.iloc[0:3, 0:3])

# 6. 语文 > 85
print("\n语文 > 85 分：")
print(df[df["语文"] > 85])

# 7. 总分 > 170 且 数学 > 90
print("\n总分 > 170 且 数学 > 90：")
print(df[(df["总分"] > 170) & (df["数学"] > 90)])
```

---

### 题3：数据清洗（难度：⭐⭐）

**题目**：有以下带有缺失值和重复值的数据：
```python
data = {
    "姓名": ["张三", "李四", "王五", "张三", "赵六", None, "钱七"],
    "年龄": [18, None, 17, 18, 20, 19, 20],
    "分数": [85, 92, None, 85, 88, 90, None]
}
```
完成以下清洗操作：
1. 查看有多少缺失值
2. 删除所有包含缺失值的行
3. 用「年龄」的平均值填充年龄的缺失值
4. 用「分数」的中位数填充分数的缺失值
5. 删除重复行
6. 重置索引

**提示**：
- `.isnull().sum()` 统计缺失值
- `.dropna()` 删除缺失值
- `.fillna(值)` 填充缺失值
- `.drop_duplicates()` 删除重复行
- `.reset_index(drop=True)` 重置索引

**参考解答**：
```python
import pandas as pd
import numpy as np

data = {
    "姓名": ["张三", "李四", "王五", "张三", "赵六", None, "钱七"],
    "年龄": [18, None, 17, 18, 20, 19, 20],
    "分数": [85, 92, None, 85, 88, 90, None]
}
df = pd.DataFrame(data)
print("原始数据：")
print(df)

# 1. 缺失值统计
print("\n缺失值统计：")
print(df.isnull().sum())

# 2. 删除姓名为None的行（先处理这个）
df_clean = df.dropna(subset=["姓名"]).copy()
print("\n删除姓名缺失的行：")
print(df_clean)

# 3. 年龄用平均值填充
age_mean = df_clean["年龄"].mean()
df_clean["年龄"] = df_clean["年龄"].fillna(age_mean)
print(f"\n年龄用平均值({age_mean:.1f})填充：")
print(df_clean)

# 4. 分数用中位数填充
score_median = df_clean["分数"].median()
df_clean["分数"] = df_clean["分数"].fillna(score_median)
print(f"\n分数用中位数({score_median})填充：")
print(df_clean)

# 5. 删除重复行
df_clean = df_clean.drop_duplicates()
print("\n删除重复行：")
print(df_clean)

# 6. 重置索引
df_clean = df_clean.reset_index(drop=True)
print("\n重置索引：")
print(df_clean)
```

---

### 题4：基础柱状图与折线图（难度：⭐⭐）

**题目**：使用 Matplotlib 完成以下可视化任务：
1. 绘制柱状图：展示 5 个学生的语文和数学成绩（并列柱状图）
2. 绘制折线图：展示一周的气温变化
3. 要求：设置标题、轴标签、图例、网格线

**数据**：
- 学生：["张三", "李四", "王五", "赵六", "钱七"]
- 语文：[85, 92, 78, 88, 90]
- 数学：[92, 88, 85, 79, 95]
- 星期：["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
- 气温：[22, 24, 25, 23, 20, 18, 21]

**提示**：
- `plt.bar()` 柱状图
- `plt.plot()` 折线图
- 两组柱状图需要错开 x 位置
- `plt.rcParams["font.sans-serif"]` 设置中文字体

**参考解答**：
```python
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

# 数据
students = ["张三", "李四", "王五", "赵六", "钱七"]
chinese = [85, 92, 78, 88, 90]
math = [92, 88, 85, 79, 95]

# 1. 柱状图
x = np.arange(len(students))
width = 0.35

plt.figure(figsize=(10, 6))
plt.bar(x - width/2, chinese, width, label="语文", color="#FF6B6B")
plt.bar(x + width/2, math, width, label="数学", color="#4ECDC4")

plt.title("学生成绩对比", fontsize=16)
plt.xlabel("学生", fontsize=12)
plt.ylabel("分数", fontsize=12)
plt.xticks(x, students)
plt.legend()
plt.ylim(0, 110)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("scores_bar.png", dpi=100)
plt.show()

# 2. 折线图
days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
temps = [22, 24, 25, 23, 20, 18, 21]

plt.figure(figsize=(10, 6))
plt.plot(days, temps, marker="o", color="red", linewidth=2, linestyle="-")

plt.title("一周气温变化", fontsize=16)
plt.xlabel("日期", fontsize=12)
plt.ylabel("气温 (°C)", fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("temperature.png", dpi=100)
plt.show()
```

---

### 题5：分组聚合与综合可视化（难度：⭐⭐⭐）

**题目**：有以下销售数据，完成分析和可视化：

```python
data = {
    "日期": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"],
    "产品": ["A", "B", "A", "B", "A", "B"],
    "地区": ["北京", "北京", "上海", "上海", "北京", "上海"],
    "销量": [100, 150, 120, 130, 90, 160],
    "销售额": [5000, 7500, 6000, 6500, 4500, 8000]
}
```

要求：
1. 按产品分组，计算总销量和总销售额
2. 按地区分组，计算平均销售额
3. 绘制 2×2 子图：
   - 左上：各产品总销售额柱状图
   - 右上：各地区销量饼图
   - 左下：销量与销售额散点图
   - 右下：各产品平均销售额折线图

**提示**：
- `.groupby(列名).agg(字典)` 分组聚合
- `plt.subplots(2, 2)` 创建子图
- 子图通过 `axes[i, j]` 访问

**参考解答**：
```python
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

data = {
    "日期": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"],
    "产品": ["A", "B", "A", "B", "A", "B"],
    "地区": ["北京", "北京", "上海", "上海", "北京", "上海"],
    "销量": [100, 150, 120, 130, 90, 160],
    "销售额": [5000, 7500, 6000, 6500, 4500, 8000]
}
df = pd.DataFrame(data)
print("原始数据：")
print(df)

# 1. 按产品分组
product_stats = df.groupby("产品").agg({
    "销量": "sum",
    "销售额": "sum"
})
print("\n按产品统计：")
print(product_stats)

# 2. 按地区分组
region_stats = df.groupby("地区")["销售额"].mean()
print("\n各地区平均销售额：")
print(region_stats)

# 3. 可视化
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle("销售数据分析", fontsize=20)

# 左上：产品销售额柱状图
ax1 = axes[0, 0]
product_stats["销售额"].plot(kind="bar", ax=ax1, color="#4ECDC4")
ax1.set_title("各产品总销售额")
ax1.set_ylabel("销售额（元）")
ax1.tick_params(axis="x", rotation=0)
ax1.grid(axis="y", alpha=0.3)

# 右上：地区销量饼图
ax2 = axes[0, 1]
region_sales = df.groupby("地区")["销量"].sum()
ax2.pie(region_sales.values, labels=region_sales.index,
        autopct="%1.1f%%", startangle=90, colors=["#FF6B6B", "#4ECDC4"])
ax2.set_title("各地区销量占比")
ax2.axis("equal")

# 左下：销量vs销售额散点图
ax3 = axes[1, 0]
scatter = ax3.scatter(df["销量"], df["销售额"], c=df["产品"].map({"A": "#FF6B6B", "B": "#4ECDC4"}),
                      s=100, alpha=0.7)
ax3.set_title("销量 vs 销售额")
ax3.set_xlabel("销量（件）")
ax3.set_ylabel("销售额（元）")
ax3.grid(True, alpha=0.3)

# 右下：各产品平均销售额折线图
ax4 = axes[1, 1]
product_avg = df.groupby("产品")["销售额"].mean()
product_avg.plot(kind="line", ax=ax4, marker="o", color="#45B7D1", linewidth=2)
ax4.set_title("各产品平均销售额")
ax4.set_ylabel("平均销售额（元）")
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("sales_analysis.png", dpi=100)
plt.show()
```
