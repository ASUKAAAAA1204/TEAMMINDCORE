# TeamMindHub Backend 项目需求文档（PRD）

**版本**：v1.2（极详细版）
**日期**：2026年3月27日
**作者**：大一学生（使用 TRAE + Codex + Claude Code + Cursor 等 AI 工具开发）
**项目类型**：纯本地后端服务（FastAPI API + Swagger UI，无独立前端界面）

---

## 文档说明

此 PRD 已高度细化，具体到每个模块的 API 接口、请求/响应字段、处理逻辑、Swagger UI 中的展示与交互细节，以及 Main Orchestrator Agent 的调度流程。

---

## 1. 项目概述

### 1.1 项目基本信息

- **项目名称**：TeamMindHub Backend（团队思维中枢后端）
- **项目定位**：一个运行在本地电脑（RTX 4070 Ti）的模块化 AI 知识与数据处理中枢后端
- **核心能力**：
  - 支持多格式文档深度解析
  - 混合检索
  - 跨文档实体聚合报告
  - 可配置的 Main Orchestrator Agent 智能调度
  - GitHub 工具自动搜索与安全安装

### 1.2 核心价值

1. **解决团队知识碎片化问题**：实现"一句话从多文档生成结构化统合报告"
2. **后端 API 服务化**：便于 TRAE、Codex、Claude Code、Cursor 等编程 AI 工具通过 HTTP 调用，进行数据分析、文件整合等任务
3. **集成成熟开源项目**：利用多个成熟开源项目的核心能力，加速开发并提升文档解析与 Agent 调度质量

### 1.3 项目目标

- **MVP 目标**：6-9 周内用 AI 工具完成 MVP
- **开源目标**：开源到 GitHub 并争取星标
- **部署环境**：本地电脑（RTX 4070 Ti）

### 1.4 目标用户

1. **个人开发者/学生**：自己管理笔记、论文、数据
2. **小型团队**：共享知识库、协作生成报告
3. **AI 编程工具用户**：通过 API 接入后端扩展能力

---

## 2. 系统架构概要

### 2.1 技术栈

| 层级 | 技术/组件 | 说明 |
|------|----------|------|
| **运行方式** | Docker Compose | FastAPI + Chroma + Ollama 容器化部署 |
| **通信协议** | REST API (JSON) + Server-Sent Events (流式) | 同步与异步通信 |
| **存储** | Chroma (向量) + SQLite (元数据) | 向量数据库 + 关系型数据库（可选 PostgreSQL） |
| **模型** | Ollama 本地优先 + 云 API 混合切换 | Qwen2.5、Llama3.1 等模型支持 |
| **开发方式** | AI 驱动 | 按模块让 TRAE 生成代码 |

### 2.2 核心模块架构

```
TeamMindHub Backend
├── modules/ingestion/          # 文档摄入模块
├── modules/retrieval/          # 智能检索模块
├── modules/report/             # 跨文档统合报告模块
├── modules/orchestrator/       # Main Orchestrator Agent 模块
├── modules/installer/          # GitHub 工具安装器
├── modules/analysis/           # 数据分析模块
└── modules/integration/        # 文件整合模块
```

---

## 3. 详细功能规格

### 3.1 文档摄入模块（modules/ingestion/）

#### 功能目标
上传多格式文件 → 深度解析（布局、表格、OCR）→ 分块向量化。

#### 支持的文件格式
- 文档：.pdf、.docx、.pptx
- 表格：.xlsx、.xls
- 图片：.png、.jpg、.jpeg
- 纯文本：.txt

---

#### API 1: POST /ingestion/upload

**请求方式**：multipart/form-data

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| files | List[UploadFile] | 是 | 上传的文件列表 |
| team_id | string | 否 | 团队ID，默认 "default" |
| tags | array[string] | 否 | 标签数组，如 ["sales", "2025"] |
| parse_mode | string | 否 | 解析模式："auto"（自动）\|"deep"（深度）\|"fast"（快速） |

**处理逻辑**：
1. 使用集成解析器提取表格、公式、图片文字
2. 智能 chunking（分块）
3. 生成 embedding 向量
4. 存储到 Chroma 向量数据库
5. "deep" 模式优先使用 RAGFlow/Docling 高级解析

**响应示例**：

```json
{
  "document_ids": ["doc_001", "doc_002"],
  "status": "processing",
  "progress": 0.65,
  "message": "已开始解析 2 个文件"
}
```

