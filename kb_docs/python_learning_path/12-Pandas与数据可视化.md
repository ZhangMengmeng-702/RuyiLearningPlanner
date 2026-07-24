---
title: Pandas与数据可视化 — 数据处理与探索分析
prerequisites: 11-NumPy基础.md
next: 13-综合实战项目.md
keywords: pandas, DataFrame, 数据清洗, groupby, 数据可视化, matplotlib, seaborn
difficulty: 2
estimated_hours: 4
---

## 学习目标

完成本章后，你能：
1. 理解 DataFrame 和 Series 的概念
2. 用 `read_csv()` 读取外部数据文件
3. 做常见的数据清洗操作（缺失值、重复值、类型转换）
4. 用 `groupby` 做分组统计
5. 合并多个 DataFrame
6. 用 Matplotlib 和 Seaborn 进行数据探索可视化
7. 掌握折线图、柱状图、散点图、热力图等常用图表

---

## 一、Pandas 基础

### 1.1 什么是 Pandas

Pandas 是 Python 数据分析的核心库，提供了强大的数据结构和数据处理工具。

两个核心数据结构：
- **Series**：一维数据（类似带标签的数组）
- **DataFrame**：二维表格（类似 Excel 表格）

### 1.2 创建 DataFrame

```python
import pandas as pd

# 从字典创建
data = {
    "姓名": ["小明", "小红", "小刚"],
    "年龄": [20, 21, 19],
    "成绩": [85, 92, 78],
}
df = pd.DataFrame(data)
print(df)
#    姓名  年龄  成绩
# 0  小明  20  85
# 1  小红  21  92
# 2  小刚  19  78
```

### 1.3 读取 CSV 文件

```python
# 这是数据分析最常用的操作
df = pd.read_csv("students.csv", encoding="utf-8")

# 常用参数
df = pd.read_csv("data.csv", encoding="utf-8")
#    — encoding: 指定编码（中文数据通常用 utf-8 或 gbk）
#    — header: 第几行是列名（默认 0）
#    — index_col: 指定哪一列作为行索引
#    — dtype: 指定列的数据类型 {"列名": str}

# 快速查看数据
print(df.head())        # 前 5 行
print(df.tail())        # 后 5 行
print(df.info())        # 列信息、非空计数、数据类型
print(df.describe())    # 数值列的统计摘要
print(df.shape)         # (行数, 列数)
```

---

## 二、数据选择与过滤

### 2.1 选择列

```python
# 选择单列 → Series
df["姓名"]

# 选择多列 → DataFrame
df[["姓名", "成绩"]]
```

### 2.2 选择行

```python
# 按索引标签
df.loc[0]                # 索引为 0 的行
df.loc[0:3]              # 索引 0 到 3 的行（包含两端）

# 按位置
df.iloc[0]               # 第一行
df.iloc[0:3]             # 前三行（左闭右开）

# 按条件（布尔索引）
df[df["成绩"] >= 90]                 # 成绩 >= 90 的行
df[(df["成绩"] >= 80) & (df["年龄"] < 25)]  # 多条件
df[df["班级"].isin(["一班", "二班"])]     # 包含在列表中
```

### 2.3 选择行和列

```python
df.loc[df["成绩"] > 80, ["姓名", "成绩"]]  # 条件+指定列
df.iloc[0:5, 0:3]                          # 位置选择
```

---

## 三、数据清洗

### 3.1 缺失值处理

```python
df.isnull().sum()        # 每列缺失值数量
df.dropna()              # 删除有缺失的行
df.dropna(axis=1)        # 删除有缺失的列
df.fillna(0)             # 缺失值填 0
df.fillna(df.mean())     # 缺失值填该列平均值
df["列名"].fillna(df["列名"].median())  # 单列填充
```

### 3.2 重复值处理

```python
df.duplicated().sum()    # 重复行数
df.duplicated(subset=["姓名"]).sum()  # 指定列的重复
df.drop_duplicates()     # 删除重复行
df.drop_duplicates(subset=["姓名"], keep="first")  # 保留第一个
```

### 3.3 类型转换

```python
df["年龄"] = df["年龄"].astype(int)          # 转整数
df["日期"] = pd.to_datetime(df["日期"])      # 转日期
df["性别"] = df["性别"].astype("category")   # 转分类类型
```

### 3.4 列操作

