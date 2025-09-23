
# Implementation Plan: pgvector MCP Server 重构与简化

**Branch**: `001-mcpserver-cli-mcpserver` | **Date**: 2025-09-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-mcpserver-cli-mcpserver/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
**主要需求**: 将现有的混合CLI工具+MCP server项目重构为纯MCP server，移除所有CLI功能，添加集合重命名工具，简化配置，支持PyPI发布和uv包管理。

**技术方针**: 保留核心MCP server功能和向量数据库服务，清理项目结构，迁移到uv包管理，简化用户配置流程（只需数据库连接+API密钥），确保Windows编码兼容性。

## Technical Context
**Language/Version**: Python 3.10+ (现有代码基于>=3.10要求)  
**Primary Dependencies**: MCP (FastMCP), SQLAlchemy, pgvector, DashScope, pydantic  
**Storage**: PostgreSQL with pgvector extension for vector storage  
**Testing**: pytest (需要重新设计测试策略，移除CLI相关测试)  
**Target Platform**: 跨平台MCP server，特别关注Windows编码兼容性
**Project Type**: single (纯MCP server，非web/mobile应用)  
**Performance Goals**: 高效向量搜索，支持批量文档处理，<2s文档处理响应  
**Constraints**: 简化配置（仅数据库+API密钥），自动文件编码检测，原子性重命名操作  
**Scale/Scope**: 支持中小型向量数据库，数千个集合，数万条向量记录

**用户特殊要求**: 
- 使用uv包管理器替代传统pip/requirements.txt
- 发布到PyPI用于uv add安装
- 清理项目文件，移除CLI工具、测试文件、缓存等垃圾文件
- 迁移配置简化：原有复杂配置→仅需DATABASE_URL + DASHSCOPE_API_KEY

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**简化原则 (Constitution placeholder - 基于项目需求设定)**:
- ✅ **单一职责**: 项目专注于MCP server功能，移除CLI工具
- ✅ **最小配置**: 配置参数限制为DATABASE_URL + DASHSCOPE_API_KEY
- ✅ **结构简化**: 避免复杂的目录层级，清理无关文件
- ✅ **跨平台兼容**: 特别关注Windows环境的文件编码处理
- ✅ **包管理现代化**: 使用uv替代传统pip/requirements.txt

**检查结果**: PASS - 所有设计决策符合简化和专注原则

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# 重构后的简化结构 (专注MCP server)
pgvector_mcp_server/              # 重命名的包名，符合PyPI惯例
├── __init__.py
├── server.py                     # 主MCP server入口
├── config.py                     # 简化的配置管理
├── database.py                   # 数据库连接管理
├── exceptions.py                 # 异常定义
├── models/                       # 数据模型
│   ├── __init__.py
│   ├── collection.py
│   └── vector_record.py
├── services/                     # 业务服务层
│   ├── __init__.py
│   ├── collection_service.py
│   ├── vector_service.py
│   ├── document_service.py
│   ├── embedding_service.py
│   └── parsers/                  # 文档解析器
│       ├── __init__.py
│       ├── base_parser.py
│       ├── text_parser.py
│       ├── csv_parser.py
│       └── pdf_parser.py
└── utils/                        # 工具函数
    ├── __init__.py
    ├── validators.py
    └── encoding.py               # 新增：Windows编码处理

# 简化的项目根目录
pyproject.toml                    # uv项目配置
README.md                         # 用户文档
LICENSE                           # 许可证
.env.example                      # 配置示例
```

**需要清理的现有文件**:
- 删除: `pgvector_cli/` (整个CLI包)
- 删除: `server_core/` (重复代码)
- 删除: `tests/` (旧测试文件) 
- 删除: `test_documents/` (测试文档)
- 删除: 各种启动脚本、Docker文件、__pycache__/ 等
- 保留并重构: `mcp_server.py` → `pgvector_mcp_server/server.py`

**Structure Decision**: 简化的单包结构，专注MCP server功能

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh cursor`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- **文件清理任务**: 删除CLI相关代码、测试文件、缓存和重复代码
- **项目重构任务**: 重命名包结构，迁移核心代码到新的目录结构
- **功能增强任务**: 添加集合重命名工具、简化配置管理、Windows编码处理
- **包管理迁移**: 更新pyproject.toml、移除旧依赖、配置uv工作流
- **测试和验证**: 创建基础集成测试、验证MCP工具功能

**具体任务类别**:
1. **清理任务 [P]**: 删除pgvector_cli/、server_core/、tests/等目录
2. **重构任务**: 创建pgvector_mcp_server/包结构，迁移核心文件
3. **新功能任务**: 实现rename_collection工具，添加encoding.py模块
4. **配置任务 [P]**: 更新pyproject.toml，简化config.py
5. **验证任务**: MCP工具集成测试，文档验证

**Ordering Strategy**:
- **Phase 1**: 清理和重构 (为新结构准备)
- **Phase 2**: 核心功能迁移和新功能实现  
- **Phase 3**: 包管理和配置更新
- **Phase 4**: 测试验证和文档完善
- 标记 [P] 用于可并行执行的独立任务

**特殊考虑**:
- 用户要求：详细分析现有代码，清理垃圾文件
- Windows兼容性：编码处理优先级高
- 原子性重命名：数据库事务设计重要

**预估输出**: 20-25个具体任务，涵盖重构、功能开发、测试验证

**重要**: 此阶段由/tasks命令执行，/plan命令不执行实际任务创建

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS (设计符合简化和专注原则)
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (无复杂性偏差需要证明)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
