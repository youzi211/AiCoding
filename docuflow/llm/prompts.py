
# """
# 统一管理所有 LLM 提示词模板
# """

# # 内容大小限制
# MAX_DOCUMENT_SIZE = 80000
# MAX_MODULE_SIZE = 20000

# # ============================================================
# # System prompts (global behavior constraints)
# # ============================================================

# # For JSON-only tasks: glossary / dag / summary / critique
# JSON_SYSTEM_PROMPT = """You are DocuFlow's structured data generator. Output exactly one JSON object.
# Rules:
# 1) Output JSON only. No Markdown. No code fences. No extra text.
# 2) Strict JSON: double quotes, no trailing commas, no comments, correct types.
# 3) Do not invent: if information is missing, use empty arrays/empty strings/null.
# 4) Consistency: keep names consistent; references must exist (e.g., dependencies must reference modules[].name).
# 5) Self-check before output: the JSON must be parseable and match the required schema.
# """

# # For Markdown-only tasks: module/system/interface/database design
# MARKDOWN_SYSTEM_PROMPT = """You are DocuFlow's design document generator. Output Markdown only (Mermaid code blocks allowed).
# Rules:
# 1) Follow the required section order and keep headings well-structured.
# 2) If information is missing, write TBD; do not invent APIs, fields, tables, or dependencies.
# 3) Mermaid must render: valid syntax, no extra noise that breaks diagrams.
# 4) Keep terminology consistent with upstream modules and the glossary.
# 5) Self-check before output: no contradictions, no duplicate sections, no unrelated chatter.
# """

# # ============================================================
# # 术语表提取
# # ============================================================

# GLOSSARY_PROMPT = """你是一位资深的技术分析师，正在从软件需求文档中提取关键术语。

# 请分析以下文档内容，提取：
# 1. 业务实体（例如：用户、订单、账户）
# 2. 领域特定的技术术语
# 3. 系统中的角色和参与者
# 4. 关键流程和工作流

# 对于每个术语，请提供：
# - 术语名称
# - 清晰的定义
# - 分类（业务实体、角色、流程、技术术语）
# - 任何别名或替代名称

# 文档内容：
# {document_content}

# 请以以下 JSON 格式回复：
# {{
#   "entries": [
#     {{
#       "term": "术语名称",
#       "definition": "清晰的定义",
#       "category": "分类",
#       "aliases": ["别名1", "别名2"]
#     }}
#   ]
# }}
# """

# # ============================================================
# # DAG 生成
# # ============================================================

# DAG_PROMPT = """你是一位资深的软件架构师，正在分析需求文档以识别系统模块及其依赖关系。

# 根据以下需求文档和术语表，请识别：
# 1. 不同的功能模块/子系统
# 2. 模块之间的依赖关系（哪个模块必须在另一个之前设计）

# 识别依赖关系的指导原则：
# - 如果模块 B 使用模块 A 的数据或接口，则 B 依赖于 A
# - 如果模块 B 需要模块 A 正常运行，则 B 依赖于 A
# - 避免循环依赖
# - 首先识别基础模块（没有依赖的模块）

# 术语表参考：
# {glossary}

# 需求文档：
# {document_content}

# 请以以下 JSON 格式回复：
# {{
#   "modules": [
#     {{
#       "name": "模块名称",
#       "description": "简要描述",
#       "dependencies": ["依赖1", "依赖2"]
#     }}
#   ]
# }}

# 重要：确保依赖图是无环的（DAG）。dependencies 中的每个模块名称必须存在于 modules 列表中。
# """

# # ============================================================
# # 模块设计
# # ============================================================

# MODULE_DESIGN_PROMPT = """你是一位资深的软件架构师，正在创建详细的设计文档。

# 请基于以下上下文，设计 "{module_name}" 模块。

# === 上下文 ===
# {context}

# === 设计要求 ===
# 请设计一份全面的模块规格说明，包括：

