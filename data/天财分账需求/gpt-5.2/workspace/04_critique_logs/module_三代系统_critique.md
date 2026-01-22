# 批判日志: 三代系统

## 批判迭代 #1 - 2026-01-21 18:19:46

**模块**: 三代系统

**分数**: 0.00 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口设计缺失鉴权与调用方身份识别方案：需明确三代系统对天财的鉴权方式（如API Key、mTLS、签名、网关JWT）、权限范围、重放防护（与X-Request-ID关系）以及返回401/403的条件与错误码。
- 错误码体系不完整且与下游不对齐：文档仅举例MERCHANT_NOT_FOUND/INVALID_SCENE，但未给出三代系统对外完整错误码、HTTP映射、可重试性、以及与账户系统（DUPLICATED_REQUEST/ACCOUNT_ALREADY_EXISTS等）和钱包系统（DUPLICATE_REQUEST等）错误码的映射与透传策略。
- 幂等设计落地不足：仅声明使用X-Request-ID，但数据模型中account_opening_request.request_id与split_forward_record.request_id的来源、唯一约束冲突处理、并发重复请求的锁策略（唯一索引+事务/幂等表）、以及重复请求返回的响应体一致性未定义。
- 请求ID链路追踪不一致：对外GET /v1/splits/{requestId}使用上游R2，但内部转发到钱包系统使用W_R2；未明确查询接口如何从R2映射到W_R2并处理钱包侧requestId变化或返回不同requestId的情况，导致可追溯性与查询可靠性不足。
- 状态机定义不完整且与查询返回不一致：split_forward_record.status仅到WALLET_SUCCESS/WALLET_FAILED，但查询示例返回status=CORE_SUCCESS与transactionId，三代系统自身并不调用业务核心，无法保证拿到CORE_SUCCESS语义；需统一状态枚举与来源（钱包系统/业务核心）并定义终态集合。
- 金额与精度规范缺失：接口示例amount为100.00（小数），但未规定最小单位（分/元）、精度与舍入规则、以及与下游钱包系统/清结算的单位一致性，存在资金类系统重大风险。
- 数据模型关键约束与索引缺失：merchant表未定义merchant_id唯一约束与status枚举；split_forward_record缺少currency、feeBearer、arrivalMode、businessRef等关键字段，导致无法实现幂等重放返回一致响应与审计对账；缺少按request_id、wallet_system_request_id的索引与唯一约束说明。
- 异步结果同步机制未闭环：仅写轮询或事件监听，但发布/消费事件均为TBD；未定义轮询频率、超时策略、终止条件、补偿与告警、以及钱包系统结果事件（如SplitTransferResultEvent）接入后的幂等消费与状态更新规则。
- 与上游模块设计存在不一致：钱包系统接口要求API Key鉴权，但三代系统转发调用钱包系统时未描述如何携带X-API-Key/签名；同时钱包系统返回requestId为wallet_req_xxx，而三代系统示例中wallet_system_request_id生成规则与返回值不一致，需明确以谁为准。
- 开户流程边界与术语存在冲突风险：概述称三代不处理账户绑定/签约/账务，但数据模型与流程未说明开户成功后由谁触发钱包系统的关系绑定（钱包系统依赖AccountOpenedEvent来自账户系统）；三代调用账户系统POST /v1/accounts后是否需要等待事件、如何处理账户INITIAL到ACTIVE的激活与可用性未说明。
- 接口契约缺少字段校验规则：未定义merchantId/roleType/scene的枚举范围与大小写、businessRef唯一性要求、remark长度、金额范围、币种限制、以及payer/payee角色校验（例如COLLECTION场景付方必须STORE收方必须HEADQUARTERS）在三代是否校验还是完全下沉到钱包系统。
- 时序图与接口路径存在潜在不一致：轮询部分使用GET /v1/splits/W_R2，但三代对外查询是GET /v1/splits/R2；图中未体现R2到W_R2的映射查询步骤，容易误导实现。