```python
# 新增列
df["总分"] = df["语文"] + df["数学"] + df["英语"]
df["等级"] = df["成绩"].apply(lambda x: "优秀" if x >= 90 else "良好")

# 删除列
df.drop("列名", axis=1, inplace=True)

# 重命名列
df.rename(columns={"old_name": "new_name"}, inplace=True)
```

---

## 四、分组统计

### 4.1 groupby 基础

```python
# 按班级分组，计算平均成绩
df.groupby("班级")["成绩"].mean()

# 多列统计
df.groupby("班级").agg({
    "成绩": ["mean", "max", "min", "count"],
    "年龄": "mean",
})

# 多字段分组
df.groupby(["班级", "性别"])["成绩"].mean()
```

### 4.2 apply 和 transform

```python
# apply：对每组应用函数
df.groupby("班级")["成绩"].apply(lambda x: x.max() - x.min())

# transform：返回与原数据同长度的结果
df["班级平均分"] = df.groupby("班级")["成绩"].transform("mean")
```

### 4.3 排序

```python
df.sort_values("成绩", ascending=False)       # 按成绩降序
df.sort_values(["班级", "成绩"], ascending=[True, False])  # 多列排序
df.sort_index()                                # 按索引排序
```

---

## 五、数据合并

### 5.1 merge（类似 SQL 的 JOIN）

```python
df1 = pd.DataFrame({"ID": [1,2,3], "姓名": ["A","B","C"]})
df2 = pd.DataFrame({"ID": [1,2,4], "成绩": [85,90,88]})

pd.merge(df1, df2, on="ID", how="inner")  # 内连接
pd.merge(df1, df2, on="ID", how="left")   # 左连接
pd.merge(df1, df2, on="ID", how="right")  # 右连接
pd.merge(df1, df2, on="ID", how="outer")  # 外连接
```

### 5.2 concat（拼接）

```python
# 行拼接（上下拼）
pd.concat([df1, df2], axis=0, ignore_index=True)

# 列拼接（左右拼）
pd.concat([df1, df2], axis=1)
```

---

## 六、数据可视化基础 — Matplotlib

### 6.1 为什么需要可视化

数据可视化是数据探索的重要手段，可以快速发现数据中的规律、趋势和异常。

### 6.2 环境准备

```python
import matplotlib.pyplot as plt
import numpy as np

# 解决中文显示问题
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
```

### 6.3 折线图 — 趋势分析

```python
# 月度销售数据
months = ["1月", "2月", "3月", "4月", "5月", "6月"]
sales = [120, 150, 130, 180, 200, 220]

plt.figure(figsize=(10, 6))
plt.plot(months, sales, marker='o', linestyle='-', color='blue', linewidth=2)
plt.title("月度销售额趋势")
plt.xlabel("月份")
plt.ylabel("销售额（万元）")
plt.grid(True, alpha=0.3)
plt.legend(["销售额"])
plt.tight_layout()
plt.show()
```

### 6.4 柱状图 — 对比分析

```python
categories = ["电子产品", "服装", "食品", "家居", "图书"]
values = [500, 350, 420, 280, 180]

plt.figure(figsize=(10, 6))
plt.bar(categories, values, color=['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336'])
plt.title("各品类销售额对比")
plt.ylabel("销售额（万元）")
plt.xticks(rotation=45)

# 在柱子上标数值
for i, v in enumerate(values):
    plt.text(i, v + 10, str(v), ha='center')

plt.tight_layout()
plt.show()
```

### 6.5 散点图 — 相关性分析

```python
# 学习时间 vs 考试分数
study_hours = np.random.normal(5, 2, 100)
scores = 50 + study_hours * 5 + np.random.normal(0, 5, 100)

plt.figure(figsize=(10, 6))
plt.scatter(study_hours, scores, alpha=0.6, color='steelblue')
plt.title("学习时间与成绩的关系")
plt.xlabel("学习时间（小时）")
plt.ylabel("考试分数")
plt.grid(True, alpha=0.3)
plt.show()
```

### 6.6 直方图 — 分布分析

```python
data = np.random.normal(100, 15, 1000)  # 模拟 IQ 数据

plt.figure(figsize=(10, 6))
plt.hist(data, bins=30, edgecolor='white', color='steelblue', alpha=0.7)
plt.title("IQ 分布直方图")
plt.xlabel("IQ 值")
plt.ylabel("人数")
plt.axvline(data.mean(), color='red', linestyle='--', label=f'均值: {data.mean():.1f}')
plt.legend()
plt.show()
```

