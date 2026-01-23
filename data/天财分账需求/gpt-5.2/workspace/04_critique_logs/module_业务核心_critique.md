# 批判日志: 业务核心

## 批判迭代 #1 - 2026-01-21 18:10:52

**模块**: 业务核心

**分数**: 0.10 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Interface Design is TBD: missing API endpoints, request/response schema, idempotency strategy, authentication/authorization, and error code contract.
- Data Model is TBD: missing tables/entities (account, ledger, transaction, journal), primary keys, indexes, constraints, and relationships needed to support posting and reconciliation.
- Business logic lacks critical accounting controls: no明确的记账模型（借贷/双录/分录）、原子性边界（单库事务还是分布式）、以及如何保证余额与流水一致性。
- Missing idempotency and duplicate request handling: no requestId/transactionId uniqueness, retry semantics, or exactly-once/at-least-once processing strategy.
- Concurrency handling is mentioned but not specified: no concrete approach (optimistic versioning, pessimistic locking, balance reservation/hold) and no deadlock/timeout strategy.
- Failure handling is incomplete: no明确的补偿/冲正（reversal）机制、部分成功场景处理、以及与账户系统调用失败时的重试/熔断/降级策略。
- Inconsistency with module boundary: document says core performs account status and balance checks, but sequence diagram shows these checks delegated to 账户系统; need to clarify which system is source of truth and where validations run.
- Downstream integration is vague: says may provide reconciliation data to 对账单系统 but no event/message definition, delivery guarantees, or data contract.
- Missing key business rules: no handling of手续费（计费中台）、到账模式、场景（归集/批付/会员结算）差异化规则，despite glossary defining them.
- No explicit state machine for transaction lifecycle: pending/posted/failed/reversed, and how status transitions are persisted and exposed.


### 改进建议
补齐接口与数据模型并落到可实现细节：1）定义REST端点（例如POST /transfers）、鉴权方式、幂等键（requestId）与错误码；2）给出核心表设计（transaction、journal_entry、account_balance、account_hold等）及唯一约束（requestId唯一）、索引与字段含义；3）明确记账与一致性方案（单库事务内写分录+更新余额，或余额由分录汇总；并发用版本号CAS或行锁+冻结/预占）；4）定义交易状态机与冲正/补偿流程，覆盖超时、重试、重复请求、账户系统不可用等；5）明确与账户系统的职责边界（谁校验状态/余额、谁执行划转），并定义对账单系统的数据输出（事件名、字段、投递语义与重放策略）；6）补充与计费中台、到账模式、场景差异相关的规则与测试用例。

---

## 批判迭代 #2 - 2026-01-21 18:11:57

**模块**: 业务核心

**分数**: 0.40 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口一致性问题：接口设计写为POST /v1/transfers，但时序图中调用为POST /transfers，需统一路径与版本策略，否则调用方与网关路由会不一致。
- 记账方向定义存在高风险歧义：文档写付方记'贷'（减少）、收方记'借'（增加），与常见会计借贷含义可能相反；需明确本系统'借/贷'的业务语义（增减规则）并给出示例分录，避免对账与报表错误。
- 幂等处理策略不完整：仅描述requestId重复且成功直接返回，但未定义重复且处理中时的返回（例如返回同transactionId与当前状态、或阻塞等待），也未定义失败可重试的判定条件与幂等键有效期。
- 并发与一致性方案缺口：同时使用account_hold预占与account_balance乐观锁，但未说明扣减时的原子条件（例如update balance where version=? and balance>=?），也未说明预占与余额扣减的顺序及失败回滚策略，存在超扣或预占泄漏风险。
- 手续费计算与事务边界不清：计费中台调用在数据库事务流程中出现，但外部RPC不应置于长事务内；需明确先计费后入账或采用本地事务+Outbox/Saga，避免锁持有过长与死锁/超时。
- 事件发布可靠性不足：声明至少一次投递，但未给出Outbox表、投递重试、去重键（如transactionId）与发布时机（与本地事务的原子性）设计，容易出现已记账但事件丢失或重复导致下游不一致。
- 错误码与HTTP语义未定义：仅列出业务错误码，未规定HTTP状态码映射、错误响应结构（是否统一code/message/data为空）、以及可重试错误的标识字段，影响调用方正确重试与告警。
- 数据模型关键约束缺失：transaction缺少currency字段落库、amount/fee_amount精度与取值约束（decimal位数、非负、最小单位）、journal_entry缺少分录序号/类型（本金/手续费/冲正）与唯一约束，难以保证可审计与防重复插入。
- 冲正机制描述不落地：提到提供冲正接口，但未定义接口、幂等键、可冲正条件（仅成功交易？部分冲正？）、以及冲正与原交易的关联字段与状态机约束，容易引入账务不平。
- 账户系统权威性表述矛盾：文档称本模块是余额变更权威来源，但账户状态以账户系统为准；未说明状态变更与余额变更的竞态处理（例如扣款前后状态变更、冻结生效时如何处理），存在合规与风控漏洞。