### 改进建议
1) 补齐对外安全与鉴权：明确天财到三代的鉴权（推荐网关JWT或mTLS+签名），定义重放防护（时间戳+nonce+签名）与X-Request-ID的关系，并给出401/403错误码与审计字段（clientId/tenantId）。2) 定义三代系统对外统一错误码表：包含HTTP映射、是否可重试、客户端动作；同时给出与账户系统/钱包系统错误码的映射与透传规则（哪些透传、哪些转换、哪些屏蔽）。3) 落地幂等：为account_opening_request.request_id与split_forward_record.request_id建立唯一索引，采用事务插入+唯一冲突返回已存响应（建议增加idempotency_record或在记录表中存response_body/response_code），并定义并发重复请求的处理。4) 明确requestId映射与查询：规定对外requestId=上游X-Request-ID；内部生成wallet_system_request_id并持久化映射；GET查询先查本地映射再查钱包系统；若钱包系统返回不同requestId，以本地wallet_system_request_id为准并记录钱包返回值字段。5) 统一状态机：定义三代侧split状态（RECEIVED/FORWARDED/WALLET_PROCESSING/WALLET_SUCCESS/WALLET_FAILED/UNKNOWN_TIMEOUT等）与终态；查询接口返回三代状态并可附带钱包侧状态字段，避免使用CORE_SUCCESS等不属于三代职责的语义。6) 资金字段规范化：明确金额单位（建议分，整型），或若保留DECIMAL则规定精度DECIMAL(20,2)、舍入规则、最小/最大金额、币种仅CNY等，并与下游契约一致。7) 补齐数据模型字段与索引：split_forward_record增加currency、fee_bearer、arrival_mode、business_ref、remark、wallet_response_code/message、wallet_request_id、wallet_transaction_id等审计字段；为request_id与wallet_system_request_id建立唯一索引；merchant表补充唯一约束与status枚举。8) 闭环异步同步：确定采用事件优先（消费钱包系统SplitTransferResultEvent）+轮询兜底；定义轮询间隔、最大时长、退避、超时置为SUSPENDED并告警；实现事件幂等表（processed_event）与状态更新规则。9) 对齐下游调用契约：在三代到钱包系统调用中补充X-API-Key/签名等必需头；明确超时、重试、熔断与降级策略，并在错误处理章节给出可操作配置。10) 更新时序图：显式展示R2到W_R2映射查询步骤，并补充事件驱动分支（钱包事件回推更新三代状态），确保图与接口实现一致。

---

## 批判迭代 #2 - 2026-01-21 18:21:30

**模块**: 三代系统

