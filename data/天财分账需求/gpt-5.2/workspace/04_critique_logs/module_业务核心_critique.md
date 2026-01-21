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

