---
title: NumPy 基础 — 数组与数值计算
prerequisites: 10-常用标准库.md
next: 12-Pandas与数据可视化.md
keywords: numpy, array, shape, 广播, 矩阵运算, ndarray
difficulty: 2
estimated_hours: 2.5
---

## 学习目标

理解 NumPy 核心概念：ndarray、形状、广播机制、基础矩阵运算。

## 核心概念

### 创建数组
```python
import numpy as np

a = np.array([1, 2, 3, 4, 5])
b = np.zeros((3, 4))         # 3行4列全0
c = np.ones((2, 3))          # 全1
d = np.arange(0, 10, 2)      # [0, 2, 4, 6, 8]
e = np.random.randn(5)       # 5个正态分布随机数
```

### 形状操作
```python
arr = np.array([[1,2,3],[4,5,6]])
print(arr.shape)             # (2, 3)
print(arr.reshape(3, 2))     # 重塑
print(arr.T)                 # 转置
```

### 广播与运算
```python
a = np.array([1, 2, 3])
print(a + 10)                # [11, 12, 13] — 广播
print(a * 2)                 # [2, 4, 6]
print(a.sum(), a.mean(), a.max())
```

### 索引与切片
```python
arr = np.array([[1,2,3],[4,5,6],[7,8,9]])

print(arr[0])           # 第一行
print(arr[:, 0])        # 第一列
print(arr[0:2, 1:3])    # 前两行，后两列

# 布尔索引
a = np.array([1, 2, 3, 4, 5])
print(a[a > 3])         # [4, 5]
```

### 矩阵运算
```python
a = np.array([[1, 2], [3, 4]])
b = np.array([[5, 6], [7, 8]])

print(a + b)                    # 逐元素相加
print(a * b)                    # 逐元素相乘
print(np.dot(a, b))             # 矩阵乘法
print(a @ b)                    # 矩阵乘法（Python 3.5+）
```

### 统计函数
```python
arr = np.array([[1, 2, 3], [4, 5, 6]])

print(arr.sum())          # 所有元素求和
print(arr.sum(axis=0))    # 每列求和
print(arr.sum(axis=1))    # 每行求和
print(arr.mean())         # 平均值
print(arr.std())          # 标准差
print(arr.min(), arr.max())  # 最小最大值
```

## 练习题

1. 生成一个 5x5 的随机矩阵，计算每行每列的平均值
2. 用 NumPy 实现向量点积和矩阵乘法
3. 创建一个 10x10 的矩阵，边框为 1，内部为 0
4. 从数组中提取所有大于平均值的元素

## 学习资源

### 推荐视频

- 🎥 [黑马程序员数据分析 - NumPy数值计算](https://www.bilibili.com/video/BV1ReshzoEgG?p=50)
  - 来源：B站 · 黑马程序员官方账号
  - 对应章节：P50 NumPy介绍 ~ P65 统计函数
  - 推荐理由：从零基础讲起，案例丰富，数组运算讲得透彻

- 🎥 [尚硅谷Python数据分析 - NumPy入门](https://www.bilibili.com/video/BV1hV4y1P7oP?p=6)
  - 来源：B站 · 尚硅谷官方账号
  - 对应章节：P06 NumPy介绍 ~ P21 本章练习
  - 推荐理由：图文并茂，广播机制讲解清晰

- 🎥 [莫烦Python - NumPy & Pandas教程](https://www.bilibili.com/video/BV1Ex411L7oT?p=1)
  - 来源：B站 · 莫烦Python
  - 对应章节：P1 Numpy属性 ~ P16 Numpy copy
  - 推荐理由：语速快，干货多，适合有基础的同学快速过一遍

### 文档教程

- 📖 [NumPy 官方文档（中文）](https://numpy.org.cn/)
- 📖 [菜鸟教程 - NumPy教程](https://www.runoob.com/numpy/numpy-tutorial.html)
- 📖 [廖雪峰Python教程 - numpy](https://www.liaoxuefeng.com/wiki/1016959663602400/1017802386482496)

### 在线练习

- 💻 [NumPy 100题](https://github.com/rougier/numpy-100)
