# 批判日志: 清结算

## 批判迭代 #1 - 2026-01-21 18:13:32

**模块**: 清结算

**分数**: 0.20 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 事件设计不完整：消费事件标注为TBD，缺少清结算从行业钱包系统或账户系统接收哪些事件、触发条件、幂等键、重试与死信策略，无法落地异步链路与一致性方案。
- 与账户系统接口不一致：清结算依赖账户系统获取账户状态与类型信息，但未定义调用账户系统的具体接口（如GET /v1/accounts/{accountId}）、字段映射（status枚举INITIAL/ACTIVE/FROZEN/CLOSED）以及对INITIAL/CLOSED不可交易的校验规则，导致跨模块契约缺失。
- 幂等方案不可实现：仅说明通过X-Request-ID幂等，但数据模型未提供幂等存储（如request_id字段、唯一索引、幂等表）与返回同一结果的规则，无法保证重复请求返回一致settlementId与status。
- 资金冻结/解冻缺少关键业务约束：/v1/funds/freeze与/unfreeze未给出请求体字段（referenceId、冻结原因、幂等键）、解冻前置校验（冻结记录状态机、部分解冻、重复解冻）以及与结算/退货流程的关联，容易产生资金可用余额不一致。
- 到账模式arrivalMode定义不清：仅描述净额/全额但未给出枚举值、与feeBearer组合下的入账/出账公式、四舍五入与最小币种规则，无法实现可对账的记账逻辑。
- 结算状态机缺失：settlement_record仅有status字段但未定义状态枚举与迁移（如INIT、FEE_PENDING、BOOKING_PENDING、SUCCESS、FAILED、REVERSED），也未说明失败后的补偿/冲正触发条件与数据修正方式（文中多处TBD）。
- 与业务核心记账交互不完整：仅描述发起记账请求但未定义请求字段、幂等键、超时重试策略、以及记账成功但本地落库失败时的恢复机制，存在双写一致性风险。
- 计费同步与计费计算职责边界混乱：流程中既调用计费中台计算手续费又在结算完成后再通过/v1/fee/sync同步，未明确sync的目的（对账/入账/落账）与幂等规则，且未说明fee_record与计费中台返回结果的权威来源与冲突处理。
- 数据模型缺少关键约束：金额字段未声明精度与币种；缺少必要索引（transaction_id唯一性、settlement_id外键约束、reference_id索引）；refund_account与账户系统的关联键不明确（account_id是否同一命名空间）。
- 错误码与HTTP语义未定义：列出错误码但未规定HTTP状态码映射、可重试/不可重试分类、以及通用响应code/message/data在失败时data结构，影响调用方处理。
- 非功能指标缺乏支撑：P99<300ms但流程包含计费中台与业务核心两次同步调用，未给出超时预算、并发控制、降级策略（例如计费计算是否允许异步）与限流方案，指标不可验证。
- 时序图缺少关键分支：未体现计费失败、记账失败、落库失败、fee sync失败的分支与补偿路径，导致关键异常流程未被设计覆盖。


### 改进建议
补齐跨系统契约与可落地的一致性设计：1）明确清结算与账户系统/计费中台/业务核心的接口契约（URL、字段、枚举、HTTP码、超时与重试、幂等键），并给出字段映射与校验规则（尤其账户status与不可交易状态）。2）实现幂等：在settlement_record或独立idempotency表增加request_id（X-Request-ID）并建立唯一索引，定义重复请求返回同一settlementId与最终状态的规则。3）定义状态机：为settlement_record与funds_freeze_record补充状态枚举与迁移图，覆盖FEE_PENDING、BOOKING_PENDING、SUCCESS、FAILED、REVERSED等，并明确补偿/冲正触发条件与数据修复步骤。4）补全资金与金额规则：arrivalMode枚举、feeBearer组合下的入账公式、精度与舍入、币种字段；冻结/解冻接口请求体与校验（referenceId、部分解冻、重复解冻、幂等）。5）完善事件：列出消费事件与发布事件的完整结构、幂等消费策略、Outbox与DLQ重试策略，并在时序图中补齐失败分支与恢复路径。6）补充索引与约束：transaction_id唯一性策略、外键与索引、reference_id索引、金额DECIMAL精度，确保可对账与可追溯。

---

## 批判迭代 #2 - 2026-01-21 18:15:13

**模块**: 清结算