# 1. **概述**：本模块的目的和范围
# 2. **接口设计**：
#    - API 端点（REST/GraphQL）
#    - 输入/输出数据结构
#    - 发布/消费的事件
# 3. **数据模型**：
#    - 数据库表/集合设计
#    - 与其他模块的关系
# 4. **业务逻辑**：
#    - 核心算法
#    - 业务规则
#    - 验证逻辑
# 5. **时序图**：关键工作流（使用 Mermaid 格式）
# 6. **错误处理**：预期错误及处理策略
# 7. **依赖说明**：本模块如何与上游模块交互

# 请以 Markdown 格式输出设计文档，包含清晰的章节和 Mermaid 图表（Mermaid中不要加注释，会导致报错）。
# """

# # ============================================================
# # 模块摘要提取
# # ============================================================

# MODULE_SUMMARY_PROMPT = """请从以下模块设计文档中提取关键摘要信息。

# 模块名称（必须使用该名称，不要改写）：{module_name}

# 模块设计文档：
# {module_content}

# 请以以下 JSON 格式输出摘要：
# {{
#   "module_name": "模块名称",
#   "purpose": "模块职责（一句话描述）",
#   "interfaces": [
#     {{"method": "GET/POST", "path": "/api/xxx", "description": "接口说明"}}
#   ],
#   "database_tables": [
#     {{"name": "表名", "description": "表说明"}}
#   ],
#   "dependencies": ["依赖的模块名"],
#   "key_features": ["核心功能点1", "核心功能点2"]
# }}

# 注意：只提取关键信息，保持简洁。
# """

# # ============================================================
# # 系统设计
# # ============================================================

# SYSTEM_DESIGN_PROMPT = """你是一位资深的软件架构师，请基于以下所有模块的摘要信息，生成系统级设计文档。

# === 需求文档（节选）===
# {requirements_excerpt}

# === 术语表（节选）===
# {glossary_excerpt}

# === 模块依赖（DAG 概览）===
# {dag_overview}

# === 模块摘要列表 ===
# {module_summaries}

# === 要求 ===
# 请生成以下内容（使用 Markdown 格式，图表使用 Mermaid）：

# 重要格式约束：
# 1) 不要输出任何顶层标题（不要使用 `# ...`）。直接从 `## 2.1 ...` 开始。
# 2) Mermaid 必须使用 ASCII 引号（"或 '），不要使用中文引号（“ ” ‘ ’）。
# 3) 严格基于输入信息；缺失写 TBD，不要编造 API/字段/表/依赖。

# ## 2.1 系统结构
# 描述整体系统架构，包含系统架构图（使用 Mermaid C4 或 flowchart）。

# ## 2.2 功能结构
# 描述系统的功能模块划分，包含功能结构图。

# ## 2.3 网络拓扑图
# 描述系统部署的网络拓扑结构（如适用）。

# ## 2.4 数据流转
# 描述系统中数据如何在各模块间流转，包含数据流图。

# ## 2.5 系统模块交互关系
# 描述各模块之间的调用和依赖关系，包含模块交互图。

# 请确保：
# 1. 图表使用 Mermaid 格式（不要添加注释会导致报错）
# 2. 内容基于实际的模块摘要信息
# 3. 描述清晰、专业
# """

# # ============================================================
# # 接口汇总
# # ============================================================

# INTERFACE_PROMPT = """请基于以下所有模块的摘要信息，生成统一的接口设计章节。

# === 需求文档（节选）===
# {requirements_excerpt}

# === 术语表（节选）===
# {glossary_excerpt}

# === 模块依赖（DAG 概览）===
# {dag_overview}

# === 模块摘要列表 ===
# {module_summaries}

# === 要求 ===
# 请生成以下内容（使用 Markdown 格式）：

# 重要格式约束：
# 1) 不要输出任何顶层标题（不要使用 `# ...`）。直接从 `## 4.1 ...` 开始。
# 2) 严格基于输入信息；缺失写 TBD，不要编造接口路径、字段或模块依赖。

# ## 4.1 对外接口
# 列出系统对外暴露的所有 API 接口，按功能分类。

# ## 4.2 模块间接口
# 列出模块之间的内部调用接口。

