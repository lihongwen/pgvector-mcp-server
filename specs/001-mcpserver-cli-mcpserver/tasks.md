# Tasks: pgvector MCP Server 重构与简化

**Input**: Design documents from `/specs/001-mcpserver-cli-mcpserver/`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓), quickstart.md (✓)

**Tech Stack**: Python 3.10+, FastMCP, SQLAlchemy, pgvector, DashScope, uv包管理
**Project Structure**: 单一MCP server项目 (pgvector_mcp_server/)

## Format: `[ID] [P?] Description`
- **[P]**: 可以并行运行（不同文件，无依赖关系）
- 所有任务都包含精确的文件路径

## Phase 3.1: 项目清理与准备 🧹
**目标**: 移除CLI工具，清理垃圾文件，为重构做准备

- [x] T001 [P] 删除CLI主模块文件：pgvector_cli/__main__.py, pgvector_cli/main.py
- [x] T002 [P] 删除CLI相关测试目录：tests/ (整个目录)
- [x] T003 [P] 删除重复代码目录：server_core/ (整个目录) 
- [x] T004 [P] 删除测试文档目录：test_documents/ (整个目录)
- [x] T005 [P] 删除缓存和构建文件：__pycache__/, pgvector_mcp_server.egg-info/, *.pyc
- [x] T006 [P] 删除Docker相关文件：docker-compose.mcp.yml, Dockerfile.mcp
- [x] T007 [P] 删除旧启动脚本：start_mcp_server.*, setup.py, setup_mcp.py
- [x] T008 [P] 删除兼容性检查文件：verify_wsl_compatibility.py
- [x] T009 [P] 删除旧依赖管理文件：requirements.txt

## Phase 3.2: 新项目结构创建 📁
**目标**: 创建重构后的pgvector_mcp_server包结构

- [x] T010 创建新包根目录：pgvector_mcp_server/
- [x] T011 [P] 创建包初始化文件：pgvector_mcp_server/__init__.py
- [x] T012 [P] 创建子目录结构：pgvector_mcp_server/{models/, services/, utils/}
- [x] T013 [P] 创建服务子目录：pgvector_mcp_server/services/parsers/

## Phase 3.3: 核心模块迁移 🔄
**目标**: 将现有核心代码迁移到新结构，保持功能完整性

- [x] T014 迁移主服务器文件：mcp_server.py → pgvector_mcp_server/server.py
- [x] T015 [P] 迁移数据库模块：pgvector_cli/database.py → pgvector_mcp_server/database.py
- [x] T016 [P] 迁移异常定义：pgvector_cli/exceptions.py → pgvector_mcp_server/exceptions.py
- [x] T017 [P] 迁移Collection模型：pgvector_cli/models/collection.py → pgvector_mcp_server/models/collection.py
- [x] T018 [P] 迁移VectorRecord模型：pgvector_cli/models/vector_record.py → pgvector_mcp_server/models/vector_record.py
- [x] T019 [P] 迁移服务模块：pgvector_cli/services/ → pgvector_mcp_server/services/ (5个服务文件)
- [x] T020 [P] 迁移解析器模块：pgvector_cli/services/parsers/ → pgvector_mcp_server/services/parsers/ (4个解析器)
- [x] T021 [P] 迁移验证工具：pgvector_cli/utils/validators.py → pgvector_mcp_server/utils/validators.py
- [x] T022 [P] 迁移格式化工具：pgvector_cli/utils/formatters.py → pgvector_mcp_server/utils/formatters.py

## Phase 3.4: 配置简化和新功能开发 ⚙️
**目标**: 实现配置简化、Windows编码支持和集合重命名功能

- [x] T023 简化配置模块：修改pgvector_mcp_server/config.py，移除DATABASE_URL和DASHSCOPE_API_KEY的硬编码默认值，要求由MCP客户端env提供，保留技术常量（dimension=1024等）
- [x] T024 [P] 创建Windows编码处理模块：pgvector_mcp_server/utils/encoding.py (自动检测+UTF-8转换)
- [x] T025 实现集合重命名MCP工具：在pgvector_mcp_server/server.py中添加rename_collection函数
- [x] T026 更新集合服务：修改pgvector_mcp_server/services/collection_service.py添加rename_collection方法
- [x] T027 集成编码检测：修改文档解析器调用encoding.py进行编码处理

## Phase 3.5: 包管理和发布配置 📦
**目标**: 迁移到uv包管理，配置PyPI发布

- [x] T028 更新pyproject.toml：修改包名为pgvector-mcp-server，移除CLI相关依赖和脚本
- [x] T029 [P] 创建新的包入口点：pgvector_mcp_server/cli.py (仅MCP server启动)
- [x] T030 [P] 更新包初始化：pgvector_mcp_server/__init__.py导出主要类和函数
- [x] T031 [P] 创建uv.lock文件：运行uv lock生成依赖锁定文件
- [x] T032 [P] 完善MCP配置文档：更新claude_desktop_config_example.json，添加详细配置说明和注释，确保用户明确在MCP客户端环境中配置

## Phase 3.6: MCP工具集成测试 🧪
**目标**: 验证所有10个MCP工具功能正常