**分数**: 0.25 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 金额单位定义不一致：接口字段amount/feeAmount声明单位为分（整数），但数据模型使用DECIMAL(20,2)且未明确存储单位；需统一为（分，BIGINT）或（元，DECIMAL）并在所有接口/表/计算规则中一致。
- 结算流程中出现不合理步骤：时序图写清结算去DB校验账户余额，但余额权威应在业务核心或账户系统；需明确余额校验与扣减/冻结的唯一权威系统，并删除或改为缓存校验（不可作为最终判断）。
- 与上游账户系统状态枚举不一致：文档写账户状态必须为ACTIVE且INITIAL/CLOSED不可交易，但错误码映射里又用403 ACCOUNT_FROZEN_OR_CLOSED，且400 INVALID_ACCOUNT_STATUS；需统一状态判断与HTTP语义（例如INITIAL/FROZEN/CLOSED均返回同一业务码与HTTP）。
- 幂等设计缺口：声明所有写操作基于X-Request-ID幂等，但GET /v1/refund-accounts/{accountId}不需要幂等；同时未定义幂等记录的生命周期、并发写入时的唯一约束冲突处理（先落库还是先调下游）以及重复请求返回的HTTP码策略。
- Outbox与事件发布不完整：描述了插入Outbox事件，但数据模型未包含outbox表结构与投递状态字段；无法落地实现可靠投递与重试/去重。
- 计费中台降级策略自相矛盾：业务逻辑写计费不可用则流程中断并置FEE_PENDING，但非功能指标又写可降级为默认费率；需明确是否允许默认费率结算、适用条件、审计与对账处理。
- 结算状态机缺少关键迁移：未覆盖INIT直接失败、BOOKING_PENDING重试/超时、SUCCESS后的对账修正、REVERSED后的终态约束；也未定义FEE_PENDING重试成功后如何回到BOOKING_PENDING的触发机制（定时任务/事件）。
- 资金冻结/解冻与账户系统职责边界不清：冻结操作写调用业务核心，但同时又写校验账户可用余额；需明确可用余额来源（业务核心返回）以及并发冻结的原子性保证（例如核心侧幂等+乐观锁/版本号）。
- 错误码与HTTP映射不严谨：409 DUPLICATED_REQUEST与幂等返回已有结果冲突（幂等通常返回200/201并带原结果）；424用于核心记账失败可能不合适（更常见是502/503或业务码+200/500）；需给出统一规范。
- 接口契约缺失关键字段：结算响应仅有status/feeAmount，但缺少settledAmount、失败原因码、记账流水号/核心凭证号等可对账字段；冻结/解冻响应缺少剩余可解冻金额与幂等回放信息。
- 数据模型缺少约束与索引细节：fee_record未声明主键类型与唯一约束（settlement_id是否唯一）；funds_freeze_record的frozen_amount更新规则与不变量（0<=frozen_amount<=amount）未通过约束表达；缺少created_at/updated_at默认值与时区约定。
- 时序图与文字不一致：文字说结算完成后异步同步计费明细，但时序图在成功路径里同步调用POST /v1/fee/sync；需明确是同步还是异步，以及失败重试对主流程的影响。
- 安全合规描述不可执行：仅写敏感数据加密传输与存储，但未明确哪些字段需要加密/脱敏（accountNo、accountId、金额）、密钥管理与日志脱敏策略；审计要求未落到表字段（操作人、来源IP、traceId等）。


### 改进建议
先做一致性与可落地性整改：1）统一金额单位与类型（推荐接口与库均用分的BIGINT，展示层再格式化），补充settled_amount/fee_amount等计算与四舍五入规则的精确定义；2）明确权威账务系统：余额校验、扣减、冻结/解冻必须由业务核心原子完成，清结算仅做前置校验（账户状态）与请求编排；3）补齐幂等与并发方案：定义X-Request-ID作用范围、重复请求返回策略（200回放原响应）、并发插入唯一键冲突处理、下游调用幂等键透传；4）补齐Outbox表与投递机制字段（event_id、aggregate_id、event_type、payload、status、retry_count、next_retry_at、created_at），并明确消费者去重键；5）统一错误码与HTTP规范，给出每个接口的成功/失败示例与字段（含失败原因、核心凭证号、对账字段）；6）修正计费降级策略（要么严格阻断并重试，要么允许默认费率但需标记、后补差与审计）；7）完善状态机与后台任务触发（FEE_PENDING/BOOKING_PENDING重试、超时、对账修复、冲正幂等）；8）补充安全与审计落库字段与日志脱敏清单。

