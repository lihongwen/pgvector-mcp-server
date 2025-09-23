# pgvector MCP Server

一个基于 Model Context Protocol (MCP) 的 PostgreSQL 向量数据库管理服务器，专为现代AI应用设计。

## 功能特性

- **MCP 兼容**: 完全基于 Model Context Protocol，与AI助手无缝集成
- **集合管理**: 创建、列出、重命名和删除向量集合
- **向量操作**: 添加向量、搜索相似内容、批量文档处理
- **智能编码**: 自动检测文件编码，特别优化Windows中文文件兼容性
- **嵌入服务**: 集成阿里云DashScope text-embedding-v4模型
- **现代包管理**: 基于uv包管理器，快速安装和依赖管理
- **原子操作**: 数据库事务保证集合重命名等操作的原子性
- **跨平台支持**: Windows、macOS、Linux全平台兼容

## 快速开始

### 1. 安装方式

**方式1：使用 uvx 直接运行 (最推荐)**
```bash
# 无需安装，直接在MCP配置中使用uvx运行
# uvx会自动下载和管理包
```

**方式2：使用 uv 安装**
```bash
# 全局工具安装
uv tool install pgvector-mcp-server

# 或项目依赖安装
uv add pgvector-mcp-server
```

**方式3：使用 pip 安装**
```bash
pip install pgvector-mcp-server
```

### 2. 设置数据库

```bash
# 连接PostgreSQL并启用pgvector扩展
psql postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 创建专用数据库（可选）
createdb mcp_vectors
```

### 3. 配置MCP客户端

在你的MCP客户端配置文件中添加以下配置 (例如 Claude Desktop):

**推荐配置 (使用 uvx，无需预安装)**:
```json
{
  "mcpServers": {
    "pgvector-mcp-server": {
      "command": "uvx",
      "args": ["pgvector-mcp-server"],
      "env": {
        "DATABASE_URL": "postgresql://username:password@localhost:5432/mcp_vectors",
        "DASHSCOPE_API_KEY": "your_dashscope_api_key_here",
        "DEBUG": "false"
      }
    }
  }
}
```

**备选配置 (如果已安装)**:
```json
{
  "mcpServers": {
    "pgvector-mcp-server": {
      "command": "pgvector-mcp-server",
      "env": {
        "DATABASE_URL": "postgresql://username:password@localhost:5432/mcp_vectors",
        "DASHSCOPE_API_KEY": "your_dashscope_api_key_here",
        "DEBUG": "false"
      }
    }
  }
}
```

**传统配置 (使用 Python 模块)**:
```json
{
  "mcpServers": {
    "pgvector-mcp-server": {
      "command": "python",
      "args": ["-m", "pgvector_mcp_server"],
      "env": {
        "DATABASE_URL": "postgresql://username:password@localhost:5432/mcp_vectors",
        "DASHSCOPE_API_KEY": "your_dashscope_api_key_here",
        "DEBUG": "false"
      }
    }
  }
}
```

### 4. 验证安装

使用MCP客户端调用 `status` 工具验证连接:

```json
{
  "tool": "status",
  "parameters": {}
}
```

预期响应:
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
  }
}
```

## MCP 工具参考

pgvector MCP Server 提供以下10个工具供MCP客户端调用:

### 1. 系统状态检查
```json
{
  "tool": "status",
  "parameters": {}
}
```

### 2. 集合管理

#### 创建集合
```json
{
  "tool": "create_collection",
  "parameters": {
    "name": "my_documents",
    "description": "我的文档集合",
    "dimension": 1024
  }
}
```

#### 列出所有集合
```json
{
  "tool": "list_collections",
  "parameters": {
    "include_documents": true
  }
}
```

#### 查看集合详情
```json
{
  "tool": "show_collection",
  "parameters": {
    "name": "my_documents",
    "include_stats": true
  }
}
```

#### 重命名集合 (新功能)
```json
{
  "tool": "rename_collection",
  "parameters": {
    "old_name": "my_documents",
    "new_name": "document_library"
  }
}
```

#### 删除集合
```json
{
  "tool": "delete_collection",
  "parameters": {
    "name": "my_documents",
    "confirm": true
  }
}
```

### 3. 向量操作

#### 添加文本向量
```json
{
  "tool": "add_text",
  "parameters": {
    "collection_name": "my_documents",
    "text": "这是一个示例文档内容",
    "metadata": {
      "source": "manual",
      "type": "document",
      "category": "技术文档"
    }
  }
}
```

#### 搜索相似内容
```json
{
  "tool": "search_collection",
  "parameters": {
    "collection_name": "my_documents",
    "query": "机器学习相关内容",
    "limit": 5,
    "search_strategy": "smart",
    "min_similarity": 0.7
  }
}
```

#### 添加文档文件
```json
{
  "tool": "add_document",
  "parameters": {
    "collection_name": "my_documents",
    "file_path": "/path/to/document.pdf",
    "metadata": {
      "category": "manual",
      "language": "zh"
    }
  }
}
```

#### 删除向量
```json
{
  "tool": "delete_vectors",
  "parameters": {
    "collection_name": "my_documents",
    "file_path": "/path/to/old_document.pdf",
    "confirm": true
  }
}
```

## 使用示例

### 基础工作流程

通过MCP客户端依次调用以下工具：

```json
// 1. 检查系统状态
{
  "tool": "status",
  "parameters": {}
}