# 对于每个接口，请说明：
# - 接口路径和方法
# - 所属模块
# - 功能说明
# - 请求/响应格式（如已知）
# 使用 Markdown 表格格式展示。
# """

# # ============================================================
# # 数据库汇总
# # ============================================================

# DATABASE_PROMPT = """请基于以下所有模块的摘要信息，生成统一的数据库设计章节。

# === 需求文档（节选）===
# {requirements_excerpt}

# === 术语表（节选）===
# {glossary_excerpt}

# === 模块依赖（DAG 概览）===
# {dag_overview}

# === 模块摘要列表 ===
# {module_summaries}

# === 要求 ===
# 请生成以下内容（使用 Markdown 格式，图表使用 Mermaid）：

# 重要格式约束：
# 1) 不要输出任何顶层标题（不要使用 `# ...`）。直接从 `## 5.1 ...` 开始。
# 2) Mermaid 必须使用 ASCII 引号（" 或 '），不要使用中文引号（“ ” ‘ ’）。
# 3) 严格基于输入信息；缺失写 TBD，不要编造表/字段/关系。

# ## 5.1 ER图
# 使用 Mermaid erDiagram 格式绘制实体关系图。

# ## 5.2 表结构
# 列出所有数据库表，包含：
# - 表名
# - 所属模块
# - 主要字段说明
# - 与其他表的关系
# 使用 Markdown 表格格式展示。
# """

# # ============================================================
# # 模块设计批判
# # ============================================================

# CRITIQUE_PROMPT = """你是一位严格的技术评审专家，正在评估模块设计文档的质量。

# 模块名称: {module_name}

# 模块设计:
# {module_design}

# 上下文:
# {context}

# 【重要评分标准 - 请严格遵循】
# 你需要像一个挑剔的技术负责人一样进行评审，不要过度宽容。请从以下维度严格评估：

# 1. **完整性** (权重: 25%):
#    - 必须包含: 概述、接口设计、数据模型、业务逻辑、错误处理
#    - 缺少任何章节扣 0.2 分
#    - 内容空洞（只有标题没有实质）每处扣 0.1 分

# 2. **一致性** (权重: 20%):
#    - 必须与上游模块接口保持一致
#    - 必须使用术语表中的标准术语
#    - 发现不一致每处扣 0.15 分

# 3. **可行性** (权重: 25%):
#    - 设计是否技术上可行
#    - 是否考虑了边界情况和异常处理
#    - 缺少关键逻辑考虑扣 0.2 分

# 4. **清晰度** (权重: 15%):
#    - 描述是否清晰易懂
#    - 结构是否合理
#    - 存在模糊或矛盾描述每处扣 0.1 分

# 5. **图规范性** (权重: 15%):
#    - Mermaid 图表必须能正确渲染
#    - 图表必须包含在 ```mermaid 代码块中
#    - 图表中有注释会导致渲染失败，这是一个严重问题
#    - 缺少必要的图表或图表错误扣 0.2 分

# 【评分规则】
# - 起始分数: 1.0
# - 根据上述扣分标准累计扣分
# - 最终分数 = 1.0 - 累计扣分（最低 0.0）
# - 90分以上(0.9+)才算优秀，80分(0.8)算良好，低于{threshold:.0f}分即为不合格

# 【通过标准】
# - 分数 >= {threshold} 且 passed = true
# - 分数 < {threshold} 且 passed = false

# 请以以下 JSON 格式输出评审结果（不要用Markdown代码块包裹）：
# {{
#   "passed": true/false,
#   "score": 0.0-1.0的小数,
#   "issues": ["具体问题描述1", "具体问题描述2"],
#   "suggestions": "具体的改进建议，针对发现的问题给出如何修改的指导"
# }}

# 【特别注意】
# - 要像一个严格的代码审查者，不要因为"看起来差不多"就给高分
# - 如果内容有明显缺失或错误，分数应该低于 0.7
# - 要在 issues 中列出所有发现的具体问题
# """

# # ============================================================
# # 根据批判反馈重新生成
# # ============================================================