---

## 批判迭代 #1 - 2026-01-22 16:14:20

**模块**: 清结算

**分数**: 0.60 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Error Handling' (deduct 0.2).
- Missing required section 'Dependency Relationships' (deduct 0.2).
- Inconsistency with glossary: The glossary defines '清结算' as an alias for '清结算/计费中台', implying a combined module, but the design treats '计费中台' as a separate upstream dependency. This creates a circular or ambiguous relationship (deduct 0.15).
- Inconsistency with upstream module 'Account System': The design states it will 'drive the account system to complete fund transfers' and 'send fund operation instructions', but the Account System design shows it consumes events from '清结算' and returns results. The interaction pattern (synchronous API call vs. async event) is not clearly defined (deduct 0.15).
- Inconsistency with upstream module 'Billing Center': The design mentions both 'calling' and 'consuming events' from the Billing Center without clarifying the primary interaction mode, leading to ambiguity (deduct 0.15).
- Missing key logic consideration for idempotency: Although mentioned as a rule, the specific mechanism (e.g., using business serial number) and how it's enforced across the workflow (e.g., at the start of settlement process) is not detailed (deduct 0.2).
- Missing key logic consideration for transaction/compensation: The design mentions 'rollback' and 'compensation mechanism' but provides no concrete steps or strategy for handling partial failures in the multi-step settlement flow (e.g., if step 6 succeeds but step 8 fails) (deduct 0.2).
- Ambiguous statement: The 'Business Logic' section states 'The boundary lies in processing the generation, execution, and result synchronization of settlement instructions, not directly managing account balances, nor handling business logic (such as split relationship) verification.' However, the subsequent workflow includes 'Ensure business data is legal and in a settable state,' which is a form of business logic verification, creating a contradiction (deduct 0.1).
- Mermaid diagram contains a critical error: The sequence diagram uses Chinese comments inside the diagram block (`Note over 风控,清结算: 冻结申请流程`). While not a syntax comment (%% or //), using natural language notes inside the mermaid code block is not standard practice and may cause rendering issues in some parsers. More critically, the diagram is missing the consumption of the 'FeeCalculatedEvent' from the Billing Center, which is mentioned in the text (deduct 0.2).


### 改进建议
1. Add the missing 'Error Handling' and 'Dependency Relationships' sections with concrete content. 2. Clarify the architectural relationship between '清结算' and '计费中台' (Billing Center) as per the glossary. Are they one module or two? If two, define the clear API/event contract. 3. Specify the interaction pattern with the Account System (synchronous API call, asynchronous command, or event-driven) and ensure it matches the Account System's documented interface. 4. Detail the idempotency implementation, e.g., a check at the beginning of the settlement process using the business serial number to reject duplicates. 5. Design a concrete compensation/saga pattern for the multi-step settlement workflow to ensure consistency in case of partial failures. 6. Reword the boundary statement to be consistent with the described validation steps. 7. Revise the sequence diagram: Remove the Chinese note or place it outside the mermaid block as a caption. Explicitly show the consumption of the 'FeeCalculatedEvent' from the Billing Center (step 2/3).

---

## 批判迭代 #2 - 2026-01-22 16:15:00

**模块**: 清结算

**分数**: 0.65 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Error Handling' (deduction -0.2).
- Hollow content in 'Interface Design' and 'Data Model' sections (deduction -0.2).
- Inconsistent module relationship: The design states '计费中台' is an internal sub-service, but the context defines it as a separate upstream module. This creates a contradiction in dependencies (deduction -0.15).
- Missing key logic consideration for handling failures in the Saga compensation mechanism (deduction -0.2).
- Ambiguous statement: The scope states it '不直接管理账户余额', but the workflow involves generating and sending account operation commands, which is a form of indirect management. This creates a potential boundary conflict (deduction -0.1).
- The Mermaid sequence diagram contains comments (e.g., '1. 结算指令(分账/会员结算)') which are not valid Mermaid syntax and will cause rendering errors (deduction -0.2).


### 改进建议
1. Populate the 'Error Handling' section with concrete error scenarios and strategies. 2. Define concrete API endpoints, request/response structures, and data model tables/fields. 3. Clarify the architectural relationship with '计费中台': either integrate it fully as a sub-component or define it as a clear external dependency. 4. Detail the compensation logic for the Saga pattern, including how compensation failures are handled. 5. Remove or properly format the comments within the Mermaid diagram sequence arrows to ensure it renders correctly.

---

## 批判迭代 #1 - 2026-01-22 17:46:45

**模块**: 清结算

**分数**: 0.60 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Section 'Interface Design' is hollow (TBD).
- Section 'Data Model' is hollow (TBD).
- Section 'Business Logic' lacks detail on key workflows like '会员结算' and '批量付款' mentioned in glossary.
- Section 'Error Handling' lacks concrete retry policies, compensation mechanisms, and idempotency handling.
- Diagram is missing critical upstream (风控, 业务核心) and downstream (对账单系统) interactions.
- Diagram sequence is incomplete; it does not show failure paths or compensation flows.
- Business logic description is inconsistent with glossary; '退货处理' mentions '天财收款账户' but glossary defines 04退货账户 for this purpose.


### 改进建议
1. Define concrete API endpoints, request/response structures, and events in Interface Design. 2. Specify core tables (e.g., settlement_orders, fee_records), key fields, and relationships in Data Model. 3. Expand Business Logic to detail workflows for 会员结算, 批量付款, and 归集, including state transitions and concurrency control. 4. Specify retry counts, backoff strategies, idempotency keys, and compensation (e.g., sagas) in Error Handling. 5. Update the sequence diagram to include interactions with 风控 (for freeze), 业务核心 (for transaction data), and 对账单系统, and add alternative failure flows. 6. Align '退货处理' logic with glossary by clarifying the use of 04退货账户.

---

## 批判迭代 #2 - 2026-01-22 17:47:32

**模块**: 清结算

**分数**: 0.70 / 1.0

**结果**: ✅ 通过


### 发现的问题

- Missing required section: No explicit 'Performance & Scalability' or 'Security' considerations are included in the design, which are crucial for a core financial module.
- Inconsistency with glossary: The design mentions '天财收款账户' and '天财接收方账户', but the glossary defines '天财收款账户' as also known as '天财专用账户'. The design uses '天财专用账户' in a different context (as a type of account for payers/receivers), which is ambiguous and not fully aligned.
- Inconsistency with glossary: The design states '资金首先结算至品牌总部的天财收款账户（主动结算模式）'. The glossary defines '主动结算' as funds settling to a merchant-specified settlement account. The design does not clarify how this mode is triggered or configured, creating a potential gap.
- Feasibility issue: The '会员结算' workflow mentions '根据预设的分账规则，触发从总部账户向各门店账户的分账流程' but lacks detail on how these rules are stored, retrieved, and executed. It also does not address concurrent rule updates or versioning.
- Feasibility issue: The error handling mentions a '降级逻辑' (fallback) using a local cached minimum fee if the计费中台 is unavailable. This is risky for a financial system as it could lead to revenue loss or incorrect settlements. The design lacks details on cache invalidation and post-fallback reconciliation.
- Clarity issue: The data model section lists 'retry_logs' but does not define its structure or how it integrates with the retry mechanism described in error handling.
- Clarity issue: The term '三代' is used in the sequence diagram and context but its role as an upstream module is not clearly defined in the 'Dependencies' section of the design. It's listed but the interaction is vague.
- Diagram validity issue: The Mermaid sequence diagram uses Chinese participant names (e.g., '三代', '业务核心'). While it will render, the use of non-alphanumeric characters in participant identifiers can sometimes cause parsing issues in some Mermaid versions. Best practice is to use simple English aliases.


### 改进建议
1. Add sections for 'Performance & Scalability' (e.g., handling peak loads for batch payments) and 'Security' (e.g., data encryption, audit trails). 2. Align all account type references precisely with the glossary definitions to avoid ambiguity. 3. Elaborate on the '会员结算' rule engine: where rules are stored, how they are applied, and concurrency handling. 4. Re-evaluate the fee calculation fallback strategy; consider a 'fail-fast' approach with manual intervention instead of automatic settlement with cached rates, or design a robust reconciliation process. 5. Define the schema for the `retry_logs` table. 6. Clarify the role and interaction pattern of '三代' in the module dependencies. 7. In the sequence diagram, consider using English aliases for participants (e.g., 'Client' for '三代') and use the `participant` keyword with the alias first for clarity (e.g., `participant C as 三代`).

---

