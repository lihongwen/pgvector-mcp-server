# Research: pgvector MCP Server 重构

**Feature**: pgvector MCP Server 重构与简化  
**Date**: 2025-09-23  

## 研究目标

基于现有混合CLI+MCP server项目，研究重构为纯MCP server所需的技术决策、包管理迁移和配置简化策略。

## 技术决策研究

### 1. uv包管理器迁移策略

**决策**: 采用uv替代传统pip+requirements.txt管理方式

**理由**:
- uv是现代Python包管理器，速度比pip快10-100倍
- 提供更好的依赖解析和锁定文件管理
- 用户明确要求使用uv进行包管理
- 支持pyproject.toml标准化配置

**迁移步骤**:
1. 移除requirements.txt、setup.py等旧文件  
2. 更新pyproject.toml配置符合uv标准
3. 创建uv.lock锁定文件确保依赖稳定性
4. 配置uv.toml（已存在，设置了中国镜像源）

**替代方案考虑**: 继续使用pip - 被拒绝，因为用户明确要求现代化包管理

### 2. PyPI发布配置

**决策**: 重命名包为`pgvector-mcp-server`，配置PyPI发布

**理由**:
- 原包名`pgvector-cli`包含CLI概念，不符合纯MCP server定位
- PyPI命名惯例使用连字符分隔单词
- 需要配置uv兼容的发布流程

**配置要点**:
- 更新pyproject.toml中的包名和元数据
- 配置entry_points指向MCP server入口
- 设置合适的版本号和依赖关系
- 准备发布文档

### 3. Windows编码兼容性处理

**决策**: 实现自动文件编码检测和UTF-8转换

**理由**:
- Windows环境常见GBK、GB2312等编码
- 用户明确要求处理中文和特殊字符
- 澄清确认采用自动检测策略

**实现方案**:
- 使用chardet库进行编码检测
- 自动转换为UTF-8进行处理
- 在utils/encoding.py中实现专用模块
- 集成到文档解析流程中

**替代方案**: 强制UTF-8编码 - 被拒绝，兼容性差

### 4. 配置简化策略

**决策**: 仅保留DATABASE_URL和DASHSCOPE_API_KEY两个必需配置

**理由**:
- 用户要求极简配置
- 其他参数设置合理默认值
- 降低用户使用门槛

**简化映射**:
- 保留: DATABASE_URL (数据库连接)
- 保留: DASHSCOPE_API_KEY (嵌入服务)
- 默认: DEBUG=false
- 默认: 日志级别、连接池、清理策略等

### 5. 集合重命名功能设计

**决策**: 添加rename_collection MCP工具，原子性操作

**理由**:
- 功能规格明确要求
- 数据库层面支持事务保证原子性
- 名称冲突时提示用户选择新名称

**实现要点**:
- 在mcp_server.py中添加@mcp.tool()装饰的重命名函数
- 使用数据库事务确保原子性
- 验证新名称不冲突
- 更新collection表的name字段和updated_at时间戳

## 项目结构清理研究

### 当前文件分析

**需要保留和重构的核心文件**:
- `mcp_server.py` → `pgvector_mcp_server/server.py` (主入口)
- `pgvector_cli/models/` → `pgvector_mcp_server/models/` (数据模型)
- `pgvector_cli/services/` → `pgvector_mcp_server/services/` (业务逻辑)
- `pgvector_cli/config.py` → `pgvector_mcp_server/config.py` (简化配置)
- `pgvector_cli/database.py` → `pgvector_mcp_server/database.py`
- `pgvector_cli/exceptions.py` → `pgvector_mcp_server/exceptions.py`
- `pgvector_cli/utils/` → `pgvector_mcp_server/utils/` (工具函数)

**需要删除的文件和目录**:
- `pgvector_cli/main.py` (CLI入口)
- `pgvector_cli/__main__.py` (CLI模块入口)
- `server_core/` (重复代码目录)
- `tests/` (旧测试，需重写)
- `test_documents/` (测试文档)
- `__pycache__/` (缓存目录)
- `pgvector_mcp_server.egg-info/` (旧打包信息)
- `start_mcp_server.*` (启动脚本)
- `docker-compose.mcp.yml`, `Dockerfile.mcp` (Docker文件)
- `setup.py`, `setup_mcp.py` (旧打包脚本)
- `requirements.txt` (旧依赖文件)
- `verify_wsl_compatibility.py` (WSL兼容检查)

### 依赖清理分析

**需要移除的CLI相关依赖**:
- `click>=8.0.0` (CLI框架)
- `rich>=13.0.0` (CLI美化)
- `tabulate>=0.9.0` (表格显示)

**需要保留的核心依赖**:
- `mcp>=1.2.0` (MCP协议)
- `sqlalchemy>=2.0.0` (ORM)
- `psycopg2-binary>=2.9.0` (PostgreSQL驱动)
- `pgvector>=0.4.0` (向量扩展)
- `dashscope>=1.0.0` (嵌入服务)
- 文档处理相关依赖
- `chardet>=5.0.0` (编码检测)

## 风险评估

**低风险**:
- 包重命名和PyPI发布配置
- uv包管理器迁移
- 文件清理操作

**中等风险**:
- 配置简化可能影响现有用户
- Windows编码处理需要充分测试

**缓解策略**:
- 保留.env.example文件作为配置参考
- 编写详细的迁移文档
- 在重命名功能中进行充分的错误处理

## 结论

所有技术决策都有明确的实现路径，风险可控。重构方案既满足用户需求（简化、现代化），又保持了核心功能的完整性。下一步可以进入设计阶段。
