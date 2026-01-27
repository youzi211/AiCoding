# 批判日志: 计费中台

## 批判迭代 #1 - 2026-01-26 16:40:54

**模块**: 计费中台

**分数**: 0.35 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Interface Design' content (API endpoints, request/response, events).
- Missing required section 'Data Model' content (tables, key fields, relationships).
- Business logic lacks concrete details: missing specific rate rule matching logic, calculation formula, and idempotency handling for retries.
- Inconsistent with glossary: '行业钱包' is defined as '分账核心' but the diagram shows it as a separate participant from '计费中台', implying it's upstream, which is correct but the module design's description of its role is vague.
- Missing key feasibility considerations: no discussion on transaction isolation, data consistency between fee calculation and ledger generation, or performance under high load.
- Ambiguous statement: '边界仅限于计费逻辑的处理，不涉及账户余额的直接操作' contradicts the dependency on '清结算' which likely does affect balances; the responsibility boundary is unclear.
- Diagram is present but overly simplistic; it omits error flows, asynchronous interactions, and the response back to '行业钱包'.
- The 'TBD' placeholders for critical design elements indicate the design is incomplete and not ready for implementation review.


### 改进建议
1. Define concrete REST/GraphQL endpoints with HTTP methods, paths, and payload examples. 2. Specify the data model: create a 'fee_ledger' table schema with fields like id, transaction_ref, payer_id, payee_id, fee_amount, fee_bearer, status, rule_id, calculated_at. 3. Detail the business logic: provide the fee calculation formula, the rule matching algorithm (e.g., by institution_id, merchant_tier), and idempotency keys for retry scenarios. 4. Expand the sequence diagram to include error responses, retry loops to the clearing system, and confirmation flows. 5. Clarify the module's boundaries and its eventual consistency guarantees with downstream systems. 6. Address non-functional requirements: expected load, latency, and database sharding strategy for the fee ledger.

---

## 批判迭代 #2 - 2026-01-26 16:43:24

**模块**: 计费中台

**分数**: 0.65 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Section 'Dependency' is missing. Required sections are: Overview, Interface Design, Data Model, Business Logic, Error Handling. Deduct -0.2.
- The 'Overview' section states the module is for '天财分账业务', but the 'Context' glossary defines '天财分账' as a transaction type within the wallet system. The module's upstream is '行业钱包 (分账核心)', which is defined as handling '分账请求接收与处理'. This is an inconsistency in scope definition. Deduct -0.15.
- The 'Interface Design' section lists a 'business_scene' field (e.g., 'MEMBER_SETTLEMENT'), but the 'Data Model' for the core `fee_ledger` table does not include a field to store this critical rule-matching dimension. This is a major inconsistency between interface and persistence. Deduct -0.15.
- The 'Business Logic' section mentions querying a '计费规则配置表 (TBD)' but provides no details on its structure, ownership (三代), or how rules are prioritized. This is a missing key logic consideration. Deduct -0.2.
- The 'Business Logic' section states the initial status is 'PENDING', but the 'Data Model' defines a status 'CLEARING_SENT'. The sequence diagram shows updating the status to 'CLEARING_SENT' after event publishing and before transaction commit. This creates ambiguity about the exact status flow and when it is persisted. Deduct -0.1.
- The sequence diagram contains a logical flaw: it shows committing the database transaction *after* publishing the event to the message queue ('发布FeeLedgerCreated事件'). In a local transaction table pattern, the event is typically persisted locally within the same transaction. Publishing to the external queue happens asynchronously. The diagram's order suggests the event could be published but the transaction could fail to commit, leading to inconsistency. This is a severe feasibility issue. Deduct -0.2.
- The 'Error Handling' section mentions '本地事务表+消息队列监听器模式 (TBD)' but does not detail how this pattern ensures consistency between the `fee_ledger` record and the `FeeLedgerCreated` event. This is a missing key logic consideration for failure handling. Deduct -0.2.


