# 批判日志: 业务核心

## 批判迭代 #1 - 2026-01-26 15:25:26

**模块**: 业务核心

**分数**: 0.60 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Section 'Interface Design' is hollow (TBD). Deduct -0.1.
- Section 'Data Model' is hollow (TBD). Deduct -0.1.
- Inconsistency: The design states the module receives data from '天财', but the glossary clarifies it's via '开放平台'. The design lacks this interface specification. Deduct -0.15.
- Inconsistency: The design mentions '账户系统' as a downstream participant, but the glossary defines it as the underlying system for '行业钱包'. The diagram shows '行业钱包' calling '账户系统', which is correct, but the module's dependency description is ambiguous. Deduct -0.15.
- Missing key logic consideration: The design mentions verifying '付方天财收款账户' but lacks details on how to handle scenarios where the payer is a '天财接收方账户' (e.g., in batch payments). Deduct -0.2.
- Missing key logic consideration: The design mentions '计算分账金额' but provides no algorithm or rules for how this calculation is performed (e.g., fixed amount, percentage, fee deduction). Deduct -0.2.
- Missing key logic consideration: The design mentions '重试与冲正机制' but provides no concrete strategy (e.g., idempotency keys, compensation transaction design, retry backoff). Deduct -0.2.
- Ambiguous statement: '其边界在于处理与“天财分账”交易类型相关的业务逻辑' is vague. Does it handle all sub-scenarios (归集, 会员结算, 批量付款) equally? The logic for each may differ. Deduct -0.1.
- Diagram validity: The Mermaid diagram is present and correctly formatted. No deduction.


### 改进建议
1. Populate the 'Interface Design' section with concrete API endpoints (REST/GraphQL), request/response payloads, and event definitions. 2. Define the 'Data Model' with core tables/entities (e.g., Transaction, Relationship, AuditLog) and their key fields. 3. Explicitly specify that the upstream interface is via the '开放平台' using the assigned APPID and institution code. 4. Clarify the module's direct dependencies: it depends on '行业钱包' for account operations, not directly on '账户系统'. 5. Detail the business logic for different scenarios (归集, 会员结算, 批量付款), including specific validation rules and amount calculation formulas. 6. Design a concrete failure recovery strategy: define idempotency keys, retry logic with exponential backoff, and a compensation transaction flow for rollback. 7. Specify how the module will handle partial failures in batch payments.

---

## 批判迭代 #2 - 2026-01-26 15:28:08

**模块**: 业务核心

**分数**: 0.75 / 1.0

**结果**: ✅ 通过


### 发现的问题

- Section 'Error Handling' is hollow, containing only a title and no substance.
- Data model is inconsistent with glossary: glossary defines '天财专用账户' includes '天财收款账户' and '天财接收方账户', but design doc uses 'payerAccountNo' and 'payeeAccountNo' without clarifying which account types are allowed per scene, leading to ambiguity.
- Business logic lacks key consideration for handling 'extInfo' field. It is marked 'TBD' in request and mentioned in calculation rules but has no defined structure or validation logic, making implementation infeasible.
- Business logic mentions '冲正机制' but does not define the data flow or state transitions for the 'COMPENSATING' status, nor does it specify how to handle failures during compensation.
- Diagram validity: The Mermaid sequence diagram is missing a critical component. It shows the '业务核心' interacting with '行业钱包' for account checks and fund transfers, but does not depict the '冲正' (compensation) flow or the asynchronous event publishing to '清结算', which are key parts of the described workflow.
- Clarity: The description of '调用行业钱包执行分账' is ambiguous. It states '将校验通过的分账指令（可能分批）发送至行业钱包', but the conditions and logic for batching are not defined.


### 改进建议
1. Populate the 'Error Handling' section with concrete error categories, HTTP status codes, retry policies, and compensation strategies as outlined in the '处理策略' subsection. 2. Clarify the account type constraints (天财收款账户 vs. 天财接收方账户) for payer and payee in each 'scene' within the business rules. 3. Define the structure and validation rules for the 'extInfo' field for each business scene. 4. Detail the compensation workflow: when it's triggered, how the 'COMPENSATING' status is used, the steps to create reverse instructions, and how to handle compensation failures. 5. Update the sequence diagram to include the compensation flow and the asynchronous notification to the clearing module ('清结算'). 6. Specify the batching logic for sending instructions to the wallet system (e.g., size limit, failure handling within a batch).

---