**Swagger UI 展示**：
- 文件拖拽上传区
- Parse Mode 下拉选择框
- Tags 多选输入框
- 上传按钮
- 实时进度条显示

---

#### API 2: GET /ingestion/documents

**请求方式**：GET

**Query 参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| team_id | string | 否 | 团队ID筛选 |
| keyword | string | 否 | 关键词搜索 |
| tags | string | 否 | 标签筛选 |
| status | string | 否 | 状态筛选：uploaded/parsed/failed |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 10 |

**响应示例**：

```json
{
  "total": 45,
  "page": 1,
  "page_size": 10,
  "documents": [
    {
      "id": "doc_001",
      "filename": "sales_report_2025.xlsx",
      "upload_time": "2026-03-27T10:30:00Z",
      "parse_status": "parsed",
      "metadata": {
        "pages": 12,
        "tables": 5,
        "images": 3
      },
      "tags": ["sales", "2025"]
    }
  ]
}
```

**Swagger UI 展示**：
- 过滤表单（team_id、keyword、tags、status）
- 可排序表格（文件名、时间、状态）
- 每行操作按钮："详情"、"删除"

---

#### API 3: DELETE /ingestion/{document_id}

**请求方式**：DELETE

**路径参数**：
- document_id: 文档ID

**响应示例**：

```json
{
  "success": true,
  "message": "文档已删除"
}
```

**Swagger UI 展示**：
- 确认对话框
- 删除后自动刷新文档列表

---

### 3.2 智能检索模块（modules/retrieval/）

#### API: POST /retrieval/search

**请求方式**：POST

**请求参数**：

```json
{
  "query": "2025年第一季度销售数据分析",
  "top_k": 8,
  "hybrid_alpha": 0.7,
  "filters": {
    "tags": ["sales"],
    "date_after": "2025-01-01"
  }
}
```

**参数说明**：

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| query | string | 是 | - | 自然语言或关键词查询 |
| top_k | int | 否 | 8 | 返回结果数量 |
| hybrid_alpha | float | 否 | 0.7 | 向量权重（0.0-1.0），越高越偏向语义搜索 |
| filters | object | 否 | - | 过滤条件（标签、日期等） |

**响应示例**：

```json
{
  "results": [
    {
      "text": "2025年第一季度销售额达到500万元，同比增长25%...",
      "score": 0.89,
      "document_id": "doc_001",
      "metadata": {
        "source_page": 3,
        "table_id": "table_002"
      }
    }
  ],
  "total_found": 23
}
```

**功能特点**：
- LlamaIndex 混合检索（语义 + 关键词）
- 支持模糊语义查询
- 可自定义过滤条件

**Swagger UI 展示**：
- Query 大输入框
- Top K 滑块
- Alpha 滑块
- Filters JSON 编辑器
- 搜索按钮
- 结果以卡片形式展示，文本高亮 + 来源链接

---

### 3.3 跨文档统合报告模块（modules/report/）

#### API: POST /report/generate

**请求方式**：POST

**请求参数**：

```json
{
  "entity": "张三",
  "report_type": "person_profile",
  "include_sources": true,
  "max_sections": 8
}
```

**参数说明**：

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| entity | string | 是 | - | 实体名称（如"张三"、"项目X"） |
| report_type | string | 是 | - | 报告类型：person_profile\|project_summary\|sales_analysis |
| include_sources | boolean | 否 | true | 是否包含来源引用 |
| max_sections | int | 否 | 8 | 最大章节数 |

**响应示例**：

```json
{
  "title": "张三个人信息统合报告",
  "sections": [
    {
      "section": "基本信息",
      "content": "张三，男，30岁，销售部高级经理...",
      "sources": ["doc_001", "doc_005"]
    },
    {
      "section": "参与项目与数据",
      "content": "2025年Q1负责X项目，销售额增长25%...",
      "sources": ["doc_003", "doc_007"]
    }
  ],
  "overall_summary": "张三是销售部核心成员，在多个项目中表现优异...",
  "sources_count": 12,
  "generated_at": "2026-03-27T10:45:00Z"
}
```

**技术实现**：
- RAGFlow 结构化提取
- Storm 多源报告生成思路
- 跨文档实体聚合

**Swagger UI 展示**：
- Entity 输入框
- Report Type 下拉菜单
- Include Sources 复选框
- Max Sections 数字输入
- 生成按钮
- 结果页面支持折叠每个 Section
- 点击来源跳转到原始文档片段

---