### 6.7 饼图 — 占比分析

```python
labels = ["电子产品", "服装", "食品", "家居", "图书"]
sizes = [30, 25, 20, 15, 10]
colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336']

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
plt.title("销售额占比")
plt.axis('equal')  # 保证是圆形
plt.show()
```

---

## 七、高级可视化 — Seaborn

### 7.1 Seaborn 简介

Seaborn 基于 Matplotlib，提供了更高级的统计图表接口，样式更美观。

```python
import seaborn as sns
import pandas as pd

# 设置样式
sns.set_style("whitegrid")
sns.set_palette("husl")
```

### 7.2 箱线图 — 分布与异常值

```python
# 加载示例数据
tips = sns.load_dataset("tips")  # 餐厅小费数据

plt.figure(figsize=(10, 6))
sns.boxplot(x="day", y="total_bill", data=tips)
plt.title("各天消费金额分布")
plt.show()
```

### 7.3 热力图 — 相关性矩阵

```python
# 计算数值列的相关性
corr = tips.select_dtypes(include=[np.number]).corr()

plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.title("数值特征相关性热力图")
plt.tight_layout()
plt.show()
```

### 7.4 分布图 — 单变量分布

```python
plt.figure(figsize=(10, 6))
sns.histplot(tips["total_bill"], bins=30, kde=True)
plt.title("消费金额分布")
plt.xlabel("消费金额")
plt.show()
```

### 7.5 散点图矩阵 — 多变量关系

```python
sns.pairplot(tips, hue="time")
plt.suptitle("各特征之间的关系", y=1.02)
plt.show()
```

---

## 八、子图布局

```python
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 子图1：折线图
axes[0, 0].plot(months, sales, marker='o')
axes[0, 0].set_title("月度销售额趋势")
axes[0, 0].set_ylabel("销售额")

# 子图2：柱状图
axes[0, 1].bar(categories, values)
axes[0, 1].set_title("各品类销售额")
axes[0, 1].tick_params(axis='x', rotation=45)

# 子图3：散点图
axes[1, 0].scatter(study_hours, scores, alpha=0.6)
axes[1, 0].set_title("学习时间 vs 成绩")
axes[1, 0].set_xlabel("学习时间")
axes[1, 0].set_ylabel("成绩")

# 子图4：直方图
axes[1, 1].hist(data, bins=30, edgecolor='white')
axes[1, 1].set_title("IQ 分布")
axes[1, 1].set_xlabel("IQ 值")

plt.tight_layout()
plt.show()
```

---

## 九、保存图表

```python
plt.savefig("chart.png", dpi=300, bbox_inches="tight")
# dpi=300 → 高清
# bbox_inches="tight" → 裁掉多余白边
```

---

## 十、数据探索完整流程示例

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 读取数据
df = pd.read_csv("data.csv", encoding="utf-8")

# 2. 快速了解数据
print("数据形状:", df.shape)
print("\n前5行:")
print(df.head())
print("\n列信息:")
print(df.info())
print("\n统计摘要:")
print(df.describe())

# 3. 数据清洗
df = df.dropna()  # 删除缺失值
df = df.drop_duplicates()  # 删除重复值

# 4. 数据分析
print("\n分组统计:")
print(df.groupby("类别")["金额"].agg(["mean", "sum", "count"]))

# 5. 可视化探索
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 各品类销售额
cat_sales = df.groupby("类别")["金额"].sum().sort_values(ascending=False)
axes[0, 0].bar(cat_sales.index, cat_sales.values)
axes[0, 0].set_title("各品类销售额")
axes[0, 0].tick_params(axis='x', rotation=45)

# 金额分布
axes[0, 1].hist(df["金额"], bins=30, edgecolor='white')
axes[0, 1].set_title("消费金额分布")

# 每日销售趋势
daily = df.groupby("日期")["金额"].sum()
axes[1, 0].plot(daily.index, daily.values)
axes[1, 0].set_title("每日销售额趋势")
axes[1, 0].tick_params(axis='x', rotation=45)

# 相关性热力图
corr = df.select_dtypes(include=[np.number]).corr()
sns.heatmap(corr, annot=True, ax=axes[1, 1], cmap="coolwarm", fmt=".2f")
axes[1, 1].set_title("相关性矩阵")

