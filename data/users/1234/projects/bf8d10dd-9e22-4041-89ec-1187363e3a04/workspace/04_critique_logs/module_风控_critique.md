# 批判日志: 风控

## 批判迭代 #1 - 2026-01-26 15:25:38

**模块**: 风控

**分数**: 0.50 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Section 'Interface Design' is hollow (TBD for API endpoints, request/response, events).
- Section 'Data Model' is hollow (TBD for tables, fields, relationships).
- Section 'Dependencies' has hollow downstream module (TBD).
- Inconsistency: Module design mentions '业务核心' as upstream, but glossary defines '业务核心' as a system that receives and processes data, suggesting a potential circular dependency or role confusion.
- Inconsistency: Module design mentions '账户系统' as a dependency for account status, but glossary states '行业钱包' handles account management and relationship validation. The design's direct call to '账户系统' may bypass the intended architecture.
- Missing key logic consideration: No details on the 'preset rules' for risk assessment (e.g., rule definitions, scoring models, rule engine architecture).
- Missing key logic consideration: No details on the '降级策略' (degradation strategy) configuration or decision logic for upstream failures.
- Missing key logic consideration: No design for how '人工审核' tasks are created, managed, and their results integrated back into the workflow.
- Ambiguous statement: '模块边界限定于业务核心发起的风险检查请求处理' is vague. It's unclear if the module is purely synchronous or also handles asynchronous risk monitoring.
- Ambiguous statement: '返回通过、拦截或需人工审核的指令' lacks clarity on the response format and how the '原因' or '指令' are structured.


### 改进建议
1. Define concrete REST/GraphQL endpoints (e.g., POST /api/v1/risk/check), request/response payloads, and domain events published/consumed. 2. Design core data models: risk rules, risk events, audit logs, manual review tasks. Specify relationships with upstream entities (e.g., merchant, transaction). 3. Clarify the module's role vs. '业务核心' and '行业钱包'. Align the dependency flow: should risk module call '行业钱包' for account/relationship status, or directly call '账户系统'? Update the glossary or design accordingly. 4. Detail the risk rule engine: rule types (amount, frequency, velocity), configuration, scoring mechanism, and how rules are evaluated. 5. Specify the degradation strategy: configurable policies (e.g., 'default_pass', 'default_block') for each upstream dependency failure, with clear logging and alerting. 6. Design the manual review workflow: task creation schema, notification mechanism to ops, result callback API, and state management. 7. Provide a complete and valid Mermaid sequence diagram without placeholders, ensuring it matches the clarified dependencies and includes error handling paths.

---

## 批判迭代 #2 - 2026-01-26 15:28:05

**模块**: 风控

**分数**: 0.65 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Error Handling' in the design document. Deduct 0.2.
- Interface design includes a 'review callback' endpoint but the data model's `review_tasks` table lacks fields (e.g., `callback_status`, `notified_time`) to manage the callback workflow, causing inconsistency. Deduct 0.15.
- Business logic mentions '从行业钱包查询的账户与关系状态' but the glossary states '关系绑定校验' is a responsibility of the industry wallet. The design lacks detail on what specific statuses (e.g., binding validity, authentication level) are queried and how they are used in rules, indicating incomplete feasibility. Deduct 0.2.
- The term '行业钱包' is used in the design, but the glossary lists '行业钱包 (别名: 钱包系统)'. The design does not clarify which term is the canonical one for module naming, causing ambiguity. Deduct 0.1.
- The sequence diagram correctly uses Mermaid but lacks a critical path: it does not show the '签约风险检查接口' (`/risk/contract/check`) workflow, which is a key module function. Deduct 0.2.


### 改进建议
1. Add a dedicated 'Error Handling' section detailing specific error codes, retry mechanisms, and alerting strategies. 2. Align the data model with interface workflows: add fields to `review_tasks` for callback tracking and clarify the canonical module name for '行业钱包'. 3. Expand the business logic to specify the exact account/relationship statuses queried from the industry wallet and how they feed into risk rules (e.g., 'binding age', 'authentication method'). 4. Update the sequence diagram to include the `contract/check` flow, or create a separate diagram for it.

---

