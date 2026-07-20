---
title: Pandas入门 — DataFrame与数据处理
prerequisites: 06-NumPy入门.md, 04-列表与字典.md
next: 09-数据可视化.md
keywords: pandas, DataFrame, Series, read_csv, 数据清洗, groupby, 合并
difficulty: 2
estimated_hours: 3
---

## 学习目标

完成本章后，你能：
1. 理解 DataFrame 和 Series 的概念
2. 用 `read_csv()` 读取外部数据文件
3. 做常见的数据清洗操作（缺失值、重复值、类型转换）
4. 用 `groupby` 做分组统计
5. 合并多个 DataFrame

## 核心概念

### 创建 DataFrame

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

### 读取 CSV 文件

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
print(df.info())        # 列信息、非空计数、数据类型
print(df.describe())    # 数值列的统计摘要
```

### 数据选择与过滤

```python
# 选择列
df["姓名"]             # 单列 → Series
df[["姓名", "成绩"]]   # 多列 → DataFrame

# 选择行（布尔索引）
df[df["成绩"] >= 90]                 # 成绩 >= 90 的行
df[(df["成绩"] >= 80) & (df["年龄"] < 25)]

# 用 loc / iloc
df.loc[0]                # 索引为 0 的行
df.iloc[0:3]             # 前三行
df.loc[df["成绩"] > 80, ["姓名", "成绩"]]  # 条件+指定列
```

### 数据清洗

```python
df.isnull().sum()        # 每列缺失值数量
df.dropna()              # 删除有缺失的行
df.fillna(0)             # 缺失值填 0
df.fillna(df.mean())     # 缺失值填该列平均值

df.duplicated().sum()    # 重复行数
df.drop_duplicates()     # 删除重复行

df["年龄"] = df["年龄"].astype(int)  # 类型转换
```

### 分组统计

```python
# 按班级分组，计算平均成绩
df.groupby("班级")["成绩"].mean()

# 多列统计
df.groupby("班级").agg({
    "成绩": ["mean", "max", "min", "count"],
    "年龄": "mean",
})
```

### 合并数据

```python
# 类似 SQL 的 JOIN
df1 = pd.DataFrame({"ID": [1,2,3], "姓名": ["A","B","C"]})
df2 = pd.DataFrame({"ID": [1,2,4], "成绩": [85,90,88]})

pd.merge(df1, df2, on="ID", how="inner")  # 内连接
pd.merge(df1, df2, on="ID", how="left")   # 左连接
pd.concat([df1, df2], axis=0)             # 行拼接
```

## 练习题

1. 加载项目提供的 `students.csv`（无则自己构造一个包含 10 人信息的 DataFrame），计算每个人的总分和平均分
2. 找出成绩前 3 名的学生
3. 按性别分组，计算男女的平均成绩和最高成绩
4. 将两个 CSV 文件（学生基本信息 + 考试成绩）用 `merge` 合并

## 常见问题

**Q**: `df["列名"]` 和 `df.列名` 有什么区别？
**A**: 两者都能取列，但 `df.列名` 要求列名是合法的 Python 标识符（无空格、无特殊字符），推荐始终用 `df["列名"]`。

**Q**: `inplace=True` 是什么意思？
**A**: 很多 Pandas 操作（如 `dropna`、`fillna`）默认返回新 DataFrame，不修改原数据。传 `inplace=True` 就直接在原数据上修改，但不推荐——链式调用时容易出 Bug。建议用 `df = df.dropna()`。

**Q**: `apply` 怎么用？
**A**: `df["列名"].apply(函数)` 将该函数应用到这一列的每个元素上。例如 `df["成绩"].apply(lambda x: "优秀" if x >= 90 else "良好")`。