// 2. 创建文档集合
{
  "tool": "create_collection",
  "parameters": {
    "name": "documents",
    "description": "文档知识库"
  }
}

// 3. 添加文档内容
{
  "tool": "add_text",
  "parameters": {
    "collection_name": "documents",
    "text": "机器学习是人工智能的重要分支",
    "metadata": {"type": "knowledge"}
  }
}

// 4. 搜索相关内容
{
  "tool": "search_collection",
  "parameters": {
    "collection_name": "documents",
    "query": "深度学习",
    "limit": 3
  }
}

// 5. 查看集合统计
{
  "tool": "show_collection",
  "parameters": {
    "name": "documents",
    "include_stats": true
  }
}
```

### 文档处理示例

```json
// 处理PDF文档
{
  "tool": "add_document",
  "parameters": {
    "collection_name": "tech_docs",
    "file_path": "/Users/username/documents/manual.pdf",
    "metadata": {
      "category": "technical",
      "language": "zh",
      "source": "official_docs"
    }
  }
}

// 搜索文档内容
{
  "tool": "search_collection",
  "parameters": {
    "collection_name": "tech_docs",
    "query": "API配置方法",
    "search_strategy": "smart",
    "metadata_filters": {
      "category": "technical"
    }
  }
}
```

### 集合重命名和管理示例

```json
// 重命名集合（新功能）
{
  "tool": "rename_collection",
  "parameters": {
    "old_name": "temp_docs",
    "new_name": "permanent_docs"
  }
}

// 列出所有集合
{
  "tool": "list_collections",
  "parameters": {
    "include_documents": true
  }
}

// 删除不需要的向量
{
  "tool": "delete_vectors",
  "parameters": {
    "collection_name": "permanent_docs",
    "file_path": "/old/path/outdated.pdf",
    "confirm": true
  }
}
```

## 特性说明

### Windows编码兼容性
- **自动编码检测**: 支持GBK、GB2312、UTF-8等编码格式
- **中文文件处理**: 优化Windows环境下的中文文件名和内容处理
- **编码转换**: 自动转换为UTF-8进行统一处理

### 搜索策略
- **smart**: SQL + 语义搜索智能组合（推荐）
- **sql_only**: 仅使用传统SQL文本搜索
- **semantic_only**: 仅使用向量相似度搜索

### 原子操作保证
- **集合重命名**: 使用数据库事务确保操作原子性
- **批量插入**: 向量数据批量处理时保证一致性
- **错误恢复**: 操作失败时自动回滚，确保数据完整性

### 性能优化
- **向量索引**: 使用pgvector的ivfflat索引优化搜索性能
- **批量处理**: 支持文档分块和批量向量生成
- **连接池**: SQLAlchemy连接池提高数据库访问效率
- **响应时间**: 文档处理目标响应时间<2秒

## 系统要求

- **Python**: 3.10+ (使用现代Python特性)
- **PostgreSQL**: 12+ 并启用pgvector扩展
- **pgvector**: 0.4.0+ 版本
- **MCP客户端**: 支持MCP协议的AI助手 (如Claude Desktop)
- **包管理**: uv (推荐) 或 pip
- **阿里云API**: DashScope API密钥用于文本嵌入

## 开发和部署

### uv项目开发
```bash
# 克隆项目
git clone <repository_url>
cd pgvector-mcp-server

# 使用uv安装依赖
uv sync

# 运行测试
uv run pytest

# 构建包
uv build

# 发布到PyPI
uv publish
```

### 环境变量配置
```bash
# 必需配置
DATABASE_URL=postgresql://username:password@localhost:5432/database
DASHSCOPE_API_KEY=your_api_key_here

# 可选配置
DEBUG=false  # 调试模式
```

## 安装配置说明

### uvx 方式的优势
- **无需预安装**: uvx 会自动下载和管理包及其依赖
- **隔离环境**: 每个工具运行在独立环境中，避免依赖冲突  
- **自动更新**: 始终使用最新版本
- **简化配置**: 配置文件更简洁，无需指定路径

### 配置选择建议
- **新用户**: 推荐使用 uvx 配置，最简单快捷
- **开发者**: 使用 `uv tool install` 安装后直接调用命令
- **生产环境**: 可选择传统的 Python 模块方式，便于版本控制

## 故障排除

**常见问题**:
- 数据库连接失败: 检查DATABASE_URL格式和PostgreSQL服务状态
- pgvector扩展未找到: 在PostgreSQL中执行 `CREATE EXTENSION vector;`
- API密钥错误: 验证DASHSCOPE_API_KEY是否正确配置
- 集合重命名失败: 检查新名称是否已存在
- uvx 网络问题: 确保网络连接正常，uvx 需要从PyPI下载包

## 完整文档

- [快速开始指南](specs/001-mcpserver-cli-mcpserver/quickstart.md)
- [API工具参考](specs/001-mcpserver-cli-mcpserver/contracts/mcp_tools.yaml)
- [数据模型设计](specs/001-mcpserver-cli-mcpserver/data-model.md)