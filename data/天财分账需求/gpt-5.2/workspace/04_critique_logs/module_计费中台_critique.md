# 批判日志: 计费中台

## 批判迭代 #1 - 2026-01-21 18:10:52

**模块**: 计费中台

**分数**: 0.10 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口设计为空（API端点、请求响应结构、事件发布消费均为TBD），无法评审对接方式、幂等、鉴权、错误码与版本策略。
- 数据模型为空（表/集合、关键字段均为TBD），无法评审计费结果如何持久化、如何对账追溯、如何支持重放与审计。
- 依赖关系表述与上下游定义不一致：在数据模型中写为依赖账户系统并同步清结算，但在依赖关系章节将账户系统标为上游模块（查询账户信息）。需明确账户系统是被调用依赖（下游依赖）还是事件上游，并统一术语。
- 核心业务逻辑缺少关键输入与规则维度定义：未明确交易类型枚举、场景（归集/批量付款/会员结算）与费率策略的映射、到账模式（净额/全额）对手续费承担与入账金额的影响。
- 缺少幂等与一致性设计：未说明计费请求的幂等键（如交易单号）与重复请求处理；未说明向清结算同步的至少一次投递下如何去重与补偿。
- 错误处理不够可执行：仅描述重试或降级，未定义哪些错误可重试、重试策略（次数/退避）、降级行为（返回默认费率或拒绝交易）以及与对账的补偿流程。
- 边界情况覆盖不足：仅列出费率为零、溢出、规则未找到，缺少金额精度与舍入规则、币种支持、最小/最大手续费封顶封底、负数或超限金额校验、账户信息缺失或状态异常处理。
- 同步清结算的数据契约缺失：未定义同步字段（手续费金额、承担方、原交易标识、计费规则版本、计算明细）、同步时机（同步成功是否影响对上游返回）与失败后的重试/补偿机制。


### 改进建议
补齐可落地的接口与数据契约：1）定义REST端点（如POST /fees/quote与POST /fees/settlement-sync或事件主题），给出请求字段（交易单号、场景、交易类型、金额、币种、手续费承担方、付方/收方账户标识、到账模式等）、响应字段（手续费、净额/全额、规则版本、明细）与标准错误码；2）设计持久化模型（计费请求表、计费结果表、同步出站表outbox），包含幂等键、状态机、规则版本、时间戳与审计字段；3）明确依赖方向与调用方式（账户系统为被调用依赖还是事件上游），统一术语；4）补充规则引擎维度与算法细节（舍入、封顶封底、精度、币种、异常输入校验），并给出各场景的费率策略映射；5）补齐一致性方案（幂等、去重、outbox+重试、补偿与对账），明确同步清结算失败时的处理与SLA；6）将错误处理细化为可执行策略（可重试错误清单、退避、熔断、降级行为与告警指标）。

---

## 批判迭代 #2 - 2026-01-21 18:11:54

**模块**: 计费中台

**分数**: 0.75 / 1.0

**结果**: ✅ 通过


### 发现的问题

- 接口幂等设计不完整：仅说明按requestId命中成功记录直接返回，但未定义requestId重复且历史状态为PENDING/PROCESSING/FAILED时的处理（返回处理中、阻塞等待、允许重试生成新结果、还是返回固定错误码），也未说明transactionId与requestId的唯一性约束关系，容易导致并发下重复计费或返回不一致结果。
- 金额与净额/全额计算存在歧义：响应字段对netAmount/grossAmount的描述为（amount - feeAmount或amount）和（amount + feeAmount或amount），但未给出在feeBearer=PAYER/RECEIVER与settlementMode=NET/GROSS四种组合下的明确公式与示例，容易造成上下游对到账金额理解不一致。
- 规则管理缺少落地数据模型：文档提到配置中心（费率规则）与feeRuleVersion，但未定义规则的结构、匹配优先级/冲突解决、版本发布与回滚策略、以及calculate与quote是否必须使用同一版本，导致实现与审计不可控。
- 错误码与HTTP语义未定义：仅描述4xx/5xx类别，没有给出具体错误码枚举、字段级校验错误返回结构、以及幂等冲突（同requestId不同payload）应返回的明确错误，影响调用方可编程处理与排障。
- Outbox发布与一致性细节不足：sync_outbox仅给出状态与重试字段，但未说明与业务表写入的事务边界（是否同库同事务）、发布幂等键（eventId/transactionId去重）、消费者幂等建议、以及FAILED后的死信/人工介入流程，可能导致重复投递或丢消息。
- 依赖账户系统的降级策略风险未约束：允许基于缓存账户信息降级计算，但未明确哪些账户属性是计费必需、缓存一致性/TTL、以及在账户状态变化（冻结/注销）时如何避免错误计费，存在合规与资金风险。