# REGENERATE_PROMPT = """你是一位资深的软件架构师，正在根据严格的评审反馈改进模块设计。

# 模块名称: {module_name}

# 当前设计（有问题的版本）:
# {current_design}

# 评审反馈（必须认真对待每一条）:
# - 评分: {score} (满分1.0，{threshold}为合格线)
# - 发现的问题: {issues}
# - 改进建议: {suggestions}

# 上下文:
# {context}

# 【改进要求】
# 1. **逐一解决问题**: 针对上面列出的每个问题，必须在改进版本中明确解决
# 2. **图表规范**: 确保所有 Mermaid 图表符合规范
#    - 必须使用 ```mermaid 代码块包裹
#    - 图表内部不要添加注释（%% 或 //），这会导致渲染失败
#    - 使用标准语法，确保图表可以正确渲染
# 3. **内容完整**: 确保包含所有必要章节（概述、接口设计、数据模型、业务逻辑、错误处理）
# 4. **保持一致**: 使用术语表中的标准术语，与上游模块保持接口一致
# 5. **实质内容**: 每个章节都要有实质性内容，不要只有空洞的标题

# 请输出改进后的完整模块设计文档（Markdown 格式）。

# 【检查清单】
# 在输出前，请确认：
# - [ ] 所有反馈中的问题都已解决
# - [ ] 所有 Mermaid 图表规范且无注释
# - [ ] 所有必要章节都完整且有实质内容
# - [ ] 与上游模块和术语表保持一致
# """
"""
统一管理所有 LLM 提示词模板（优化版）
核心优化点：
- 控制指令（格式约束/不可编造/输出限制）统一用英文 + 列表化，模型更“听话”
- 规则前置：STRICT RULES / INPUT / TASK 物理分隔，降低认知负载
- 明确违规后果：If any rule is violated, the output is INVALID
"""

# 内容大小限制
MAX_DOCUMENT_SIZE = 80000
MAX_MODULE_SIZE = 20000
# ============================================================
# System prompts (global behavior constraints)
# ============================================================

# For JSON-only tasks: glossary / dag / summary / critique
JSON_SYSTEM_PROMPT = """You are DocuFlow's structured data generator.
You MUST output exactly ONE valid JSON object and NOTHING else.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
1) Output JSON only. No Markdown. No code fences. No extra text.

2) Strict JSON syntax (RFC 8259):
   - Use double quotes for all keys and string values
   - No trailing commas
   - No comments
   - Correct value types (string / number / boolean / null / array / object)

3) String safety rules (CRITICAL):
   - Do NOT use unescaped double quotes " inside string values.
   - If emphasis is needed, use single quotes '...' or parentheses （...） instead.
   - Never produce invalid JSON due to quoting.

4) Do NOT invent facts, names, APIs, fields, tables, or dependencies.
   - If information is missing or uncertain, use empty strings, empty arrays, or null.

5) Keep names consistent across the entire output.
   - References must exist (e.g., dependencies must reference modules[].name).

6) Self-check before output:
   - The JSON must be parseable
   - The JSON must strictly match the output format/schema provided by the user
   - If any rule would be violated, simplify the content but keep JSON valid

If any rule is violated, the output is INVALID.
"""

