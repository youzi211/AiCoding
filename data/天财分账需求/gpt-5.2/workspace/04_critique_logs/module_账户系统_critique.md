# 批判日志: 账户系统

## 批判迭代 #1 - 2026-01-21 18:11:02

**模块**: 账户系统

**分数**: 0.00 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口设计为空（API端点、请求/响应、事件均为TBD），无法评审对外契约与幂等、鉴权、版本管理等关键点。
- 数据模型为空（表/集合、关键字段均为TBD），无法验证账户唯一性、状态机、能力配置等规则如何落库与约束。
- 关键业务规则缺失：未定义账户唯一性维度（按商户+角色+场景？）与幂等键/重复请求处理策略，无法保证不重复开户。
- 关键状态机缺失：仅提到冻结/注销等异常，但未定义账户状态枚举、允许的状态迁移、各状态下允许的操作与返回码。
- 与下游通知机制不明确：时序图中有'通知账户开通完成'，但接口设计的事件/回调为TBD，缺少可靠投递（重试、去重、死信）与一致性方案。
- 与上游三代的数据对齐缺失：未说明三代提供的商户/开户信息字段、校验规则、以及不一致时的主数据归属与冲突解决策略。
- 错误处理过于笼统：提到重试与事务补偿，但未定义跨系统一致性边界（本地事务+Outbox/Saga等）、重试退避、幂等与补偿触发条件。
- 能力配置描述不落地：如'支持分账、绑定多张银行卡、设置默认提现卡'未明确哪些能力由账户系统控制、哪些由钱包系统控制，缺少能力模型与权限校验点。
- 缺少安全与合规要求：未定义鉴权（调用方身份、签名/Token）、敏感字段保护、审计日志与权限隔离，账户系统作为底层能力风险较高。
- 缺少非功能性指标：未给出SLA、超时、限流、并发开户峰值、数据库唯一索引与性能方案，影响可行性评估。


### 改进建议
补齐可评审的最小可行设计：1）接口设计：明确REST端点（如开户、查询、变更状态、配置能力）、请求/响应字段、错误码、幂等键（例如requestId或merchantId+role+scene）、鉴权方式与版本策略；同时定义对钱包系统的通知方式（事件或回调）及其可靠性（Outbox、重试、去重、死信）。2）数据模型：给出账户表、账户能力表、账户标签/角色表、状态变更流水表等核心表结构与关键字段（accountId、merchantId、roleType、scene、status、capabilities、createdAt等），并用唯一索引/约束落地'唯一性'规则。3）业务逻辑：定义账户状态枚举与状态迁移图，明确各场景（归集/批付/会员结算）开户时的初始状态与必填关联关系；给出重复开户、并发请求、下游不可用时的处理流程。4）一致性与失败处理：明确跨系统一致性方案（例如本地事务+Outbox发布事件，钱包消费幂等；或Saga补偿），定义重试策略（次数、退避、可重放）与补偿动作。5）边界与职责：明确账户系统与钱包系统在'绑卡/默认卡/能力开关'上的职责边界与权限校验点，并补充安全、审计与非功能指标。

---

## 批判迭代 #2 - 2026-01-21 18:12:22

**模块**: 账户系统

**分数**: 0.25 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 幂等设计不完整：仅声明使用X-Request-ID做幂等校验，但未定义幂等记录的存储结构（表字段、唯一索引、过期策略）、幂等命中时返回的响应一致性规则（是否返回首次响应体、状态码）、以及并发重复请求下的竞态处理（先查后插会产生并发窗口）。
- 账户唯一性规则与状态定义存在冲突：文档写同一merchantId+roleType+scene只能存在一个有效（ACTIVE或INITIAL）账户，但数据库唯一索引对所有状态生效，会导致CLOSED后无法重新开户，且与状态机允许CLOSED后可能需要重开不一致。
- 接口语义缺失关键约束：PATCH /status与PATCH /capabilities未定义权限模型（谁可操作、按merchantId隔离还是按token scope）、并发控制（ETag/版本号/乐观锁）、以及幂等要求（写操作都需X-Request-ID但接口定义未明确这些PATCH也必须携带）。
- 错误码与幂等行为不一致：定义DUPLICATED_REQUEST为409且表示请求已处理，但时序图中重复请求返回已创建账户信息，未明确此时应返回200还是409，导致调用方难以实现稳定重试策略。
- 与上游三代的数据校验不可行描述：写到MERCHANT_NOT_FOUND（与三代校验）以及定期与三代校验merchant基础信息，但未说明校验接口/触发时机/超时降级策略；在开户链路中同步校验会影响P99<200ms目标且缺少缓存与降级方案。
- Outbox投递机制缺少可落地细节：未定义Outbox表结构、事件去重键（eventId或accountId+eventType+version）、投递顺序保证（同一account的状态变更事件顺序）、以及消费者幂等依据字段，容易导致重复或乱序带来的下游状态回退。
- 能力模型不清晰：account_capability.config为JSON但未定义schema与校验规则；capability_code枚举与场景默认能力规则只覆盖部分场景，MEMBER_SETTLEMENT标注TBD导致核心业务能力缺口。
- 状态机缺少关键迁移与约束说明：未说明INITIAL如何触发到ACTIVE（由谁、何时、是否依赖下游绑定成功），也未说明CLOSED是否允许查询/恢复；同时写到INITIAL和CLOSED不允许业务操作，但未定义哪些接口属于业务操作（例如capabilities配置是否允许在INITIAL）。
- 安全与合规部分存在空洞：权限隔离标注TBD，但该模块涉及跨商户账户管理与状态变更，缺少明确的鉴权授权与审计字段定义（operator来源、是否记录调用方、IP等）。