### 3.4 Main Orchestrator Agent 模块（modules/orchestrator/）

#### 配置文件（config.py 或 .env）

```env
MAIN_ORCHESTRATOR=qwen_orchestrator
AVAILABLE_AGENTS=qwen_orchestrator,local_llama,deepseek_researcher
```

#### API: POST /orchestrator/run

**请求方式**：POST

**请求参数**：

```json
{
  "main_agent": "qwen_orchestrator",
  "task": "以 Qwen2.5 作为主 Agent，生成张三的所有信息报告并分析销售趋势",
  "parameters": {
    "max_steps": 10,
    "timeout": 300
  }
}
```

**参数说明**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| main_agent | string | 否 | 主Agent，默认使用 config 中的配置 |
| task | string | 是 | 自然语言任务描述 |
| parameters | object | 否 | 额外参数（最大步数、超时等） |

#### 内部调度逻辑（LangGraph StateGraph）

```
Supervisor (Main Agent)
    ↓ 解析意图
    ↓ 路由决策
    ├─→ retrieval (检索模块)
    ├─→ report (报告生成模块)
    ├─→ analysis (数据分析模块)
    ├─→ installer (工具安装模块)
    └─→ 整合结果
        ↓ 返回 trace 日志
```

**响应格式**：

1. **流式响应（SSE）**：实时显示执行日志
2. **最终结构化输出**：

```json
{
  "task_id": "task_20260327_001",
  "status": "completed",
  "trace": [
    {"step": 1, "action": "调用 retrieval 模块", "timestamp": "..."},
    {"step": 2, "action": "调用 report 模块", "timestamp": "..."}
  ],
  "result": {
    "report": {...},
    "analysis": {...}
  },
  "executed_at": "2026-03-27T10:47:30Z"
}
```

**Swagger UI 展示**：
- Main Agent 下拉选择框
- Task 大文本框
- Parameters JSON 编辑器
- 执行按钮
- 结果区显示：
  - 实时日志流（决策路径）
  - 最终结构化报告
- 支持暂停/恢复执行

---

### 3.5 GitHub 工具安装器（modules/installer/）

#### 功能说明
自动搜索 GitHub 上的开源工具，分析安全性，并在隔离环境中安装到系统中。

---

#### API 1: POST /installer/search

**请求方式**：POST

**请求参数**：

```json
{
  "query": "excel advanced analysis tool"
}
```

**响应示例**：

```json
{
  "total": 15,
  "results": [
    {
      "name": "Excel-Analysis-Tool",
      "url": "https://github.com/username/excel-analysis-tool",
      "stars": 1234,
      "description": "高级Excel数据分析工具，支持自动化处理...",
      "readme_summary": "这是一个基于Python的Excel分析工具...",
      "license": "MIT"
    }
  ]
}
```

**Swagger UI 展示**：
- Search 输入框 + 搜索按钮
- 结果表格（每行包含仓库名称、描述、星标数）
- 每行有 "Install" 按钮

---

#### API 2: POST /installer/install

**请求方式**：POST

**请求参数**：

```json
{
  "repo_url": "https://github.com/username/excel-analysis-tool",
  "confirm": true
}
```

**参数说明**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| repo_url | string | 是 | GitHub 仓库 URL |
| confirm | boolean | 是 | 必须为 true 才执行安装 |

**处理流程**：
1. 搜索仓库信息
2. 分析安全性（License、依赖、代码质量）
3. 用户确认
4. git clone 或 pip install（隔离 venv）
5. 注册为新 tool

**响应示例**：

```json
{
  "success": true,
  "tool_name": "excel_analysis_tool",
  "installed_path": "/tools/excel_analysis_tool",
  "message": "工具安装成功"
}
```

**Swagger UI 展示**：
- Repo URL 输入框
- 确认复选框（必须勾选）
- 风险提示横幅
- 安装按钮
- 安装进度条
- 安装结果显示

---

### 3.6 数据分析与文件整合模块

#### API 1: POST /analysis/execute

**请求方式**：POST

**请求参数**：

```json
{
  "task": "分析2025年各季度销售额趋势",
  "document_ids": ["doc_001", "doc_002", "doc_005"],
  "output_format": "json"
}
```

**响应示例**：

```json
{
  "task_id": "analysis_001",
  "results": {
    "summary": "2025年销售额整体呈上升趋势，Q4达到峰值...",
    "statistics": {
      "total_sales": 25000000,
      "quarterly_growth": [0.12, 0.15, 0.20, 0.25]
    },
    "chart_description": "折线图显示Q1到Q4销售额持续增长"
  }
}
```

