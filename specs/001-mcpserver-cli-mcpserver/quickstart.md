# Quick Start Guide: pgvector MCP Server

**版本**: 1.0.0  
**目标用户**: 需要向量数据库管理功能的开发者  

## 概述

pgvector MCP Server 是一个轻量级的 Model Context Protocol 服务器，提供 PostgreSQL + pgvector 向量数据库管理功能。支持集合管理、向量搜索、文档处理和集合重命名等操作。

## 系统要求

- **Python**: 3.10+
- **PostgreSQL**: 12+ (需启用 pgvector 扩展)
- **包管理器**: uv (推荐) 或 pip
- **操作系统**: Windows, macOS, Linux

## 快速安装

### 1. 使用 uv 安装 (推荐)

```bash
# 安装 pgvector MCP server
uv add pgvector-mcp-server

# 或者从 PyPI 安装
pip install pgvector-mcp-server
```

### 2. 数据库准备

```bash
# 连接到 PostgreSQL
psql -U postgres

# 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

# 创建数据库用户（可选）
CREATE USER mcp_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE your_database TO mcp_user;
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库连接 (必需)
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# DashScope API 密钥 (必需)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 可选配置 (有默认值)
DEBUG=false
```

**配置说明**:
- `DATABASE_URL`: PostgreSQL 连接字符串
- `DASHSCOPE_API_KEY`: 阿里云 DashScope API 密钥（用于文本嵌入）
- 其他参数使用智能默认值，无需手动配置

## 基础使用

### 启动 MCP Server

```python
# 方式1: 直接运行
python -c "from pgvector_mcp_server import run_server; run_server()"

# 方式2: 作为模块运行
python -m pgvector_mcp_server

# 方式3: 在代码中使用
from pgvector_mcp_server import FastMCP
app = FastMCP("pgvector-mcp-server")
app.run()
```

### 验证系统状态

使用 MCP 客户端调用 `status` 工具：

```json
{
  "tool": "status",
  "parameters": {}
}
```

预期响应：

```json
{
  "success": true,
  "database": {
    "connected": true,
    "pgvector_installed": true
  },
  "embedding_service": {
    "available": true,
    "provider": "DashScope"
  },
  "collections": {
    "total": 0
  }
}
```

## 核心功能演示

### 1. 创建集合

```json
{
  "tool": "create_collection",
  "parameters": {
    "name": "my_documents",
    "description": "我的文档集合"
  }
}
```

### 2. 添加文本内容

```json
{
  "tool": "add_text",
  "parameters": {
    "collection_name": "my_documents",
    "text": "这是一段示例文本，将被转换为向量并存储。",
    "metadata": {
      "source": "demo",
      "type": "text"
    }
  }
}
```

### 3. 搜索相似内容

```json
{
  "tool": "search_collection",
  "parameters": {
    "collection_name": "my_documents",
    "query": "示例文本",
    "limit": 5
  }
}
```

### 4. 重命名集合 (新功能)

```json
{
  "tool": "rename_collection",
  "parameters": {
    "old_name": "my_documents",
    "new_name": "document_library"
  }
}
```

### 5. 批量处理文档

```json
{
  "tool": "add_document",
  "parameters": {
    "collection_name": "document_library",
    "file_path": "/path/to/document.pdf",
    "metadata": {
      "category": "manual",
      "language": "zh"
    }
  }
}
```

## 高级功能

### Windows 编码支持

服务器自动检测和处理文件编码，特别针对 Windows 环境优化：

- 自动检测 GBK、GB2312、UTF-8 等编码
- 统一转换为 UTF-8 进行处理
- 中文和特殊字符完全支持

### 智能搜索策略

支持多种搜索模式：

```json
{
  "tool": "search_collection",
  "parameters": {
    "collection_name": "my_collection",
    "query": "搜索内容",
    "search_strategy": "smart",  // 智能搜索
    "metadata_filters": {
      "category": "important"
    }
  }
}
```

**搜索策略说明**:
- `smart`: SQL + 语义搜索智能组合
- `sql_only`: 仅使用传统 SQL 搜索
- `semantic_only`: 仅使用向量相似度搜索

### 批量操作优化

文档处理针对性能进行了优化：

- 自动分块处理大文档
- 批量向量生成（减少 API 调用）
- 数据库事务确保一致性
- 进度报告和错误恢复

## 故障排除

### 常见问题

**1. 数据库连接失败**

```
错误: Failed to connect to database
解决: 检查 DATABASE_URL 格式和数据库服务状态
```

**2. pgvector 扩展未安装**

```
错误: pgvector extension not found
解决: 在 PostgreSQL 中执行 CREATE EXTENSION vector;
```

**3. API 密钥无效**

```
错误: DashScope API authentication failed
解决: 检查 DASHSCOPE_API_KEY 是否正确
```

**4. 集合重命名失败**

```
错误: Collection name already exists
解决: 选择不同的集合名称，或先删除同名集合
```

### 性能优化建议

1. **数据库优化**:
   ```sql
   -- 为大型集合创建适当的索引
   CREATE INDEX idx_collection_vectors ON vectors_collection_name 
   USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
   ```

2. **批量操作**:
   - 使用 `add_document` 而非多次 `add_text`
   - 合理设置文档分块大小（500-1000字符）

3. **内存管理**:
   - 大文档处理时监控内存使用
   - 适当调整数据库连接池大小

## 下一步

- 查看 [API 参考文档](contracts/mcp_tools.yaml) 了解所有可用工具
- 参考 [数据模型文档](data-model.md) 了解数据结构设计  
- 浏览 [GitHub 仓库](https://github.com/username/pgvector-mcp-server) 获取源码和示例

## 支持与反馈

- 📧 Email: support@example.com
- 🐛 Issues: GitHub Issues
- 📖 文档: 项目 README

**版本兼容性**: 此快速指南适用于 pgvector MCP Server v1.0.0+
