---
title: NumPy 数值计算入门
prerequisites: 04-列表与字典.md
keywords: numpy, array, shape, 广播, 矩阵运算
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

## 练习题

1. 生成一个 5x5 的随机矩阵，计算每行每列的平均值
2. 用 NumPy 实现向量点积和矩阵乘法