---

#### API 2: POST /integration/merge

**请求方式**：POST

**请求参数**：

```json
{
  "document_ids": ["doc_001", "doc_002"],
  "rule": {
    "strategy": "concatenate",
    "format": "markdown"
  }
}
```

**响应示例**：

```json
{
  "merged_content": "# 合并文档\n\n## 文档1\n...\n\n## 文档2\n...",
  "total_length": 5420,
  "source_count": 2
}
```

---

### 3.7 AI 工具接入通用接口

#### API: GET /tools

**请求方式**：GET

**响应示例**：

```json
{
  "tools": [
    {
      "name": "retrieval_search",
      "description": "在知识库中进行智能检索",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "top_k": {"type": "integer"}
        }
      }
    },
    {
      "name": "report_generate",
      "description": "生成跨文档统合报告",
      "parameters": {
        "type": "object",
        "properties": {
          "entity": {"type": "string"},
          "report_type": {"type": "string"}
        }
      }
    }
  ]
}
```

**功能说明**：
- 返回所有工具的 OpenAI-style function calling schema
- 供 Cursor、Claude Code 等 AI 工具直接调用
- 支持动态注册新工具（通过 installer 模块）

---

## 4. 非功能需求

### 4.1 性能要求

- **异步处理**：大文件与报告生成采用异步任务队列
- **流式响应**：长耗时操作支持 SSE 流式返回
- **响应时间**：
  - 简单查询：< 2s
  - 文档上传：< 5s（开始处理）
  - 报告生成：< 30s（中等复杂度）

### 4.2 可用性要求

- **统一错误格式**：

```json
{
  "error": {
    "code": "ERR_001",
    "message": "文档解析失败",
    "details": "PDF 文件加密，无法提取内容"
  }
}
```

- **详细日志 trace**：每个请求附带 trace_id，便于追踪问题

### 4.3 安全要求

- **文件沙箱**：上传文件隔离存储
- **安装确认**：工具安装必须用户明确确认
- **API 限流**：防止滥用，限制每个 IP 的请求频率
- **权限控制**：team_id 隔离，防止跨团队访问

### 4.4 可维护性要求

- **模块化设计**：每个功能模块独立，便于替换升级
- **文档完善**：Swagger UI 自动生成，代码注释充分
- **日志规范**：结构化日志，便于分析和监控

---

## 5. 开发路线图（AI 驱动）

### 阶段 1：骨架 + orchestrator（Week 1-2）

- [ ] 搭建 FastAPI 项目骨架
- [ ] 配置 Docker Compose 环境
- [ ] 实现 Main Orchestrator Agent（LangGraph StateGraph）
- [ ] 集成 Ollama 本地模型
- [ ] 基础 Swagger UI 文档

### 阶段 2：ingestion（Week 2-3）

- [ ] 集成 RAGFlow 解析器
- [ ] 集成 Docling 解析器
- [ ] 实现 /ingestion/upload 接口
- [ ] 实现 /ingestion/documents 接口
- [ ] 实现文件删除功能
- [ ] Chroma 向量存储集成

### 阶段 3：retrieval + report（Week 3-4）

- [ ] 集成 LlamaIndex 检索框架
- [ ] 实现 /retrieval/search 接口
- [ ] 实现混合检索（向量 + 关键词）
- [ ] 集成 Storm 报告生成思路
- [ ] 实现 /report/generate 接口
- [ ] 跨文档实体聚合逻辑

### 阶段 4：installer + analysis（Week 4-5）

- [ ] 实现 /installer/search 接口
- [ ] 实现 /installer/install 接口
- [ ] 实现隔离环境安装
- [ ] 实现 /analysis/execute 接口
- [ ] 实现 /integration/merge 接口

### 阶段 5：测试、tools schema、Docker、README（Week 5-6）

- [ ] 单元测试 + 集成测试
- [ ] 实现 /tools 接口
- [ ] 优化 Docker Compose 配置
- [ ] 编写完整 README
- [ ] 准备 GitHub 开源

**预期里程碑**：
- Week 2：MVP 骨架可运行
- Week 4：核心功能可用
- Week 6：完整功能 + 开源准备

---

## 6. 集成开源项目列表

以下是本项目深度集成的开源项目（仅提取核心逻辑，重构适配本项目栈，并在 README 中注明来源）：

### 6.1 文档解析与理解