### 改进建议
先修正接口与时序图的路径版本一致性，并在接口契约中补齐HTTP状态码与错误响应规范（含可重试标识）。明确'借/贷'在本系统的增减规则，给出至少两种场景（全额/净额、付方/收方承担手续费）的分录示例与校验公式。将计费调用移出数据库长事务：建议先计费再入账，或采用预估费率+事后调整；同时明确余额扣减的原子SQL条件（balance>=amount+fee且version匹配）与account_hold的生命周期（创建、超时释放、扣减、幂等）。事件发布采用Outbox模式：在同一事务写transaction、journal、balance与outbox事件记录，异步投递并以transactionId作为去重键，定义重试与死信。补齐数据模型字段与约束（currency、decimal精度、非负、唯一键、分录类型/序号、冲正关联字段），并把冲正接口与状态机规则写成可执行的契约（可冲正条件、幂等键、并发控制）。最后补充账户状态竞态处理策略（查询缓存一致性、冻结/销户在途交易处理、失败重试与补偿）。

---

## 批判迭代 #1 - 2026-01-22 16:10:50

**模块**: 业务核心

**分数**: 0.50 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Interface Design' (TBD for API endpoints, request/response, events).
- Missing required section 'Data Model' (TBD for tables, fields, relationships).
- Hollow content in 'Interface Design' section.
- Hollow content in 'Data Model' section.
- Inconsistent terminology: '计费中台' is listed as a separate downstream module but is also conflated with '清结算' in the glossary.
- Missing key logic consideration for handling asynchronous callbacks and ensuring idempotency.
- Ambiguous statement: '协调下游系统' is vague; specific coordination logic (e.g., synchronous vs. asynchronous calls, state management) is not defined.
- Diagram validity issue: Mermaid diagram is present but the sequence shows '清结算' directly calling '账户系统' and '账务核心', which may oversimplify the actual interaction patterns and error paths.


### 改进建议
1. Define concrete REST/GraphQL endpoints, request/response payloads, and domain events. 2. Specify the core data entities (e.g., TransactionOrder, SettlementRecord) with their fields and relationships to other modules. 3. Clarify the distinction and dependency between '计费中台' and '清结算'. 4. Detail the compensation/冲正 mechanism, idempotency handling, and state machine for the core workflow. 5. Elaborate on the coordination logic, including call patterns, timeouts, and retries. 6. Consider enriching the sequence diagram to include error/retry paths and the interaction with a message broker for asynchronous notifications.

---

## 批判迭代 #2 - 2026-01-22 16:11:06

**模块**: 业务核心

**分数**: 0.60 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Interface Design' content (TBD).
- Missing required section 'Data Model' content (TBD).
- Missing key logic consideration: No details on how to handle asynchronous callback timeouts or reconciliation mechanisms.
- Missing key logic consideration: No details on retry, circuit breaker, or fallback strategies for downstream failures.
- Diagram validity issue: Sequence diagram shows synchronous flow but design states '结算完成通知（异步）' is asynchronous, creating a contradiction in the diagram's representation.


