# 清理项目无用代码计划

## 📌 目标

删除项目中的无用代码，包括：
- 未使用的导入 (unused imports)
- 未使用的变量 (unused variables)
- 未使用的函数/类 (unused functions/classes)
- 重复代码 (duplicate code)
- 废弃的注释代码 (dead code)

## 📋 检查清单

### 1. Python 静态分析

- [ ] **未使用的导入**: `pyflakes` 或 `autoflake`
- [ ] **未使用的变量**: `pylint` 或 `flake8`
- [ ] **重复代码**: `simian` 或 `detect-duplicate-code`

### 2. 手动检查

- [ ] 空目录 (`__pycache__` 除外)
- [ ] 临时文件 (`*.tmp`, `*.bak`)
- [ ] 旧的备份文件 (`*.backup`, `*.old`)
- [ ] 空的 `__init__.py` 文件（不必要的）
- [ ] 重复的函数/类
- [ ] 过时的注释代码
- [ ] 无用的 TODO/FIXME 注释

### 3. 具体检查项

#### 项目根目录
- [ ] 检查是否有临时文件
- [ ] 检查是否有备份文件
- [ ] 检查是否有不必要的隐藏文件

#### 各模块目录
- [ ] `core/` - 检查是否有未使用的工具函数
- [ ] `data/` - 检查是否有未使用的数据加载代码
- [ ] `factors/` - 检查是否有未实现的因子
- [ ] `backtest/` - 检查是否有未使用的回测组件
- [ ] `dashboard/` - 检查是否有未使用的页面组件

#### 代码检查
- [ ] 搜索 `# TODO:` 注释，检查是否需要处理
- [ ] 搜索 `# FIXME:` 注释，检查是否需要处理
- [ ] 搜索 `pass` 语句，检查是否是无用的占位符
- [ ] 搜索 `...` (Ellipsis)，检查是否是无用的占位符

## 🎯 执行步骤

### Step 1: 安装静态分析工具

```bash
pip install autoflake flake8 pyflakes
```

### Step 2: 运行自动检查

```bash
# 未使用的导入
autoflake --remove-unused-imports -r quant_factor_system/

# 代码风格检查
flake8 quant_factor_system/ --select=E9,F63,F7,F82 --show-source --statistics
```

### Step 3: 手动检查

- [ ] 检查空目录
- [ ] 删除临时文件
- [ ] 删除备份文件
- [ ] 删除不必要的 `__init__.py`
- [ ] 删除注释掉的代码

### Step 4: 验证

- [ ] 运行测试确保没有破坏功能
- [ ] 运行导入测试
- [ ] 运行 Dashboard 确保正常启动

## 📁 常见无用代码模式

```python
# 1. 未使用的导入
import os  # 未使用

# 2. 未使用的变量
def func():
    x = 10  # 未使用
    return 5

# 3. 未使用的函数
def unused_func():
    pass

# 4. 占位符代码
def empty_func():
    pass  # 或 ...

# 5. 注释掉的代码
# def old_func():
#     pass
```

## ⚠️ 注意事项

1. **不要删除可能的调试代码** - 确认确实无用再删除
2. **不要删除可能未来需要的代码** - 只删除确定无用的
3. **备份重要代码** - 删除前确认不需要
4. **验证删除后果** - 删除后运行测试

---

*创建时间: 2026-02-19*