# For Markdown-only tasks: module/system/interface/database design
MARKDOWN_SYSTEM_PROMPT = """You are DocuFlow's design document generator.
You MUST output Markdown only (Mermaid code blocks allowed).

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
1) Output Markdown only. No JSON. No extra explanations outside Markdown.

2) MANDATORY INFERENCE (CRITICAL - READ CAREFULLY):
   You are a SENIOR SOFTWARE ARCHITECT. Your job is to DESIGN, not just transcribe.
   - You MUST infer and design: API endpoints, request/response structures, database tables, fields, business logic, error handling, workflows.
   - Base your inference on: requirements context, industry best practices, standard architecture patterns, upstream module designs.
   - "TBD" is STRICTLY FORBIDDEN for any designable content.
   - "TBD" is ONLY allowed for: deployment-specific info (IP addresses, server hostnames, port numbers, credentials, environment-specific configs).
   - If you use "TBD" for APIs, fields, tables, logic, or workflows, the output is INVALID and will be rejected.
   - When inferring, use common naming conventions (e.g., RESTful paths, standard HTTP methods, typical field names like id, created_at, updated_at).

3) Mermaid diagrams must render:
   - Must be inside ```mermaid code blocks
   - Must NOT contain any comments (%% or //)
   - Use valid Mermaid syntax
   - Use ASCII quotes (" or ') only (never Chinese quotes " " ' ')

4) Keep terminology consistent with the glossary and upstream modules.

5) Self-check before output:
   - No contradictions
   - No duplicate/empty sections
   - No unrelated content
   - No lazy "TBD" for designable content

If any rule is violated, the output is INVALID.
"""
# ============================================================
# 术语表提取 (JSON)
# ============================================================

GLOSSARY_PROMPT = """You are a senior technical analyst.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
- Output JSON only (no Markdown, no code fences).
- Do NOT invent terms. Extract from the document only.
- If a field is unknown, use empty string / empty array.
- Keep naming consistent.
- Output must match the required JSON schema.
If any rule is violated, the output is INVALID.

=====================
INPUT DOCUMENT
=====================
{document_content}

=====================
TASK
=====================
从需求文档中提取“关键术语表”，包括但不限于：
1) 业务实体（例如：用户、订单、账户）
2) 领域特定术语（业务/技术）
3) 系统角色/参与者
4) 关键流程/工作流名称

对每个术语提供：
- term：术语名称
- definition：清晰定义（1~2句）
- category：分类（业务实体/角色/流程/技术术语）
- aliases：别名（如无则 []）

Return EXACTLY this JSON schema:
{{
  "entries": [
    {{
      "term": "术语名称",
      "definition": "清晰的定义",
      "category": "分类",
      "aliases": ["别名1", "别名2"]
    }}
  ]
}}
"""

# ============================================================
# DAG 生成 (JSON)
# ============================================================

DAG_PROMPT = """You are a senior software architect.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
- Output JSON only (no Markdown, no code fences).
- Do NOT invent modules or dependencies. Infer ONLY from the document.
- The dependency graph MUST be acyclic (a DAG). Avoid cycles.
- dependencies[] must reference existing modules[].name.
- If unsure, keep dependencies empty [] rather than guessing.
If any rule is violated, the output is INVALID.

=====================
INPUT
=====================
[Glossary]
{glossary}

[Requirements Document]
{document_content}

=====================
TASK
=====================
基于需求文档与术语表，识别系统的功能模块/子系统，并给出模块之间的依赖关系。

依赖识别原则：
- 如果模块 B 使用模块 A 的数据或接口，则 B 依赖 A
- 如果模块 B 需要模块 A 正常运行，则 B 依赖 A
- 避免循环依赖
- 优先识别基础模块（无依赖）

Return EXACTLY this JSON schema:
{{
  "modules": [
    {{
      "name": "模块名称",
      "description": "简要描述",
      "dependencies": ["依赖1", "依赖2"]
    }}
  ]
}}
"""
# ============================================================
# 模块设计 (Markdown)
# ============================================================

