# DocuFlow-AI

将软件需求文档转换为结构化设计文档的 AI 系统。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## 环境配置

创建 `.env` 文件：

```env
DOCUFLOW_AZURE_OPENAI_API_KEY=你的API密钥
DOCUFLOW_MODEL_NAME=deepseek-v3.2

# GPT5.2 部署
GPT5.2_AZURE_OPENAI_ENDPOINT=https://xxxx.openai.azure.com/
GPT5.2_AZURE_OPENAI_DEPLOYMENT=gpt-5.2
GPT5.2_AZURE_OPENAI_API_VERSION=2025-04-01-preview

# GPT5.1 部署
GPT5.1_AZURE_OPENAI_ENDPOINT=https://xxxx.openai.azure.com/
GPT5.1_AZURE_OPENAI_DEPLOYMENT=gpt-5.1-codex-max
GPT5.1_AZURE_OPENAI_API_VERSION=2025-04-01-preview

# DeepSeek 部署
DeepSeek-V3.2_AZURE_OPENAI_ENDPOINT=https://xxxx.services.ai.azure.com
DeepSeek-V3.2_AZURE_OPENAI_DEPLOYMENT=DeepSeek-V3.2
DeepSeek-V3.2_AZURE_OPENAI_API_VERSION=2024-05-01-preview

# 设计批判（可选）
DOCUFLOW_CRITIQUE_ENABLED=true
DOCUFLOW_CRITIQUE_THRESHOLD=0.7
DOCUFLOW_CRITIQUE_MAX_ITERATIONS=2
DOCUFLOW_CRITIQUE_MODEL=             # 批判使用的模型（可选，留空则使用主模型）
                                     # 可选值: gpt-5.2, gpt-5.1, deepseek-v3.2
```

## CLI 使用

### 一键运行

```powershell
docuflow all -p 天财分账需求 -m gpt-5.2
```

### 分步执行

```powershell
# 阶段1：初始化（术语表、架构DAG）
docuflow init -p 天财分账需求 -m gpt-5.2

# 阶段2：生成模块设计
docuflow run -p 天财分账需求

# 阶段3：系统概述
docuflow overview -p 天财分账需求

# 阶段4：组装最终文档
docuflow assemble -p 天财分账需求
```

### 常用命令

```powershell
# 查看进度
docuflow status -p 天财分账需求

# 查看可用模型
docuflow models

# 重置模块状态
docuflow reset -p 天财分账需求 --module 认证系统
docuflow reset -p 天财分账需求 --all

# 逐步模式（每个模块后暂停）
docuflow run -p 天财分账需求 --step
```

## API 服务

```powershell
# 启动服务
docuflow-api

# 访问文档
# http://localhost:8000/docs
```

### 主要端点

| 端点 | 说明 |
|------|------|
| `POST /api/v1/projects` | 创建项目 |
| `GET /api/v1/projects` | 获取项目列表 |
| `POST /api/v1/projects/{id}/tasks` | 创建并启动任务 |
| `GET /api/v1/projects/{id}/modules` | 获取模块内容 |
| `WS /api/v1/ws` | 实时任务进度 |

## 输出目录

```
data/<项目名>/<模型名>/
├── workspace/
│   ├── 01_global/          # 术语表、系统设计、接口设计
│   └── 02_modules/         # 各模块设计文档
└── output/
    └── final_design_document.md
```

## 目录结构

```
docuflow/
├── api/              # FastAPI 接口
├── cli/              # 命令行工具
├── core/             # 核心配置与模型
├── graph/            # LangGraph 工作流
├── llm/              # LLM 客户端
├── parsers/          # 文档解析器
└── utils/            # 工具函数
```
