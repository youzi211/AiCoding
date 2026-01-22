# 批判日志: 行业钱包系统

## 批判迭代 #1 - 2026-01-21 18:16:32

**模块**: 行业钱包系统

**分数**: 0.00 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口设计为空（API端点、请求响应结构、发布事件均为TBD）。请补齐至少：分账请求API（含幂等键requestId）、关系绑定查询/维护API、签约回调接收API、查询签约状态API，并给出字段级请求响应示例与错误码。
- 数据模型为空（表/集合、关键字段均为TBD）。请定义最少可用的持久化模型：业务关系绑定表（store_merchant_id、hq_merchant_id、scene、status、unique约束）、签约状态表（wallet_request_id、signing_id、payer/receiver、scene、status、expires_at）、事件去重表（event_id、event_type、processed_at）以及必要索引。
- 事件契约不完整：仅声明消费AccountOpenedEvent，但未定义事件字段、版本、幂等键、重放语义、死信处理与补偿流程。请明确AccountOpenedEvent的payload字段（accountId、merchantId、roleType、scene、status、eventId、occurredAt）并定义钱包系统发布的关键事件（如RelationshipBoundEvent、SplitTransferRequestedEvent或SigningRequestedEvent）及其用途。
- 与上游模块不一致：账户系统已发布AccountStatusChangedEvent，但钱包系统设计未消费该事件，导致账户冻结/注销后关系与准入校验可能滞后。请增加对AccountStatusChangedEvent的消费与本地状态同步策略（或明确每次实时查询账户系统且不落本地状态）。
- 枚举与术语不一致：钱包系统文档使用中文场景名（归集/批量付款/会员结算）与角色值（STORE/HEADQUARTERS），而账户系统接口使用英文枚举（COLLECTION/BATCH_PAYMENT/MEMBER_SETTLEMENT）。请统一对外API与内部模型的枚举，并给出映射表与兼容策略。
- 签约触发规则表述不清且可能不一致：文档写明（批量付款、会员结算）首次向特定收方付款前需签约，但未定义签约粒度（按付方-收方-场景？按付方-场景？按资金用途？）。请明确唯一键与复用规则，并在数据模型中体现。
- 关键流程缺少可执行的失败补偿设计：仅提到交易悬挂与人工介入，但未定义状态机、重试边界、幂等与对账触发条件。请补充钱包系统侧的交易编排状态机（RECEIVED、VALIDATED、SIGNING_PENDING、SIGNING_SUCCESS、CORE_REQUESTED、CORE_SUCCESS、FAILED、SUSPENDED）及每个状态的重试/超时/补偿动作。
- 下游调用契约缺失：调用业务核心POST /v1/transfers需要的字段（payerAccountNo、payeeAccountNo、feeBearer、arrivalMode等）在钱包系统侧未定义如何生成与校验，也未说明与计费中台的交互方式（试算/正式计费由谁调用）。请明确：钱包系统是否调用计费中台，还是由业务核心调用；并补齐字段来源与校验规则。
- 时序图覆盖面不足且缺少关键分支：仅展示归集与首次签约的批量付款示例，未展示签约失败/超时、重复回调、业务核心幂等重试、AccountOpenedEvent重复投递与死信处理等关键路径。请补充至少一个包含失败与重试的时序图或在现有图中增加alt分支。
- 错误处理缺少可落地的错误码与对外契约：仅描述策略，没有定义对上游（天财/三代）返回的错误码、HTTP状态、可重试标识与traceId。请建立错误码表并明确哪些错误可重试、是否需要调用方改参、以及如何查询处理结果（基于requestId）。


### 改进建议
先把最小可交付版本（MVP）补齐为可实现的契约与模型：1）定义对外REST API：POST /v1/splits（分账请求，必含requestId幂等键、scene、payerMerchantId、payeeMerchantId、amount、feeBearer、arrivalMode、businessRef），GET /v1/splits/{requestId}（查询结果），POST /v1/signings/callback（接收电子签约平台回调，含signing_id与wallet_request_id），GET /v1/relationships（查询绑定）；2）落地数据表：relationship_binding（唯一约束store+scene）、signing_record（唯一约束wallet_request_id，另建payer+payee+scene复用索引）、processed_event（event_id唯一）、split_transaction（requestId唯一+状态机）；3）补齐事件：消费AccountOpenedEvent与AccountStatusChangedEvent并定义字段与幂等；发布RelationshipBoundEvent与SplitTransferResultEvent（用于异步通知/对账）；4）明确签约粒度与复用规则（建议按payerMerchantId+payeeMerchantId+scene+fundPurpose或按业务要求简化），并定义签约超时与重试（定时查询电子签约平台GET /api/v1/signings/{id}）；5）明确计费责任边界（钱包系统调用计费中台试算并透传到业务核心，或完全由业务核心调用，二选一并写清字段）；6）补充失败分支时序图与对外错误码表（含可重试标识、traceId、幂等语义与最终一致性查询方式）。

---

## 批判迭代 #2 - 2026-01-21 18:18:22

**模块**: 行业钱包系统