MODULE_DESIGN_PROMPT = """You are a senior software architect.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
1) Output Markdown only.

2) MANDATORY DESIGN (NO "TBD" ALLOWED):
   - You MUST design complete APIs, data models, and business logic based on the requirements.
   - Infer technical details using: industry best practices, RESTful conventions, standard patterns.
   - "TBD" is FORBIDDEN. If you write "TBD" for any API, field, table, or logic, the output is INVALID.
   - Use standard naming: RESTful paths (/api/v1/resource), common fields (id, created_at, updated_at, status).

3) Mermaid diagrams:
   - Must be inside ```mermaid code blocks
   - Must NOT include comments (%% or //)
   - Must render correctly

4) Keep terminology consistent with the provided context.

5) ALL section titles MUST be in Chinese. Do NOT use English section titles.

If any rule is violated, the output is INVALID.

=====================
CONTEXT
=====================
{context}

=====================
TASK
=====================
为模块 "{module_name}" 编写完整的设计文档。

你必须根据需求上下文推断并设计所有技术细节，包括但不限于：API路径、请求响应结构、数据库表字段、业务规则。

文档必须包含以下章节（保持顺序，章节标题必须使用中文）：

## 1. 概述
- **目的与范围**: 描述本模块的核心职责和边界

## 2. 接口设计
- **API端点**: 必须设计具体的 RESTful API（方法、路径、描述）
- **请求/响应结构**: 必须定义 JSON 结构（字段名、类型、是否必填）
- **发布/消费的事件**: 如有异步通信需求

## 3. 数据模型
- **表/集合**: 必须设计具体的数据库表
- **关键字段**: 必须列出字段名、类型、约束（主键、外键、索引等）
- **与其他模块的关系**: 数据关联（一对多、多对多等）

## 4. 业务逻辑
- **核心工作流/算法**: 主要业务流程的详细步骤
- **业务规则与验证**: 具体的校验规则（如：密码长度>=8）
- **关键边界情况处理**: 异常场景及处理方式

## 5. 时序图
- 至少包含一个关键工作流的 Mermaid sequenceDiagram

## 6. 错误处理
- **预期错误情况**: 具体的错误类型和错误码
- **处理策略**: 返回什么响应、是否重试、是否告警

## 7. 依赖关系
- **上游模块**: 本模块调用哪些模块的接口
- **下游模块**: 哪些模块会调用本模块

输出完整的 Markdown 模块设计文档。
"""
# ============================================================
# 模块摘要提取 (JSON)
# ============================================================

MODULE_SUMMARY_PROMPT = """You are a structured summarizer for system module designs.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
- Output JSON only (no Markdown, no code fences).
- Do NOT invent APIs/tables/dependencies; only extract from the module content.
- If unknown, use empty arrays/empty strings.
- "module_name" MUST equal the provided module name exactly.
If any rule is violated, the output is INVALID.

=====================
INPUT
=====================
Module name (MUST keep exactly): {module_name}

Module design document:
{module_content}

=====================
TASK
=====================
Extract key summary info for system-level aggregation.

Return EXACTLY this JSON schema:
{{
  "module_name": "模块名称",
  "purpose": "模块职责（一句话描述）",
  "interfaces": [
    {{"method": "GET/POST", "path": "/api/xxx", "description": "接口说明"}}
  ],
  "database_tables": [
    {{"name": "表名", "description": "表说明"}}
  ],
  "dependencies": ["依赖的模块名"],
  "key_features": ["核心功能点1", "核心功能点2"]
}}
"""

# ============================================================
# 系统设计 (Markdown)
# ============================================================

SYSTEM_DESIGN_PROMPT = """You are a senior software architect.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
1) Output Markdown only.
2) Do NOT output any top-level title (no '# ...').
   - Start directly from '## 2.1 ...'
3) MANDATORY DESIGN - "TBD" IS FORBIDDEN:
   - You MUST synthesize and design system architecture based on the module summaries.
   - Infer system structure, data flows, and interactions from the provided information.
   - "TBD" is ONLY allowed for deployment-specific info (network topology IPs, server names).
   - For architecture, data flow, module interactions: you MUST design them, not write "TBD".
4) Mermaid diagrams:
   - Must be inside ```mermaid code blocks
   - Must NOT include comments (%% or //)
   - Use ASCII quotes only (" or ')
If any rule is violated, the output is INVALID.

=====================
INPUT
=====================
[Requirements excerpt]
{requirements_excerpt}

[Glossary excerpt]
{glossary_excerpt}

[DAG overview]
{dag_overview}

[Module summaries]
{module_summaries}

=====================
TASK
=====================
Generate the system-level design document in Markdown with Mermaid diagrams.

Required sections (keep the exact numbering and headings):

## 2.1 系统结构
- 描述整体系统架构
- 包含系统架构图（Mermaid C4 或 flowchart）
- 必须基于模块摘要绘制完整的架构图

## 2.2 功能结构
- 描述系统功能模块划分
- 包含功能结构图
- 必须展示所有模块及其层级关系

## 2.3 网络拓扑图
- 如有具体部署信息则绘制，否则绘制典型的三层架构拓扑（客户端-应用服务器-数据库）

## 2.4 数据流转
- 描述系统数据在各模块间流转
- 必须包含数据流图（flowchart），展示主要业务数据的流向

## 2.5 系统模块交互关系
- 描述模块之间的调用/依赖关系
- 必须包含模块交互图，展示 API 调用关系

Write in a clear and professional style.
"""