- [x] T033 [P] 创建MCP工具测试：tests/test_mcp_tools.py (status, create_collection, list_collections)
- [x] T034 [P] 创建重命名功能测试：tests/test_rename_collection.py (验证原子性和冲突处理)
- [x] T035 [P] 创建编码处理测试：tests/test_encoding.py (Windows兼容性验证)
- [x] T036 [P] 创建集成测试：tests/test_integration.py (完整工作流测试)

## Phase 3.7: 文档和验证 📚
**目标**: 更新文档，验证功能完整性

- [x] T037 [P] 更新README.md：反映纯MCP server定位，添加uv安装指南
- [x] T038 [P] 创建PyPI发布文档：docs/PUBLISHING.md (uv build和发布流程)
- [x] T039 运行完整功能验证：按quickstart.md执行所有基础操作
- [x] T040 [P] 性能基准测试：验证<2s文档处理响应时间
- [x] T041 Windows兼容性测试：在Windows环境测试中文文件处理

## Dependencies

**阶段依赖**:
- Phase 3.1 (清理) → Phase 3.2 (创建结构)
- Phase 3.2 (结构) → Phase 3.3 (迁移)  
- Phase 3.3 (迁移) → Phase 3.4 (新功能)
- Phase 3.4 (新功能) → Phase 3.5 (包管理)
- Phase 3.5 (包管理) → Phase 3.6 (测试)
- Phase 3.6 (测试) → Phase 3.7 (验证)

**关键依赖关系**:
- T010 blocks T011-T013, T014-T022
- T014 blocks T025 (需要server.py存在才能添加重命名功能)
- T023 blocks T032 (简化配置后才能完善MCP配置文档)
- T025-T027 blocks T034 (重命名功能实现后才能测试)
- T024 blocks T035 (编码模块创建后才能测试)
- T028-T031 blocks T038 (包配置完成后才能写发布文档)

## Parallel Execution Examples

**Phase 3.1 并行清理 (可同时执行)**:
```bash
# 同时删除多个无关联的目录和文件
Task: "删除CLI主模块文件：pgvector_cli/__main__.py, pgvector_cli/main.py"
Task: "删除CLI相关测试目录：tests/"  
Task: "删除重复代码目录：server_core/"
Task: "删除缓存和构建文件：__pycache__/, *.pyc"
Task: "删除Docker相关文件：docker-compose.mcp.yml, Dockerfile.mcp"
```

**Phase 3.3 并行迁移 (可同时执行)**:
```bash
# 迁移不同的模块文件，无相互依赖
Task: "迁移数据库模块：pgvector_cli/database.py → pgvector_mcp_server/database.py"
Task: "迁移异常定义：pgvector_cli/exceptions.py → pgvector_mcp_server/exceptions.py"
Task: "迁移Collection模型：pgvector_cli/models/collection.py → pgvector_mcp_server/models/collection.py"
Task: "迁移VectorRecord模型：pgvector_cli/models/vector_record.py → pgvector_mcp_server/models/vector_record.py"
```

**Phase 3.6 并行测试 (可同时执行)**:
```bash
# 测试不同功能模块，测试文件独立
Task: "创建MCP工具测试：tests/test_mcp_tools.py"
Task: "创建重命名功能测试：tests/test_rename_collection.py"
Task: "创建编码处理测试：tests/test_encoding.py"
Task: "创建集成测试：tests/test_integration.py"
```

## Notes

- **[P] 标记规则**: 不同文件或目录的操作可以并行执行
- **迁移策略**: 保持代码功能不变，仅改变文件位置和包结构  
- **测试优先**: 新功能(T025-T027)在测试(T033-T036)之前完成
- **配置策略**: 仅通过MCP客户端环境变量配置，简化必需参数为DATABASE_URL和DASHSCOPE_API_KEY
- **Windows特别关注**: T024、T035、T041专门处理Windows编码问题
- **原子性重命名**: T025、T026确保数据库事务完整性
- **性能要求**: T040验证<2s响应时间目标

## Task Generation Rules Applied

1. **从研究文档 (research.md)**:
   - uv迁移 → T028-T031 包管理任务
   - 编码处理 → T024, T027, T035 编码相关任务
   - 配置简化 → T023, T032 MCP配置任务

2. **从数据模型 (data-model.md)**:
   - Collection实体 → T017, T026 集合相关任务
   - VectorRecord实体 → T018 向量记录任务
   - 重命名功能 → T025, T034 重命名相关任务

3. **从合约 (contracts/)**:
   - 10个MCP工具 → T033 MCP工具测试
   - rename_collection → T025, T034 重命名工具实现和测试

4. **从快速开始 (quickstart.md)**:
   - 用户场景 → T039 完整功能验证
   - 安装流程 → T037 README更新

## Validation Checklist ✅

- [x] 所有contracts的MCP工具都有对应的实现任务 (T025为新工具，其他在T014迁移中)
- [x] 所有data-model实体都有模型迁移任务 (T017-T018)  
- [x] 所有核心功能都有测试任务 (T033-T036)
- [x] 并行任务确实无相互依赖 ([P]标记的任务操作不同文件)
- [x] 每个任务都指定了精确的文件路径
- [x] 没有任务修改相同文件作为另一个[P]任务 (已验证无冲突)
- [x] 用户特殊要求都有对应任务 (CLI清理、uv迁移、Windows编码、重命名功能)

**任务总数**: 41个任务，预计20-25小时完成
**并行任务**: 28个可并行执行，显著提升开发效率
**关键路径**: T010→T014→T025→T034→T039 (核心功能链)