### 改进建议
1. Add a 'Dependencies' section detailing internal (DB, MQ, rule config service) and external (upstream/downstream) dependencies, including non-functional aspects. 2. Clarify the module's scope in the 'Overview' to precisely align with the glossary: it serves the '行业钱包 (分账核心)' for its '天财分账' transactions. 3. Add a `business_scene` field (VARCHAR) to the `fee_ledger` data model to persist the rule-matching dimension. 4. Design and document the rule configuration table/service, including fields (e.g., institution_id, scene, payer/payee type, effective dates, priority, rate, fixed fee), ownership (三代), and matching logic. 5. Redesign the sequence diagram and clarify the status flow: a) Insert `fee_ledger` record with status 'PENDING' and event data in a local 'outbox' table within a single DB transaction. b) Commit the transaction. c) A separate listener process picks up the 'outbox' record, publishes the event to MQ, and updates the `fee_ledger` status to 'CLEARING_SENT'. This ensures atomicity. 6. Detail the 'local transaction table + message queue listener' pattern in the 'Business Logic' or 'Error Handling' section to explain how event publishing is guaranteed.

---

## 批判迭代 #1 - 2026-01-26 17:00:09

**模块**: 计费中台

**分数**: 0.45 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Section 'Interface Design' is hollow (API endpoints, request/response structures are TBD).
- Section 'Data Model' is hollow (table definition and key fields are TBD).
- Section 'Business Logic' is hollow (core workflow steps, fee calculation rules, and idempotency strategy are TBD).
- Section 'Error Handling' is hollow (error codes, retry strategies, and compensation mechanisms are TBD).
- Inconsistency with glossary: The glossary defines '清结算' and '计费中台' as separate entities, but the module design's sequence diagram shows '计费中台' directly interacting with '清结算', which may oversimplify or misrepresent the actual system boundaries.
- Missing key logic consideration: No details on how fee rates are sourced, configured, or applied, which is a core function.
- Missing key logic consideration: No details on the compensation mechanism for failed fee clearing result notifications.
- Ambiguous statement: '参与手续费清分流程，并接收/回传清分结果' is unclear about the module's active vs. passive role and the exact data flow.
- Ambiguous statement: '计费相关记账协同(TBD)' in the sequence diagram is vague and does not specify the interaction with the accounting core.


### 改进建议
The design is a skeleton with critical sections marked as TBD. To proceed, you must define: 1) Concrete REST/GraphQL API specifications. 2) Complete data model for the '计费流水' table, including idempotency keys and status fields. 3) Detailed business logic for fee calculation, including rule sourcing and the handling of edge cases like '净额转账下手续费大于等于转账金额'. 4) A comprehensive error handling strategy with specific error codes, retry policies, and compensation workflows for clearing failures. 5) Clarify the module's role in the fee clearing process and its interactions with '清结算' and '账务核心' based on the actual system architecture.

---

## 批判迭代 #2 - 2026-01-26 17:17:02

**模块**: 计费中台

**分数**: 0.40 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Completeness: The design is severely incomplete. Critical sections like Interface Design, Data Model, and Business Logic are filled with 'TBD' placeholders instead of concrete specifications. This constitutes hollow content across multiple sections.
- Feasibility: The design is not technically feasible. Key dependencies (e.g., fee rule source), core calculation logic (formulas, rounding), and failure handling strategies (retry, compensation) are undefined. Edge cases like 'fee >= transfer amount' are noted but have no resolution.
- Consistency: The design acknowledges but does not resolve the ambiguity between '计费中台' and '清结算' from the glossary. The role boundary is clarified in text but the interaction mechanisms (interfaces, events) remain entirely TBD, leaving the core dependency unresolved.
- Clarity: The pervasive use of 'TBD' for essential elements (field names, endpoints, rules) makes the design ambiguous and non-actionable. It describes what *should* exist but not *what* exists.
- Diagram Validity: The sequence diagram correctly uses Mermaid syntax and is properly placed. However, it depicts interactions (e.g., '清分结果回传') for which the design explicitly states the mechanism is TBD, creating a contradiction between the diagram and the textual description.


### 改进建议
This is a design skeleton, not an implementable specification. To proceed, the following must be concretely defined: 1) **Interfaces**: Define exact REST/GraphQL endpoints, HTTP methods, request/response payloads with all mandatory fields (e.g., transaction amount, business ID, appId). 2) **Data Model**: Define the '计费流水' table schema with actual field names, types, constraints, and a detailed state machine. 3) **Business Logic**: Specify the source and structure of fee rules, the exact calculation formula and rounding rules, and concrete handling for all edge cases. 4) **Dependencies**: Formalize the integration method with 清结算 (API contracts or event schemas) and identify the fee rule provider. Remove all TBDs with specific decisions.

---

