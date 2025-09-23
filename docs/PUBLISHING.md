# PyPI Publishing Guide: pgvector-mcp-server

这个文档描述了如何使用 uv 包管理器构建和发布 pgvector-mcp-server 到 PyPI。

## 前置要求

### 1. 环境准备

```bash
# 安装uv包管理器 (如果尚未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证uv安装
uv --version

# 验证Python版本
python --version  # 应该是3.10+
```

### 2. PyPI账户设置

```bash
# 安装twine (如果需要额外验证)
uv add --dev twine

# 配置PyPI API令牌
# 在 ~/.pypirc 中添加:
[pypi]
username = __token__
password = your_pypi_api_token_here

# 或使用环境变量
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=your_pypi_api_token_here
```

## 发布流程

### 1. 版本准备

#### 1.1 更新版本号

在 `pyproject.toml` 中更新版本号：

```toml
[project]
name = "pgvector-mcp-server"
version = "1.0.0"  # 更新版本号
```

#### 1.2 验证项目配置

```bash
# 检查项目配置
uv check

# 验证依赖关系
uv lock --check
```

### 2. 代码质量检查

```bash
# 运行测试套件
uv run pytest tests/ -v

# 类型检查 (如果配置了mypy)
uv run mypy pgvector_mcp_server/

# 代码格式化检查
uv run black --check pgvector_mcp_server/
uv run isort --check-only pgvector_mcp_server/
```

### 3. 文档更新

```bash
# 更新CHANGELOG.md
echo "## [1.0.0] - $(date +%Y-%m-%d)" >> CHANGELOG.md
echo "### Added" >> CHANGELOG.md
echo "- 新功能描述" >> CHANGELOG.md

# 验证README.md和快速开始指南
uv run python -m pgvector_mcp_server --help
```

### 4. 构建分发包

```bash
# 清理之前的构建
rm -rf dist/

# 使用uv构建包
uv build

# 验证构建产物
ls -la dist/
# 应该看到:
# pgvector_mcp_server-1.0.0-py3-none-any.whl
# pgvector_mcp_server-1.0.0.tar.gz
```

### 5. 本地测试分发包

```bash
# 创建测试环境
python -m venv test_env
source test_env/bin/activate

# 安装构建的包
pip install dist/pgvector_mcp_server-1.0.0-py3-none-any.whl

# 测试安装
python -c "from pgvector_mcp_server import __version__; print(__version__)"

# 测试MCP server启动
python -m pgvector_mcp_server --help

# 清理测试环境
deactivate
rm -rf test_env
```

### 6. 发布到PyPI

#### 6.1 发布到测试PyPI (推荐先测试)

```bash
# 发布到测试PyPI
uv publish --repository testpypi dist/*

# 验证测试发布
pip install --index-url https://test.pypi.org/simple/ pgvector-mcp-server==1.0.0
```

#### 6.2 发布到正式PyPI

```bash
# 发布到正式PyPI
uv publish dist/*

# 验证正式发布
pip install pgvector-mcp-server==1.0.0
```

### 7. 发布后验证

```bash
# 验证包可以正常安装
uv add pgvector-mcp-server==1.0.0

# 检查PyPI页面
# https://pypi.org/project/pgvector-mcp-server/
```

## 版本管理策略

### 语义版本控制

遵循 [SemVer](https://semver.org/) 版本控制规范：

- **MAJOR** (主版本): 不兼容的API更改
- **MINOR** (次版本): 向后兼容的功能添加
- **PATCH** (补丁版本): 向后兼容的错误修复

#### 版本示例

```bash
# 新功能发布
1.0.0 -> 1.1.0

# 错误修复
1.1.0 -> 1.1.1

# 重大更改
1.1.1 -> 2.0.0
```

### 预发布版本

```bash
# Alpha版本
1.0.0a1, 1.0.0a2

# Beta版本
1.0.0b1, 1.0.0b2

# 候选版本
1.0.0rc1, 1.0.0rc2
```

## 自动化发布 (GitHub Actions)

### 创建发布工作流

在 `.github/workflows/publish.yml` 中创建自动发布流程：

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
      with:
        version: "latest"
    
    - name: Set up Python
      run: uv python install 3.11
    
    - name: Install dependencies
      run: uv sync --all-extras --dev
    
    - name: Run tests
      run: uv run pytest
    
    - name: Build package
      run: uv build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: uv publish
```

### 配置GitHub Secrets

在GitHub仓库设置中添加：

- `PYPI_API_TOKEN`: PyPI API令牌

## 常见问题解决

### 1. 构建失败

```bash
# 检查pyproject.toml语法
uv check

# 更新uv到最新版本
curl -LsSf https://astral.sh/uv/install.sh | sh

# 清理缓存重新构建
uv cache clean
uv build
```

### 2. 上传失败

```bash
# 检查网络连接
ping pypi.org

# 验证API令牌
# 在PyPI账户设置中重新生成API令牌

# 手动使用twine上传 (备用方案)
uv run twine upload dist/*
```

### 3. 版本冲突

```bash
# PyPI不允许重复版本号，需要更新版本
# 在pyproject.toml中更新版本号后重新构建

# 检查已发布版本
pip index versions pgvector-mcp-server
```

### 4. 依赖问题

```bash
# 更新uv.lock文件
uv lock --upgrade

# 验证依赖兼容性
uv tree

# 解决依赖冲突
uv add "package>=1.0,<2.0"
```

## 发布检查清单

- [ ] 代码通过所有测试
- [ ] 版本号正确更新
- [ ] CHANGELOG.md已更新
- [ ] README.md反映最新功能
- [ ] 依赖关系已锁定 (uv.lock)
- [ ] 本地测试包安装成功
- [ ] 测试PyPI发布成功
- [ ] 正式PyPI发布成功
- [ ] GitHub发布标签已创建
- [ ] 发布公告已发布

## 最佳实践

1. **渐进发布**: 先发布到测试PyPI
2. **版本一致性**: 确保所有地方的版本号一致
3. **文档同步**: 发布前更新所有相关文档
4. **回滚准备**: 保留发布前的代码状态
5. **监控发布**: 发布后监控下载和使用情况

## 相关链接

- [uv Documentation](https://docs.astral.sh/uv/)
- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/)
