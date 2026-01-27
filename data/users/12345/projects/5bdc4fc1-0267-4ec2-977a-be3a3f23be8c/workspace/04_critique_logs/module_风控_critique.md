# 批判日志: 风控

## 批判迭代 #1 - 2026-01-26 17:00:21

**模块**: 风控

**分数**: 0.50 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Interface Design' (TBD for API endpoints, request/response, events).
- Missing required section 'Data Model' (TBD for tables, key fields, relationships).
- Hollow content in 'Interface Design' and 'Data Model' sections (titles only, no substance).
- Inconsistent with glossary: '风控' is listed as a role/participant, but the design does not define its triggering mechanism or upstream dependencies.
- Missing key logic consideration: No details on how '幂等' (idempotency) is implemented (key source, storage, validation).
- Missing key logic consideration: No details on '回滚处理' (rollback) logic (trigger conditions, compensation strategy, state machine).
- Missing key logic consideration: No handling for edge cases like '部分成功' (partial success) or concurrent operations.
- Ambiguous statement: '交易冻结的资金范围必须为：已结算至天财收款账户的资金' is too vague; no definition of how to identify or scope these funds.
- Ambiguous statement: '冻结生效后，相关账户的资金操作能力受限（受限范围 TBD）' leaves the impact undefined.
- Diagram validity issue: Sequence diagram is too simplistic and lacks critical interactions (e.g., missing idempotency check, error flows, confirmation of downstream actions).


### 改进建议
1. Define concrete REST/GraphQL endpoints, request/response payloads, and event schemas for the module. 2. Design the data persistence layer: define tables (e.g., `freeze_orders`) with fields for freeze_type, target_account, idempotency_key, status, rollback_reference, etc. 3. Specify the upstream trigger for risk control instructions (e.g., an admin system, automated rule engine). 4. Detail the idempotency mechanism: define the source of the idempotency key (e.g., client-provided UUID), how it's stored, and the validation logic. 5. Design the rollback state machine: define states (INIT, PROCESSING, SUCCESS, FAILED, ROLLBACK_INITIATED, ROLLBACKED), triggers, and compensation actions. 6. Specify error handling strategies: retry policies for downstream failures, and compensation for partial successes. 7. Clarify the scope of '已结算资金' for transaction freezes (e.g., by transaction ID, batch ID, time range). 8. Update the sequence diagram to include idempotency checks, error responses, and confirmations from downstream systems.

---

## 批判迭代 #2 - 2026-01-26 17:20:39

**模块**: 风控

**分数**: 0.50 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Error Handling' in the design document. The section titled '6. 错误处理' is present, but the reviewer's standard requires it as a separate, complete section. This is a missing section deduction.
- Hollow content: The entire 'Interface Design' section (2) is marked as TBD with no concrete endpoints, request/response models, or event schemas, despite the review requirement to provide them. This constitutes hollow content.
- Hollow content: The entire 'Data Model' section (3) is marked as TBD with no concrete table names, field names, or relationships, despite the review requirement to provide them.
- Inconsistency with glossary: The glossary defines '风控' as a participant/module that *initiates* freeze instructions. The design document states the module '发起并管理' (initiates and manages) instructions, which is consistent. However, the design then contradicts this by stating the trigger source is TBD and the module only provides '冻结指令受理' (freeze instruction acceptance) capability, shifting from an initiator to a passive acceptor. This is an inconsistency.
- Missing key logic consideration for feasibility: The design repeatedly states that the core mechanism for identifying funds for '交易冻结' (transaction freeze) is TBD. Without a concrete, unique identifier for 'funds already settled to the Tiancai collection account', the entire transaction freeze feature is unimplementable. This is a severe feasibility issue.
- Missing key logic consideration for feasibility: The design does not specify how to resolve conflicts or ensure consistency when concurrent operations (like transfers, withdrawals) occur on the same account or funds that are being frozen. The handling is deferred to downstream systems (TBD), leaving a critical gap in the module's control logic.
- Ambiguous/conflicting statement: Section 1.3 states the module is responsible for validating that '定位要素齐全且可被下游识别' (positioning elements are complete and can be recognized by downstream). However, since the elements themselves are TBD, this responsibility cannot be fulfilled, creating a contradiction.
- Diagram validity issue: The Mermaid sequence diagrams are correctly formatted. However, they are based entirely on TBD components and interactions. While they follow syntax, their semantic validity for review is low as they depict undefined processes. A minor deduction is applied.


### 改进建议
1. **Define Concrete Interfaces**: Replace all TBDs in Section 2 with specific REST endpoints (e.g., POST /api/v1/freeze/merchant), detailed request/response JSON schemas (including field names, types, and examples), and event payload definitions. 2. **Define Concrete Data Model**: Specify the actual table name (e.g., `risk_control_freeze_order`), all columns with SQL types, indexes (especially for idempotency keys), and foreign key relationships. 3. **Specify Fund Identification Logic**: Collaborate with downstream systems (Accounting Core) to define the exact business identifier(s) for 'settled funds' (e.g., `settlement_batch_id`, `transaction_id`). This is the cornerstone of the transaction freeze feature. 4. **Clarify Module Role**: Align the module's description with the glossary. Explicitly define the upstream trigger (e.g., a specific system name and interface) and confirm if the module proactively initiates or reactively accepts instructions. 5. **Address Concurrency**: Design a concrete strategy for handling race conditions, such as using database pessimistic locks on the target account record within the risk module or defining a strict state transition protocol with downstream systems. 6. **Flesh out Error Handling**: While the section exists, detail specific HTTP status codes, error code enums, retry policies (exponential backoff), and compensation (SAGA) patterns for partial failures.

---