**分数**: 0.15 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 幂等键定义与落库字段不一致：POST /v1/splits 说明幂等键为请求头 X-Request-ID，但 split_transaction.request_id 被描述为外部请求ID/幂等键且示例又使用 path/requestId 查询。需要明确一个唯一幂等键来源（header或body字段），并在表字段、API参数、错误码DUPLICATE_REQUEST语义中保持一致。
- 与上游电子签约平台接口不一致：钱包系统文档写定时轮询 GET /api/v1/signings/{id}，但自身回调时序与发起接口在文档中写 POST /signings（未带 /api/v1 前缀），且电子签约平台定义发起为 POST /api/v1/signings。需要统一签约平台的URL前缀、路径与字段命名（signing_id vs signingId等）。
- 与上游电子签约平台幂等头不一致：钱包系统回调幂等键写 X-Idempotency-Key，签约平台设计中回调到钱包系统要求携带 X-Idempotency-Key，但签约平台发起接口幂等头为 Idempotency-Key。需要明确钱包系统调用签约平台时使用的幂等头名称与值，并在双方文档中对齐。
- 与上游账户系统鉴权方式不一致：钱包系统接口鉴权为 API Key，但账户系统上游设计为 Authorization Bearer Token。钱包系统作为账户系统调用方时应说明使用Bearer Token或通过网关换取凭证，否则集成不可落地。
- 关键字段缺失导致流程不可实现：签约平台发起签约请求需要 user_id、user_mobile、callback_url、auth_type、fund_purpose 等，但钱包系统的 /v1/splits 请求体未提供 fundPurpose、用户标识/手机号、回调地址来源规则。需要补齐字段或定义从商户资料/三代获取的映射与校验。
- 业务核心对接字段不一致：钱包系统描述调用业务核心 POST /v1/transfers 透传计费结果，但业务核心接口定义字段为 payerAccountNo/payeeAccountNo 等账户号；钱包系统API与数据模型仅有 payerMerchantId/payeeMerchantId，未定义如何解析到账户号/账户ID（从账户系统查询哪个接口、缓存策略、失败处理）。
- 计费中台对接字段不一致：计费中台需要 payerAccountId/receiverAccountId、settlementMode(GROSS/NET)，钱包系统仅有 merchantId与 arrivalMode(NET)且未提供账户ID映射与GROSS枚举。需要定义枚举映射与字段转换，并说明当计费中台要求transactionId时由谁生成、何时生成。
- 关系绑定模型无法支持文档中的签约粒度：签约复用规则按 payerMerchantId + payeeMerchantId + scene + fundPurpose，但 split_transaction 未包含 fund_purpose 字段，signing_record 有 fund_purpose 但 /v1/splits 未提供该字段且未说明默认值/枚举。需要在交易表与API中补齐 fundPurpose 并建立一致的校验与索引策略。
- 事件驱动关系绑定逻辑不完整：AccountOpenedEvent payload包含 merchantId、roleType、scene，但 relationship_binding 需要 storeMerchantId 与 hqMerchantId。仅凭单个merchantId无法推导绑定对端，文档未说明绑定关系的来源（天财/三代配置、额外API、事件中是否包含对端ID）。需要补充绑定建立的输入来源与一致性策略。
- 错误处理与状态机存在冲突：错误处理章节写业务校验失败立即置为 FAILED 且不可重试，但状态机还包含 SIGNING_PENDING、SIGNING_SUCCESS 等中间态；对于 SIGNING_REQUIRED 被定义为400且不可重试，但实际应返回可引导签约并进入SIGNING_PENDING而非FAILED。需要明确哪些错误是终态失败、哪些是流程分支（需要签约）并调整状态迁移与HTTP语义。
- 回调安全细节不足：签约回调仅提到 X-Signature 验签，但未定义签名算法、参与字段、重放防护（timestamp/nonce）、以及签名密钥管理与轮换。需要补齐可实现的验签规范与失败响应策略。
- 时序图与接口字段不一致：时序图中 POST /v1/splits (requestId=req1) 将requestId放在参数中，但接口定义幂等键在header X-Request-ID；同时签约发起在图中为 POST /signings（wallet_request_id=req2）与接口清单不一致。需要修正时序图以匹配最终接口契约。
- 缺少关键非功能与数据一致性设计：未定义split_transaction与signing_record的并发更新控制（乐观锁/状态条件更新）、回调与定时轮询的竞态处理（例如回调先到/轮询先到）、以及重复调用业务核心的防重策略（基于requestId映射到核心requestId）。这些是核心可行性缺口。


### 改进建议
先做一次契约对齐与最小可实现闭环：1）统一幂等键：明确外部幂等键为header X-Request-ID（或body.requestId二选一），并在split_transaction.request_id、GET查询路径参数、DUPLICATE_REQUEST语义中完全一致；2）补齐跨系统映射：定义从merchantId到accountNo/accountId的查询流程（调用账户系统GET /v1/accounts?merchantId&roleType&scene），并在调用计费中台与业务核心时使用其要求的账户标识与枚举（arrivalMode与settlementMode映射）；3）签约闭环：在/v1/splits请求中增加fundPurpose与签约所需用户标识来源规则（userId/userMobile从三代/商户资料获取），并统一签约平台接口路径为/api/v1/signings、幂等头名称与值；4）关系绑定输入来源补全：说明store与hq的绑定由哪个上游提供（例如天财/三代配置接口或事件扩展字段），否则AccountOpenedEvent无法建立relationship_binding；5）状态机与错误码重构：将SIGNING_REQUIRED从终态失败改为流程分支（返回202或业务码并进入SIGNING_PENDING），并用条件更新+乐观锁保证回调/轮询/重试的并发安全；6）补充验签规范：定义X-Signature算法（如HMAC-SHA256）、签名串字段、timestamp/nonce校验与重放窗口，以及密钥管理；7）修正时序图与文档一致，确保所有mermaid步骤使用最终字段与路径。

---