### 改进建议
补齐可执行的契约与一致性设计：1）幂等：定义requestId唯一约束、同requestId不同请求体的处理（返回409并附冲突字段摘要）、对PROCESSING的并发请求返回202或阻塞等待策略，并明确transactionId是否也需唯一及其与requestId关系；2）金额公式：用表格明确四种（feeBearer x settlementMode）下payer/receiver实际出入账金额、netAmount/grossAmount含义，并给出至少2个示例（含fee=0与封顶封底）；3）规则：给出规则结构（维度、费率类型、min/max、舍入）、匹配优先级与冲突规则、版本选择策略（quote返回version并要求calculate携带或服务端锁定）、以及审计追溯字段；4）错误处理：定义统一错误响应（code/message/details/requestId/transactionId）、列出关键错误码（参数、账户不可用、规则未命中、幂等冲突、依赖超时等）与HTTP映射；5）Outbox：明确同事务写入、事件唯一ID与去重策略、发布重试与死信处理、下游消费幂等要求；6）降级：限定可降级的场景与必需账户属性、缓存TTL与失效策略，并在账户状态不可确认时默认拒绝计费。

---

## 批判迭代 #1 - 2026-01-22 16:10:47

**模块**: 计费中台

**分数**: 0.50 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Section 'Interface Design' is hollow (title only, no substance).
- Section 'Data Model' is hollow (title only, no substance).
- Inconsistency: The glossary defines '清结算' as an alias for '清结算/计费中台', but the module design treats '计费中台' as a separate module that provides results to '清结算'. This creates a naming and responsibility conflict.
- Missing key logic consideration: No details on how fee rules are stored, queried, or applied (e.g., rule engine, configuration management).
- Missing key logic consideration: No details on how the module handles idempotency for fee calculation requests.
- Missing key logic consideration: No details on how the module ensures data consistency when notifying downstream systems.
- Ambiguous statement: The boundary description '不涉及资金的扣划、账户余额管理或会计分录记录' is clear, but the dependency on '清结算' is not detailed enough to confirm this separation.


### 改进建议
1. Populate the 'Interface Design' section with concrete API endpoints (e.g., POST /api/v1/fee/calculate), request/response payloads, and event definitions. 2. Define the 'Data Model' section with at least a core table for fee rules and a table for fee calculation records. 3. Clarify the relationship with the '清结算' module as defined in the glossary to resolve the naming and responsibility overlap. 4. Elaborate on the business logic to describe the rule engine, idempotency mechanisms, and failure recovery strategies. 5. Ensure the sequence diagram accurately reflects the clarified dependencies and data flow.

---

## 批判迭代 #2 - 2026-01-22 16:11:21

**模块**: 计费中台

**分数**: 0.80 / 1.0

**结果**: ✅ 通过


### 发现的问题

- Completeness: 'Error Handling' section lacks concrete error codes and specific retry/fallback strategies for external dependencies.
- Consistency: The document states '清结算' is an alias for '清结算/计费中台', implying a combined module, but the design treats '计费中台' as a sub-module. The relationship and boundaries are ambiguous and not clearly aligned with the glossary.
- Feasibility: The design mentions consuming events 'TBD' and publishing events, but lacks details on event schema, idempotency handling for consumers, and the 'reliable message delivery mechanism' is only vaguely mentioned.
- Clarity: The core workflow mentions 'priority' for rule matching but does not define the priority criteria (e.g., specificity of payer/payee type). The term '最具体' is ambiguous.
- Diagram Validity: The Mermaid diagram is present and renders, but it omits the '缓存服务' dependency mentioned in the text and does not show the error/fallback paths described in the logic.


### 改进建议
1. Define specific error codes (e.g., FEE_RULE_NOT_FOUND, INVALID_PARAMETER) and detail fallback logic for cache/database failures. 2. Explicitly define the architectural relationship with '清结算' (e.g., a service within the same bounded context) to resolve glossary ambiguity. 3. Specify the event payload schema for 'FeeCalculatedEvent' and detail the idempotent consumption pattern. 4. Clarify the rule matching algorithm, including the exact dimensions and precedence order. 5. Update the sequence diagram to include cache lookup and error response paths for completeness.

---