# ============================================================
# 接口汇总 (Markdown)
# ============================================================

INTERFACE_PROMPT = """You are a senior software architect.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
1) Output Markdown only.
2) Do NOT output any top-level title (no '# ...').
   - Start directly from '## 4.1 ...'
3) MANDATORY DESIGN - "TBD" IS FORBIDDEN:
   - You MUST design complete interface specifications based on the module summaries.
   - For each interface: define method, path, request/response structure.
   - If module summaries lack detail, infer standard RESTful APIs based on module purpose.
   - Use common patterns: GET for retrieval, POST for creation, PUT/PATCH for update, DELETE for removal.
4) Use Markdown tables for interfaces.
If any rule is violated, the output is INVALID.

=====================
INPUT
=====================
[Requirements excerpt]
{requirements_excerpt}

[Glossary excerpt]
{glossary_excerpt}

[DAG overview]
{dag_overview}

[Module summaries]
{module_summaries}

=====================
TASK
=====================
Generate the unified interface design chapter in Markdown.

Required sections:

## 4.1 对外接口
- 列出系统对外暴露的所有 API 接口，按功能分类
- 必须为每个模块设计至少一个核心 API
- Use a Markdown table with columns:
  - Method (GET/POST/PUT/DELETE)
  - Path (/api/v1/...)
  - Module
  - Description
  - Request/Response (JSON 结构简述)

## 4.2 模块间接口
- 列出模块之间的内部调用接口
- 基于 DAG 依赖关系推断模块间调用
- Use a Markdown table with the same columns.

所有接口必须有具体设计，禁止使用 TBD。
"""

# ============================================================
# 数据库汇总 (Markdown)
# ============================================================

DATABASE_PROMPT = """You are a senior software architect.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
1) Output Markdown only.
2) Do NOT output any top-level title (no '# ...').
   - Start directly from '## 5.1 ...'
3) MANDATORY DESIGN - "TBD" IS FORBIDDEN:
   - You MUST design complete database schemas based on the module summaries.
   - For each table: define table name, fields (name, type, constraints), relationships.
   - If module summaries lack detail, infer standard fields: id (PK), created_at, updated_at, status, etc.
   - Design proper relationships: foreign keys, junction tables for many-to-many.
4) Mermaid diagrams:
   - Must be inside ```mermaid code blocks
   - Must NOT include comments (%% or //)
   - Use ASCII quotes only (" or ')
5) Section titles and headings MUST be written in Chinese.
   - Do NOT translate section titles into English.
If any rule is violated, the output is INVALID.

=====================
INPUT
=====================
[Requirements excerpt]
{requirements_excerpt}

[Glossary excerpt]
{glossary_excerpt}

[DAG overview]
{dag_overview}

[Module summaries]
{module_summaries}

=====================
TASK
=====================
Generate the unified database design chapter in Markdown with Mermaid diagrams.

Required sections:

## 5.1 ER图
- 使用 Mermaid erDiagram 绘制完整的实体关系图
- 必须包含所有模块涉及的数据表
- 必须标注表之间的关系（一对一、一对多、多对多）

## 5.2 表结构
- 列出所有数据库表，使用 Markdown 表格
- 必须包含以下列：
  - 表名
  - 所属模块
  - 主要字段（字段名、类型、说明）
  - 关系（外键关联）
- 每张表至少包含：主键、业务字段、时间戳字段

所有表结构必须有具体设计，禁止使用 TBD。
"""