plt.tight_layout()
plt.savefig("data_exploration.png", dpi=200, bbox_inches="tight")
plt.show()
```

---

## 十一、常见问题

**Q**: `df["列名"]` 和 `df.列名` 有什么区别？
**A**: 两者都能取列，但 `df.列名` 要求列名是合法的 Python 标识符（无空格、无特殊字符），推荐始终用 `df["列名"]`。

**Q**: `inplace=True` 是什么意思？
**A**: 很多 Pandas 操作（如 `dropna`、`fillna`）默认返回新 DataFrame，不修改原数据。传 `inplace=True` 就直接在原数据上修改，但不推荐——链式调用时容易出 Bug。建议用 `df = df.dropna()`。

**Q**: `apply` 怎么用？
**A**: `df["列名"].apply(函数)` 将该函数应用到这一列的每个元素上。例如 `df["成绩"].apply(lambda x: "优秀" if x >= 90 else "良好")`。

**Q**: 中文字体显示为方框怎么办？
**A**: 显式设置中文字体：
```python
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
```

**Q**: Seaborn 和 Matplotlib 的关系是什么？
**A**: Seaborn 基于 Matplotlib，提供了更高层的 API。Seaborn 的图表本质上也是 Matplotlib 对象，可以用 `plt` 的 API 进一步修改。

---

## 练习题

1. 加载一个 CSV 数据集，完成数据清洗（处理缺失值、重复值）
2. 用 groupby 按某列分组，计算另一列的统计量（均值、最大值、最小值）
3. 绘制一个包含 4 个子图的 2x2 画布：折线图、柱状图、散点图、直方图
4. 加载一个数据集，用 Seaborn 绘制热力图查看各列之间的相关性
5. 合并两个 DataFrame（类似 SQL 的 JOIN 操作）

---

## 学习资源

### 推荐视频

- 🎥 [黑马程序员数据分析 - Pandas数据处理](https://www.bilibili.com/video/BV1ReshzoEgG?p=70)
  - 来源：B站 · 黑马程序员官方账号
  - 对应章节：P70 Pandas介绍 ~ P120 分组聚合
  - 推荐理由：案例丰富，数据清洗和分组统计讲得非常详细

- 🎥 [黑马程序员数据分析 - 数据可视化](https://www.bilibili.com/video/BV1ReshzoEgG?p=125)
  - 来源：B站 · 黑马程序员官方账号
  - 对应章节：P125 Matplotlib介绍 ~ P140 Seaborn高级图表
  - 推荐理由：从基础图表到高级可视化，案例丰富，讲得很细致

- 🎥 [尚硅谷Python数据分析 - Pandas入门](https://www.bilibili.com/video/BV1hV4y1P7oP?p=22)
  - 来源：B站 · 尚硅谷官方账号
  - 对应章节：P22 Pandas介绍 ~ P51 综合案例
  - 推荐理由：从Series到DataFrame循序渐进，实战案例多

- 🎥 [尚硅谷Python数据分析 - Matplotlib与Seaborn](https://www.bilibili.com/video/BV1hV4y1P7oP?p=53)
  - 来源：B站 · 尚硅谷官方账号
  - 对应章节：P53 可视化介绍 ~ P62 项目实战
  - 推荐理由：图表类型覆盖全面，样式调整讲得很清楚

- 🎥 [莫烦Python - Pandas教程](https://www.bilibili.com/video/BV1Ex411L7oT?p=17)
  - 来源：B站 · 莫烦Python
  - 对应章节：P17 Pandas基本介绍 ~ P30 Pandas plot出图
  - 推荐理由：干货密集，适合快速过一遍核心操作

### 文档教程

- 📖 [Pandas 官方文档（中文）](https://www.pypandas.cn/docs/)
- 📖 [Matplotlib 官方文档（中文）](https://matplotlib.org.cn/)
- 📖 [Seaborn 官方文档](https://seaborn.pydata.org/)
- 📖 [菜鸟教程 - Pandas教程](https://www.runoob.com/pandas/pandas-tutorial.html)
- 📖 [菜鸟教程 - Matplotlib教程](https://www.runoob.com/matplotlib/matplotlib-tutorial.html)
- 📖 [Python Graph Gallery](https://python-graph-gallery.com/) — 各种图表的代码示例

### 在线练习

- 💻 [Pandas 100题](https://github.com/ajcr/100-pandas-puzzles)
- 💻 [Matplotlib 练习题库](https://github.com/rougier/matplotlib-tutorial)