### 改进建议
补齐可实现的幂等与并发控制：新增idempotency表（request_id唯一、request_hash、response_body、status、expired_at），所有写接口强制X-Request-ID并定义命中时返回200+首次响应体；对账户创建使用单条INSERT依赖唯一索引并捕获冲突返回已存在账户信息或明确409语义。调整唯一性与重开策略：若允许CLOSED后重开，改为部分唯一索引（仅对非CLOSED生效）或引入is_active/valid_flag；同时明确CLOSED后的行为。完善PATCH接口契约：定义权限模型（按merchantId隔离、token scope/角色）、加入乐观锁（version字段或If-Match/ETag），并明确状态迁移校验与错误码。落地Outbox：定义outbox表（event_id唯一、aggregate_id=account_id、event_type、payload、created_at、published_at、retry_count、next_retry_at），规定同一account按created_at或sequence递增投递；事件payload包含version用于下游幂等与顺序处理。补齐三代校验与性能：明确开户时是否强依赖三代查询，若需要则加缓存与超时降级（例如仅校验merchantId格式+异步补偿校验），并给出超时/失败时的返回策略。明确能力config schema与MEMBER_SETTLEMENT默认能力与流程，避免TBD进入主干设计。补齐审计与安全：定义operator取值（来自token的sub/clientId）、记录调用方、traceId，并完成权限隔离方案。

---

## 批判迭代 #1 - 2026-01-22 16:12:11

**模块**: 账户系统

**分数**: 0.70 / 1.0

**结果**: ✅ 通过


### 发现的问题

- Section 'Interface Design' is hollow (TBD for API endpoints, request/response structures, and events).
- Section 'Data Model' is hollow (TBD for tables and key fields).
- Inconsistent account type naming: Design mentions '天财收款账户/天财接收方账户/01待结算账户/04退货账户' but glossary defines '01待结算账户' and '04退货账户' as aliases; the design should use the primary terms.
- Missing key logic consideration for handling concurrent operations: Mentions 'database transaction or optimistic lock' but lacks specifics on implementation (e.g., version column, retry strategy).
- Missing key logic consideration for eventual consistency in distributed scenarios: Stated but no strategy (e.g., event sourcing, compensation) is provided.
- Diagram validity issue: Mermaid sequence diagram is present but lacks a participant for '业务核心' which is a key upstream module for the '账务核心' as per context, showing an incomplete system view.


### 改进建议
1. Populate the 'Interface Design' section with concrete REST endpoints (e.g., POST /api/v1/accounts), detailed request/response schemas (JSON examples), and specific event names (e.g., AccountCreatedEvent, BalanceChangedEvent). 2. Define the 'Data Model' with actual table names, primary keys, indexes, and detailed field definitions (data types, constraints). 3. Standardize terminology: Use '待结算账户' and '退货账户' as primary terms, with type codes (01, 04) as attributes. 4. Elaborate on concurrency control: Specify the use of a 'version' field in the account_balance table for optimistic locking and describe the retry logic. 5. Describe the eventual consistency mechanism, such as using idempotent event handlers or a saga pattern for cross-system updates. 6. Update the sequence diagram to include all relevant upstream modules (e.g., 业务核心) and downstream modules (e.g., 对账单系统) as per the dependency context.

---

