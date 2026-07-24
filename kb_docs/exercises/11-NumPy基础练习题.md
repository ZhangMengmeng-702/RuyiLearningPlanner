---
title: NumPy基础练习题
chapter: 11-NumPy基础
difficulty: 2
keywords: NumPy, ndarray, 数组, 矩阵运算, 索引, 广播
---

# 第十一章：NumPy基础练习题

## 题目

### 题1：数组创建与基本属性（难度：⭐）

**题目**：完成以下操作：
1. 创建一个 1 维数组，包含 0-9 的整数
2. 创建一个 3×3 的全 0 数组
3. 创建一个 2×4 的全 1 数组
4. 创建一个 4×4 的单位矩阵
5. 创建一个长度为 10 的随机数组（0-1 之间）
6. 打印上面每个数组的 shape、ndim、dtype

**提示**：
- `np.arange(10)`
- `np.zeros((3, 3))`
- `np.ones((2, 4))`
- `np.eye(4)`
- `np.random.random(10)`

**参考解答**：
```python
import numpy as np

# 1. 一维数组
arr1 = np.arange(10)
print("数组1：", arr1)
print("  shape:", arr1.shape, "ndim:", arr1.ndim, "dtype:", arr1.dtype)

# 2. 全0数组
arr2 = np.zeros((3, 3))
print("\n数组2：\n", arr2)
print("  shape:", arr2.shape, "ndim:", arr2.ndim, "dtype:", arr2.dtype)

# 3. 全1数组
arr3 = np.ones((2, 4))
print("\n数组3：\n", arr3)
print("  shape:", arr3.shape, "ndim:", arr3.ndim, "dtype:", arr3.dtype)

# 4. 单位矩阵
arr4 = np.eye(4)
print("\n数组4：\n", arr4)
print("  shape:", arr4.shape, "ndim:", arr4.ndim, "dtype:", arr4.dtype)

# 5. 随机数组
arr5 = np.random.random(10)
print("\n数组5：", arr5)
print("  shape:", arr5.shape, "ndim:", arr5.ndim, "dtype:", arr5.dtype)
```

---

### 题2：数组索引与切片（难度：⭐⭐）

**题目**：有一个 5×5 的数组：
```python
arr = np.arange(25).reshape(5, 5)
```
取出以下内容：
1. 第 2 行（索引从0开始）
2. 第 3 列
3. 第 1-3 行，第 2-4 列（子矩阵）
4. 所有大于 10 的元素
5. 对角线元素

**提示**：
- 行索引：`arr[row_idx]`
- 列索引：`arr[:, col_idx]`
- 切片：`arr[start:end, start:end]`
- 布尔索引：`arr[arr > 10]`
- 对角线：`np.diag(arr)`

**参考解答**：
```python
import numpy as np

arr = np.arange(25).reshape(5, 5)
print("原数组：\n", arr)

# 1. 第2行
print("\n第2行：", arr[2])

# 2. 第3列
print("第3列：", arr[:, 3])

# 3. 子矩阵 1-3行，2-4列
print("子矩阵(1-3行, 2-4列)：\n", arr[1:4, 2:5])

# 4. 大于10的元素
print("大于10的元素：", arr[arr > 10])

# 5. 对角线
print("对角线元素：", np.diag(arr))
```

---

### 题3：数组运算（难度：⭐⭐）

**题目**：有两个数组：
```python
a = np.array([1, 2, 3, 4, 5])
b = np.array([10, 20, 30, 40, 50])
```
完成以下运算：
1. 对应元素相加、相减、相乘、相除
2. 每个元素平方
3. 计算 a 和 b 的点积（内积）
4. 比较 a 和 b 的大小，返回布尔数组
5. 求 a 的总和、平均值、最大值、最小值、标准差

**提示**：
- 数组运算都是逐元素的
- 点积：`np.dot(a, b)` 或 `a @ b`
- 统计方法：`.sum()`, `.mean()`, `.max()`, `.min()`, `.std()`

**参考解答**：
```python
import numpy as np

a = np.array([1, 2, 3, 4, 5])
b = np.array([10, 20, 30, 40, 50])

print("a =", a)
print("b =", b)

# 1. 四则运算
print("\n相加：", a + b)
print("相减：", a - b)
print("相乘：", a * b)
print("相除：", a / b)

# 2. 平方
print("\n每个元素平方：", a ** 2)

# 3. 点积
print("点积：", np.dot(a, b))

# 4. 比较
print("\na < b：", a < b)
print("a == b：", a == b)

# 5. 统计
print("\n总和：", a.sum())
print("平均值：", a.mean())
print("最大值：", a.max())
print("最小值：", a.min())
print("标准差：", a.std())
```

---

### 题4：矩阵运算（难度：⭐⭐⭐）

**题目**：有两个矩阵：
```python
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
```
完成以下操作：
1. 矩阵乘法（A × B）
2. A 的转置
3. A 的逆矩阵
4. A 的行列式
5. 解线性方程组 Ax = b，其中 b = [1, 2]

**提示**：
- 矩阵乘法：`A @ B` 或 `np.dot(A, B)`
- 转置：`A.T`
- 逆矩阵：`np.linalg.inv(A)`
- 行列式：`np.linalg.det(A)`
- 解方程组：`np.linalg.solve(A, b)`

**参考解答**：
```python
import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
b = np.array([1, 2])

print("A =\n", A)
print("B =\n", B)

# 1. 矩阵乘法
print("\nA × B =\n", A @ B)

# 2. 转置
print("A 的转置 =\n", A.T)

# 3. 逆矩阵
print("A 的逆矩阵 =\n", np.linalg.inv(A))

# 4. 行列式
print("A 的行列式 =", np.linalg.det(A))

# 5. 解方程组
x = np.linalg.solve(A, b)
print("Ax = b 的解 x =", x)
print("验证 Ax =", A @ x)
```

---

### 题5：广播机制（难度：⭐⭐⭐）

**题目**：利用广播机制完成以下任务：
1. 给一个 3×3 矩阵的每一行加上同一个向量 `[1, 2, 3]`
2. 给一个 3×3 矩阵的每一列加上同一个向量 `[10, 20, 30]`
3. 将一个 1 维数组 `[1, 2, 3, 4]` 变成 4×4 矩阵，每一行都是这个数组
4. 计算两个数组的欧氏距离矩阵（行与行之间的距离）

**提示**：
- 广播规则：维度不同时，从右往左对齐，大小为 1 的维度会被扩展
- 行向量形状 (1, n)，列向量形状 (m, 1)

**参考解答**：
```python
import numpy as np

# 1. 每行加向量
matrix = np.zeros((3, 3))
row_vec = np.array([1, 2, 3])  # shape: (3,)
result1 = matrix + row_vec
print("每行加向量：\n", result1)

# 2. 每列加向量
col_vec = np.array([[10], [20], [30]])  # shape: (3, 1)
result2 = matrix + col_vec
print("\n每列加向量：\n", result2)

# 3. 1维数组变成4行
arr = np.array([1, 2, 3, 4])  # shape: (4,)
result3 = arr.reshape(1, 4).repeat(4, axis=0)
# 或者用广播：
result3_2 = arr + np.zeros((4, 1))
print("\n变成4行矩阵：\n", result3)

# 4. 欧氏距离矩阵
A = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])  # 4个点
# 计算两两之间的距离
diff = A[:, np.newaxis, :] - A[np.newaxis, :, :]
dist_matrix = np.sqrt((diff ** 2).sum(axis=2))
print("\n欧氏距离矩阵：\n", dist_matrix)
```