### 改进建议
1. Define concrete API endpoints, request/response structures, and events. 2. Define core data tables, key fields, and relationships. 3. Elaborate on the compensation/reversal mechanism design for critical fund operations. 4. Specify the strategy for handling asynchronous callback timeouts (e.g., proactive query, reconciliation job). 5. Detail the retry policy, circuit breaker configuration, and fallback logic for downstream service calls. 6. Correct the sequence diagram to clearly distinguish synchronous calls and asynchronous notifications (e.g., using '->>' for async messages).

---

## 批判迭代 #1 - 2026-01-22 17:46:35

**模块**: 业务核心

**分数**: 0.65 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Section 'Interface Design' is hollow (title only, no substance).
- Section 'Data Model' is hollow (title only, no substance).
- The module's role is described as a 'persistent layer' but also includes 'format validation' and 'business logic' like uniqueness checks, which creates a contradiction in responsibility definition.
- The diagram shows '天财' directly interacting with '三代', but the glossary defines '三代' as a system role that processes instructions from '天财'. This is not an inconsistency but the diagram oversimplifies the flow by omitting the implied system boundary.
- The error handling strategy mentions 'retry mechanism' but does not specify retry count, backoff strategy, or what constitutes a retryable vs. non-retryable error, which is a key logic consideration.
- The diagram is technically valid Mermaid but lacks critical detail. It does not show the data flow for error responses back to '三代', which is a key part of the interaction.


### 改进建议
1. Populate the 'Interface Design' section with concrete API endpoints (e.g., POST /api/v1/transactions), request/response payload examples, and event definitions. 2. Define the 'Data Model' with specific table names (e.g., `t_core_transaction`), key fields (id, biz_no, institution_id, amount, status, created_at), and relationships. 3. Clarify the module's responsibility: either it is a simple persistence service (only stores validated data from upstream) or it includes validation logic. If it includes validation, detail the rules. 4. Enhance the error handling section by defining retry policies (max attempts, backoff), idempotency key handling for duplicate requests, and differentiation between client and server errors. 5. Update the sequence diagram to include an alternative error flow (e.g., alt block) showing the response path when validation or storage fails.

---

## 批判迭代 #2 - 2026-01-22 17:46:54

**模块**: 业务核心

**分数**: 0.50 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Interface Design' content (TBD).
- Missing required section 'Data Model' content (TBD).
- Hollow content in 'Interface Design' section.
- Hollow content in 'Data Model' section.
- Inconsistent terminology: Module name '业务核心' is not listed as a system role in the glossary.
- Inconsistent upstream dependency: Module design lists '三代' as the only upstream, but glossary indicates '行业钱包' also processes core wallet logic and may be a source of data.
- Missing key logic consideration: No details on data storage strategy (e.g., database type, sharding, indexing, retention policy).
- Missing key logic consideration: No details on the 'necessary format validation' logic or rules.
- Missing key logic consideration: No details on the retry mechanism for storage failures.
- Missing key logic consideration: No details on the idempotency handling for duplicate business serial numbers.
- Ambiguous statement: '不涉及资金处理、账户操作或复杂的业务逻辑计算' contradicts the responsibility of '进行必要的格式校验' and '业务流水号唯一性' which are business logic.
- Diagram validity issue: Sequence diagram shows '对账单系统' pulling data from '业务核心', but the module design states it provides data '为下游的对账单生成、数据查询等提供数据支撑', which is vague. The diagram should clarify if it's a pull or push model.


### 改进建议
1. Define concrete API endpoints, request/response structures, and events in the Interface Design section. 2. Define the core data tables, key fields (e.g., transaction_id, institution_id, amount, status, timestamp, participants), and relationships in the Data Model section. 3. Align module naming with the glossary; consider if this module is part of '业务核心' as defined in the glossary or a separate entity. 4. Clarify all upstream data sources (e.g., 三代, 行业钱包). 5. Detail the technical implementation of data validation, storage, retry, and idempotency mechanisms. 6. Refine the overview to accurately reflect the module's logical responsibilities without contradiction. 7. Update the sequence diagram to precisely reflect the data provisioning interface (e.g., REST API call, event consumption).

---