**分数**: 0.20 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口契约与金额单位自相矛盾：分账请求示例使用"amount": 10000（看似分），但业务规则又写示例"amount: 100.00"仅示意且契约为整数分；同时上游钱包系统文档示例仍为100.00（元）。需要统一对外契约（字段类型、单位、示例）并与钱包系统对齐，否则会导致跨系统金额放大/缩小100倍。
- 查询接口ID语义不一致：三代对外GET /v1/splits/{requestId}使用天财requestId（即X-Request-ID=R2），但轮询钱包GET /v1/splits/{requestId}又可能使用wallet_response_request_id或wallet_system_request_id；同时事件SplitTransferResultEvent的requestId是钱包返回的wallet_req_xxx。需要明确三代对外path参数到底是天财requestId还是三代内部requestId，并定义稳定映射与返回字段，否则调用方无法可靠查询。
- 错误码映射规则不合理且会误导重试：将账户系统的INVALID_ACCOUNT_STATUS等业务错误转换为DOWNSTREAM_UNAVAILABLE会把不可重试的业务错误伪装成可重试，导致上游无效重试与告警噪音。需要按业务/系统错误分类映射，并保留可诊断的错误码与message。
- 安全设计缺少可落地细节：声明mTLS+JWT+签名+timestamp+nonce防重放，但未定义签名算法、签名串规范、nonce存储/过期策略、允许的时间偏移窗口、以及在多实例部署下如何共享nonce去重（仅靠DB还是缓存）。缺少这些会导致实现不可互通或存在重放窗口。
- 幂等与并发处理缺少关键实现约束：描述"事务中插入记录后调用下游"会导致长事务/锁持有与吞吐下降；同时未说明并发重复请求在唯一索引冲突时如何原子读取并返回response_body（避免读到空/半成品）。需要改为先落库短事务（RECEIVED）再异步调用下游，或使用状态机+乐观锁。
- 事件模型在本模块中是TBD：接口部分发布/消费事件写TBD，但业务逻辑又强依赖消费钱包系统SplitTransferResultEvent与processed_event表。需要在本模块文档中补齐消费事件定义（topic、payload字段、幂等键、重试/DLQ策略）与发布事件（若无则明确不发布）。
- 状态枚举与上游不一致：三代查询返回status为WALLET_SUCCESS/WALLET_FAILED，但钱包系统查询返回CORE_SUCCESS/FAILED等；轮询终止条件写CORE_SUCCESS/FAILED，三代自身状态机又包含WALLET_PROCESSING等。需要定义清晰的状态映射表与对外稳定枚举，否则调用方无法理解终态含义。
- 数据模型缺少关键约束与字段：merchant表未体现tenantId但鉴权要求tenantId并声称多租户；split_forward_record未定义business_ref唯一性/去重策略（同一订单重复请求如何处理）；缺少traceId/tenantId/clientId落库字段以支撑审计与排障。
- 时序图与文字存在细节冲突：时序图中开户流程"更新开户状态为SUCCESS"后直接返回"受理成功"，但接口成功响应示例status=PROCESSING；需要统一开户接口是同步成功还是异步受理，并定义查询接口（当前没有开户查询接口）。
- 轮询与重试策略缺少关键边界：未定义重试触发条件（哪些错误/超时）、最大重试总时长、与幂等键的关系、以及UNKNOWN_TIMEOUT后如何对账修复；也未说明钱包系统返回404/RELATIONSHIP_NOT_FOUND等业务错误时三代应如何对外返回与是否终止轮询。


### 改进建议
1) 先冻结对外契约：明确amount单位（分）与类型（integer），更新三代与钱包系统文档示例与字段说明，补充校验规则（最大值、精度、币种）。2) 明确ID体系：对外GET /v1/splits/{requestId}固定使用天财X-Request-ID；在响应与查询结果中新增walletRequestId字段（钱包requestId）与forwardRequestId字段（三代转发X-Request-ID），并给出三者映射与查询优先级。3) 补齐事件章节：在本模块定义消费SplitTransferResultEvent的payload、topic、幂等键eventId、重试与DLQ、以及processed_event表的唯一约束与清理策略；若不发布事件则明确不发布。4) 修正错误码映射：建立业务错误透传/映射表（例如INVALID_ACCOUNT_STATUS应映射为ACCOUNT_STATUS_INVALID或INVALID_PARAMETER且不可重试），系统错误才映射为DOWNSTREAM_UNAVAILABLE；对外响应统一携带traceId。5) 调整幂等与事务：避免在同一DB事务内调用下游；采用短事务落库(RECEIVED) + 异步转发（或出站Outbox）+ 状态机/乐观锁更新；并定义并发冲突时的原子读取返回逻辑。6) 安全落地：定义签名算法（如HMAC-SHA256）、canonical string、nonce去重存储（Redis+TTL或DB表+TTL清理）、允许时间偏移窗口与错误码。7) 统一状态机：给出钱包状态到三代对外状态的映射表，并保证轮询终止条件与对外枚举一致；同时补齐开户查询接口或将开户接口明确为同步返回SUCCESS并与时序图/示例一致。

---

