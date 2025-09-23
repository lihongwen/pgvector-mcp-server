# Data Model: pgvector MCP Server

**Feature**: pgvector MCP Server 重构与简化  
**Date**: 2025-09-23  

## 概述

定义重构后MCP server的核心数据实体模型，基于现有PostgreSQL+pgvector架构，优化数据结构以支持集合重命名和高效向量操作。

## 核心实体

### 1. Collection（集合实体）

**用途**: 管理向量集合的元数据和配置信息

**表名**: `collections`

**字段定义**:
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | 集合唯一标识符 |
| `name` | String(255) | UNIQUE, NOT NULL, INDEX | 集合名称，支持重命名操作 |
| `description` | Text | NULLABLE | 集合描述信息 |
| `dimension` | Integer | NOT NULL, DEFAULT=1024 | 向量维度，固定为1024（DashScope） |
| `is_active` | Boolean | DEFAULT=True | 软删除标记 |
| `created_at` | DateTime | NOT NULL, DEFAULT=NOW() | 创建时间戳 |
| `updated_at` | DateTime | NULLABLE, ON UPDATE=NOW() | 更新时间戳（重命名时更新） |
| `deleted_at` | DateTime | NULLABLE | 软删除时间戳 |

**关系**:
- `One-to-Many` → VectorRecord (一个集合包含多个向量记录)

**业务规则**:
- 集合名称必须唯一（重命名时检查冲突）
- 软删除：设置`is_active=False`和`deleted_at`时间戳
- 重命名操作：原子性更新`name`和`updated_at`字段
- 维度固定为1024，与DashScope嵌入服务匹配

### 2. VectorRecord（向量记录实体）

**用途**: 存储向量数据和相关元数据

**表名**: `vectors_{collection_name}` (动态表名，按集合分表)

**字段定义**:
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | 向量记录唯一标识符 |
| `collection_id` | Integer | FOREIGN KEY, NOT NULL, INDEX | 关联的集合ID |
| `content` | Text | NOT NULL | 原始文本内容 |
| `vector` | Vector(1024) | NOT NULL | pgvector向量数据 |
| `extra_metadata` | JSONB | DEFAULT='{}' | 扩展元数据（文件路径、类型等） |
| `created_at` | DateTime | NOT NULL, DEFAULT=NOW() | 创建时间戳 |

**关系**:
- `Many-to-One` → Collection (多个向量记录属于一个集合)

**业务规则**:
- 向量维度必须为1024
- 文件路径存储在extra_metadata中，支持编码检测
- 批量插入时使用数据库事务确保一致性
- 集合重命名时，vector表名不变（通过collection_id关联）

**索引设计**:
```sql
-- 向量相似度搜索索引
CREATE INDEX idx_vectors_{collection_name}_vector 
ON vectors_{collection_name} 
USING ivfflat (vector vector_cosine_ops) 
WITH (lists = 100);

-- 元数据查询索引  
CREATE INDEX idx_vectors_{collection_name}_metadata 
ON vectors_{collection_name} 
USING gin (extra_metadata);

-- 集合关联索引
CREATE INDEX idx_vectors_{collection_name}_collection_id 
ON vectors_{collection_name} (collection_id);
```

## 配置实体

### 3. Settings（配置实体）

**用途**: 简化的应用配置管理

**存储方式**: 环境变量 + .env文件（非数据库存储）

**配置字段**:
| 配置名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|---------|------|
| `DATABASE_URL` | String | ✅ | 无 | PostgreSQL连接字符串 |
| `DASHSCOPE_API_KEY` | String | ✅ | 无 | 阿里云DashScope API密钥 |
| `DASHSCOPE_BASE_URL` | String | ❌ | https://dashscope.aliyuncs.com/compatible-mode/v1 | DashScope服务端点 |
| `DEBUG` | Boolean | ❌ | False | 调试模式开关 |

**简化策略**:
- 移除复杂的配置选项（连接池、清理策略等使用默认值）
- 仅保留核心必需配置
- 通过pydantic-settings进行类型验证

## 数据流模型

### 集合重命名流程

```
1. 验证输入 → 检查名称格式和冲突
2. 开始事务 → 数据库事务开始
3. 更新Collection记录 → name + updated_at字段
4. 提交事务 → 原子性完成重命名
5. 返回结果 → 成功或错误信息
```

### 文档处理流程

```
1. 文件上传 → 自动编码检测（Windows兼容）
2. 内容分块 → 使用chunking_service
3. 向量生成 → 批量调用DashScope API
4. 数据存储 → 批量插入VectorRecord
5. 索引更新 → pgvector自动更新相似度索引
```

## 数据一致性规则

**引用完整性**:
- VectorRecord.collection_id必须存在于Collection.id
- 集合删除时级联删除相关向量（软删除）

**并发控制**:
- 集合重命名使用数据库锁防止并发冲突
- 批量向量插入使用事务确保一致性

**数据验证**:
- 集合名称：字母、数字、下划线，长度1-64字符
- 向量维度：固定1024维度
- 元数据：有效JSON格式

## 性能优化

**查询优化**:
- 向量相似度搜索使用ivfflat索引
- 元数据查询使用GIN索引
- 分页查询避免大结果集

**存储优化**:
- 按集合分表减少单表数据量
- JSONB格式存储元数据提高查询效率
- 软删除避免硬删除的性能影响

**缓存策略**:
- SQLAlchemy连接池复用数据库连接
- 预编译查询模式减少SQL解析开销

## 迁移策略

**现有数据兼容**:
- 保持Collection和VectorRecord表结构不变
- 重构代码时保持数据库schema兼容性
- 集合重命名功能为新增功能，不影响现有数据

**版本升级**:
- 使用SQLAlchemy的Alembic进行schema版本管理
- 渐进式迁移，避免长时间服务中断

此数据模型设计支持功能规格中的所有需求：集合管理、重命名操作、向量搜索、文档处理和Windows编码兼容性。