# ============================================================
# 模块设计批判 (JSON)
# ============================================================

CRITIQUE_PROMPT = """You are a strict technical reviewer.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
- Output JSON only (no Markdown, no code fences).
- The score must be a float between 0.0 and 1.0.
- "passed" must be consistent with the threshold rule.
- Issues must be concrete and actionable (no vague complaints).
If any rule is violated, the output is INVALID.

=====================
INPUT
=====================
Module name: {module_name}

[Module design]
{module_design}

[Context]
{context}

=====================
REVIEW STANDARD (STRICT)
=====================
You must review as a demanding tech lead (do not be overly generous).
Deduct points based on:

1) Completeness (25%)
   - Must include: Overview, Interface Design, Data Model, Business Logic, Error Handling
   - Missing a required section: -0.2
   - Hollow content (title only, no substance): -0.1 each
   - Using "TBD" for designable content (APIs, fields, tables, logic): -0.15 each occurrence

2) Consistency (20%)
   - Must align with upstream modules and the glossary
   - Each inconsistency: -0.15

3) Feasibility (25%)
   - Must be technically feasible
   - Must handle edge cases and failures
   - Missing key logic consideration: -0.2

4) Clarity (15%)
   - Clear structure and no contradictions
   - Each ambiguous/conflicting statement: -0.1

5) Diagram Validity (15%)
   - Mermaid must render correctly and be inside ```mermaid blocks
   - Mermaid comments (%% or //) are severe issues
   - Missing/incorrect critical diagram: -0.2

Scoring:
- Start from 1.0
- Final score = 1.0 - total deductions (min 0.0)
- 0.9+ excellent, 0.8 good
- Below {threshold} is unacceptable

Pass rule:
- score >= {threshold} => passed = true
- score < {threshold} => passed = false

=====================
OUTPUT JSON SCHEMA
=====================
Return EXACTLY this JSON schema:
{{
  "passed": true,
  "score": 0.0,
  "issues": ["issue 1", "issue 2"],
  "suggestions": "specific improvement guidance"
}}
"""

# ============================================================
# 根据批判反馈重新生成 (Markdown)
# ============================================================

REGENERATE_PROMPT = """You are a senior software architect.

=====================
STRICT OUTPUT RULES (MUST FOLLOW)
=====================
1) Output Markdown only.
2) You MUST address every issue from the critique.
3) MANDATORY DESIGN - "TBD" IS FORBIDDEN:
   - You MUST design complete APIs, data models, and business logic.
   - Do NOT use "TBD" as an excuse to avoid designing.
   - If the previous version had "TBD", you MUST replace it with actual designs.
4) Mermaid diagrams:
   - Must be inside ```mermaid code blocks
   - Must NOT include comments (%% or //)
   - Must render correctly
5) ALL section titles MUST be in Chinese. Do NOT use English section titles.
If any rule is violated, the output is INVALID.

=====================
INPUT
=====================
模块名称: {module_name}

[当前设计（有问题的版本）]
{current_design}

[评审反馈]
- 评分: {score} (满分1.0，{threshold}为合格线)
- 发现的问题: {issues}
- 改进建议: {suggestions}

[上下文]
{context}

=====================
TASK
=====================
根据评审反馈，重新生成改进后的完整模块设计文档。

改进要求：
1) 逐一解决反馈中列出的每个问题
2) 确保包含所有必需章节，且每个章节都有实质内容：
   - 概述
   - 接口设计（必须有具体 API 定义）
   - 数据模型（必须有具体表结构）
   - 业务逻辑（必须有具体规则）
   - 时序图
   - 错误处理（必须有具体错误码）
   - 依赖关系
3) 确保 Mermaid 图表符合规范且可渲染
4) 保持与术语表和上游模块的一致性
5) 将所有 "TBD" 替换为实际设计内容

输出前请确认：
- [ ] 所有反馈问题都已解决
- [ ] 所有 Mermaid 图表规范且无注释
- [ ] 所有必需章节完整且有实质内容
- [ ] 无任何 "TBD" 占位符
"""