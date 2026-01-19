# DocuFlow-AI 快速使用

简要说明如何运行本工具将需求文档转为结构化设计文档。

## 安装
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## 准备输入
- 将需求文档放在 `data/input/<项目名>/`（示例：`data/input/天财分账需求/`）。
- 运行前确保已设置 Azure OpenAI 相关环境变量或 `.env`（需有密钥与模型配置）。

## 一键使用（推荐）
```powershell
docuflow all -p 天财分账需求 -m gpt-5.2
```

注意：也可使用 `python -m docuflow` 方式运行；不支持 `--langgraph` 参数。

## 分步使用
```powershell
# 阶段 1：初始化（术语表、架构 DAG）
docuflow init -p 天财分账需求 -m gpt-5.2

# 阶段 2：生成模块设计（可逐步）
docuflow run -p 天财分账需求
# 逐步模式：
docuflow run -p 天财分账需求 --step

# 阶段 3：系统概述
docuflow overview -p 天财分账需求

# 阶段 4：组装最终文档
docuflow assemble -p 天财分账需求
```

## 常用
```powershell
# 查看进度
docuflow status -p 天财分账需求

# 查看可用模型
docuflow models
```

# DocuFlow-AI 使用说明

将需求文档转换为结构化设计文档的简易流程说明。本项目提供命令行工具，按“初始化 → 模块生成 → 系统概述 → 组装成品”的阶段输出设计材料。

## 环境要求
- Python >= 3.11（建议使用虚拟环境）
- 已配置 Azure OpenAI（仅支持 Azure OpenAI）

## 安装
在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## 环境变量与 .env
在项目根目录创建 `.env`（或以系统环境变量方式注入）：

```env
# 通用
DOCUFLOW_AZURE_OPENAI_API_KEY=你的AzureOpenAI密钥
DOCUFLOW_MODEL_NAME=gpt-5.2  # 可选: gpt-5.1, deepseek-v3.2

# 选择 gpt-5.2 时需要：
GPT5.2_AZURE_OPENAI_ENDPOINT=https://xxxx.openai.azure.com/
GPT5.2_AZURE_OPENAI_DEPLOYMENT=你的部署名
GPT5.2_AZURE_OPENAI_API_VERSION=2024-xx-xx

# 若使用 gpt-5.1：
# GPT5.1_AZURE_OPENAI_ENDPOINT=...
# GPT5.1_AZURE_OPENAI_DEPLOYMENT=...
# GPT5.1_AZURE_OPENAI_API_VERSION=...

# 若使用 deepseek-v3.2：
# DeepSeek-V3.2_AZURE_OPENAI_ENDPOINT=...
# DeepSeek-V3.2_AZURE_OPENAI_DEPLOYMENT=...
# DeepSeek-V3.2_AZURE_OPENAI_API_VERSION=...
```

说明：`DOCUFLOW_*` 为通用配置；模型专属的 `*_AZURE_OPENAI_*` 变量不带 `DOCUFLOW_` 前缀。

## 目录约定
- 输入文档：`data/input/<项目名>/`（例如将需求文档放在 `data/input/天财分账需求/`）
- 工作与输出：`data/<项目名>/<模型名>/{workspace,output}/`

生成后的关键文件位置示例：
- 术语表与拓扑：`data/<项目名>/<模型名>/workspace/01_global/`
- 模块设计：`data/<项目名>/<模型名>/workspace/02_modules/`
- 最终成品：`data/<项目名>/<模型名>/output/final_design_document.md`

## 快速开始
两种调用方式均可：`docuflow ...` 或 `python -m docuflow ...`

1) 初始化（生成术语表与架构 DAG）
```powershell
docuflow init -p 天财分账需求 -m gpt-5.2
# 或
python -m docuflow init -p 天财分账需求 -m gpt-5.2
```

2) 生成模块设计（按依赖拓扑顺序）
```powershell
docuflow run -p 天财分账需求
# 逐步模式（每个模块后暂停）：
docuflow run -p 天财分账需求 --step
```

3) 生成系统概述
```powershell
docuflow overview -p 天财分账需求
```

4) 组装最终文档
```powershell
docuflow assemble -p 天财分账需求
```

一键全流程：
```powershell
docuflow all -p 天财分账需求 -m gpt-5.2
```

或使用：
```powershell
python -m docuflow all -p 天财分账需求 -m gpt-5.2
```

## 常用辅助命令
- 查看项目进度：
```powershell
docuflow status -p 天财分账需求
```

- 列出可用模型与默认模型：
```powershell
docuflow models
```

- 列出已存在的项目（根据 `data/input/` 与输出目录）：
```powershell
docuflow list-projects
```

- 重置模块状态（失败或需重跑时）：
```powershell
# 重置指定模块
docuflow reset -p 天财分账需求 --module 认证系统

# 重置所有模块
docuflow reset -p 天财分账需求 --all
```

## 疑难排查
- 使用方式：推荐直接使用 `docuflow ...`（通过 `pip install -e .` 安装后会注册命令）；未安装脚本或想直接运行模块时，请使用 `python -m docuflow ...`。不要使用 `python docuflow ...`。
- 参数支持：当前不支持 `--langgraph` 参数；如出现“未识别的选项”或退出码 1，请移除该参数并重试。
- Python 版本：需 Python >= 3.11。若虚拟环境未激活，先执行 `\.venv\Scripts\Activate.ps1`。
- 环境变量：确保 `.env` 或系统环境变量已配置 `DOCUFLOW_AZURE_OPENAI_API_KEY` 以及所选模型对应的 `*_AZURE_OPENAI_*`。
- 目录结构：输入文档需位于 `data/input/<项目名>/`，例如 `data/input/天财分账需求/`；运行后输出在 `data/<项目名>/<模型名>/`。
- 查看帮助：`docuflow --help` 或查看子命令帮助，如 `docuflow run --help`。