| 项目 | 核心能力 | GitHub | 集成用途 |
|------|---------|--------|---------|
| **RAGFlow** | 深度文档理解、表格提取、Agentic RAG | https://github.com/infiniflow/ragflow | 智能文档解析、表格识别 |
| **Docling** | 先进 PDF/Office 文档解析（布局、表格、公式、OCR） | https://github.com/docling-project/docling | PDF 深度解析 |
| **MinerU** | 复杂 PDF 转 Markdown/JSON | https://github.com/opendatalab/mineru | 复杂文档高质量提取 |
| **RAG-Anything** | 多模态统一 RAG 处理框架 | https://github.com/HKUDS/RAG-Anything | 多模态内容处理 |

### 6.2 RAG 基础与检索

| 项目 | 核心能力 | GitHub | 集成用途 |
|------|---------|--------|---------|
| **LlamaIndex** | RAG 核心框架（Loader、索引、Retriever、混合搜索） | https://github.com/run-llama/llama_index | 混合检索、向量索引 |

### 6.3 Agent 编排与调度

| 项目 | 核心能力 | GitHub | 集成用途 |
|------|---------|--------|---------|
| **LangGraph** | 状态化 Agent 编排框架（Supervisor/Orchestrator 模式） | https://github.com/langchain-ai/langgraph | Main Agent 调度逻辑 |
| **CrewAI** | 多角色 Agent 协作 | - | 角色参考 |

### 6.4 报告生成

| 项目 | 核心能力 | GitHub | 集成用途 |
|------|---------|--------|---------|
| **RAGFlow** | 结构化提取 | https://github.com/infiniflow/ragflow | 报告结构化内容提取 |
| **Storm** | LLM 驱动的多源长报告生成 | https://github.com/stanford-oval/storm | 报告生成思路参考 |

---

## 7. 集成原则

1. **仅参考必要代码**：提取核心逻辑，重构为本项目模块化结构
2. **避免 License 冲突**：确保使用的代码符合相应开源协议
3. **注明来源**：在 README 中列出感谢与链接
4. **适配本栈**：根据项目技术栈进行适配改造
5. **保持独立**：每个开源项目的能力独立封装，便于替换升级

---

## 附录 A：技术选型对比

| 组件 | 候选方案 | 最终选择 | 选择理由 |
|------|---------|---------|---------|
| Web 框架 | FastAPI / Flask / Django | FastAPI | 性能高、自动生成文档、异步支持 |
| 向量数据库 | Chroma / Pinecone / Milvus | Chroma | 本地部署简单、开源免费 |
| Agent 框架 | LangGraph / LangChain / CrewAI | LangGraph | 状态化编排、适合复杂流程 |
| 文档解析 | RAGFlow / Docling / Unstructured | 多选互补 | 不同项目擅长不同格式 |

---

## 附录 B：API 速查表

| API | 方法 | 功能 |
|-----|------|------|
| `/ingestion/upload` | POST | 上传并解析文档 |
| `/ingestion/documents` | GET | 获取文档列表 |
| `/ingestion/{document_id}` | DELETE | 删除文档 |
| `/retrieval/search` | POST | 智能检索 |
| `/report/generate` | POST | 生成统合报告 |
| `/orchestrator/run` | POST | 执行 Agent 任务 |
| `/installer/search` | POST | 搜索 GitHub 工具 |
| `/installer/install` | POST | 安装工具 |
| `/analysis/execute` | POST | 执行数据分析 |
| `/integration/merge` | POST | 合并文档 |
| `/tools` | GET | 获取工具列表 |

---

## 附录 C：错误码定义

| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| ERR_001 | 文档解析失败 | 检查文件格式是否支持 |
| ERR_002 | 向量存储失败 | 检查 Chroma 服务是否运行 |
| ERR_003 | 检索无结果 | 尝试调整查询词或参数 |
| ERR_004 | Agent 超时 | 检查任务复杂度或增加超时时间 |
| ERR_005 | 工具安装失败 | 检查网络连接或依赖兼容性 |

---

**文档版本历史**

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|---------|
| v1.0 | 2026-03-20 | 作者 | 初始版本 |
| v1.1 | 2026-03-24 | 作者 | 增加 installer 模块 |
| v1.2 | 2026-03-27 | 作者 | 细化 API 接口和 Swagger UI 交互细节 |

---

**版权声明**

本项目采用 MIT 协议开源，欢迎贡献代码。集成开源项目的核心能力时，请遵守对应项目的 License 要求。
