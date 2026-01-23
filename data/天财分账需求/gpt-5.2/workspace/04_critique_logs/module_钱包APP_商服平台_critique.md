# 批判日志: 钱包APP/商服平台

## 批判迭代 #1 - 2026-01-21 18:11:00

**模块**: 钱包APP/商服平台

**分数**: 0.20 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口设计章节为TBD，缺少任何可评审的API端点、鉴权方式、请求/响应字段、错误码与幂等策略，导致前后端无法对齐与联调。
- 数据模型章节为TBD，未定义前端需要的核心展示与交互数据结构（如分账单、签约流程、账户信息、账单明细、草稿），也未说明缓存/本地存储与字段来源映射。
- 事件/通知机制描述不一致：业务逻辑写'轮询或接收通知'，但接口设计的事件为TBD，且时序图中ES直接通知APP，缺少明确的回调通道设计（WebHook到后端再转发、还是前端轮询钱包系统）。
- 依赖关系不完整：上游列出账户系统、对账单系统，但时序图未体现；下游模块为TBD，未说明与统一登录、风控、埋点、消息推送等常见前端依赖的边界与集成方式。
- 关键业务规则缺失：未定义场景枚举值与角色权限矩阵、手续费承担方/到账模式/资金用途等字段的前端校验与展示规则，也未说明与协议模板选择的映射关系。
- 缺少关键失败与安全考虑：未说明登录与会话管理、接口签名/Token刷新、敏感信息脱敏、重放与CSRF防护；也未定义签约H5跳转的回跳参数校验与防篡改。
- 草稿与断点续办仅一句话，缺少可执行方案：保存范围、加密、过期策略、跨设备同步与冲突处理、恢复入口与状态机定义均未给出。
- 时序图虽可渲染，但流程可行性不足：认证系统被ES调用的前提与接口边界未说明（是否允许ES直连AS），且缺少钱包系统侧对签约结果的落库与APP查询路径，导致状态一致性无法保证。


### 改进建议
补齐可落地的接口与数据定义：1）列出核心API清单（签约初始化、获取签约页、查询签约状态、发起归集/批付/会员结算、查询交易、查询账单、查询账户与关系、获取错误码映射），为每个接口给出方法、路径、鉴权、幂等键、分页、超时与重试策略、错误码；2）定义前端领域模型与页面所需字段（账户、关系、签约流程、交易单、批次、账单、草稿），明确字段来源与状态枚举；3）明确状态更新机制二选一并画全链路：前端轮询钱包系统（给出轮询间隔与终止条件）或后端接收ES回调再推送/前端查询（给出回调验签与一致性策略）；4）补充权限与规则矩阵（总部/门店在各场景可见性、必填字段、资金用途与协议模板映射、手续费承担方与到账模式展示/校验）；5）补充安全与可靠性（登录会话、Token刷新、H5回跳校验、敏感数据脱敏、草稿加密与过期、失败重试与幂等、批量提交的部分失败处理与可重试粒度）。

---

## 批判迭代 #2 - 2026-01-21 18:11:57

**模块**: 钱包APP/商服平台

**分数**: 0.35 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口设计缺少关键字段与约束：未定义各端点的必填/可选字段、字段类型与枚举（scene、authType、status、arrivalMode等）、金额单位与精度、批量付款文件上传接口与格式（CSV/Excel、编码、字段映射）、以及幂等键requestId在HTTP层的承载方式（header还是body）和幂等有效期。
- 安全设计不完整且与依赖不一致：文档要求所有接口携带Token，但未说明统一登录平台的Token获取/刷新/失效处理的具体机制（refresh token、silent renew、并发刷新互斥），也未说明前端如何存储Token（内存/安全存储）与XSS/CSRF防护策略。
- 轮询方案可行性不足：固定5秒轮询、最长30分钟缺少退避策略、页面不可见/后台时的暂停策略、服务端限流与429处理、以及多标签页/多终端并发轮询的去重方案，容易造成不必要的压力与电量消耗。
- 数据模型描述与实现边界模糊：声明local_draft加密存储但未给出加密方案（Web端无法安全保管密钥、移动端需说明Keychain/Keystore），也未说明缓存一致性策略（账户/关系变更后的失效触发）与多账号切换隔离。
- 业务规则存在关键缺口：仅描述门店仅可见归集（作为付方），但未明确归集的收方约束（是否只能总部）、收方选择来源与校验；批量付款与会员结算的收方名单来源、去重、限额、单笔/单日上限、手续费与到账模式的可选范围均未定义，导致前端校验无法落地。
- 错误处理不够可执行：提到错误码映射表，但未定义错误码结构、国际化/多语言策略、以及前端如何区分可重试与不可重试错误；重试最多3次未说明重试间隔、仅对哪些错误重试、以及幂等与重试的组合策略。
- 与术语表存在一致性风险：术语表区分认证系统与电子签约平台，但时序图中电子签约平台直接调用认证系统且前端也提到回跳参数签名校验，未说明签名的签发方与验签公钥来源（由谁提供、如何轮换），容易与实际集成边界不一致。
- 时序图覆盖不足：仅给出签约流程，未给出交易发起（归集/批付/会员结算）与批量部分失败重试的关键时序，且文档声称类似但缺少关键交互（幂等、状态终态定义、对账单下载/导出）。


### 改进建议
补齐接口契约与可落地细节：为每个API提供请求/响应JSON示例、字段类型/枚举/约束、错误码清单与可重试规则；明确requestId的传递位置与幂等窗口。完善登录与安全：定义Token刷新流程（并发刷新互斥、失败回退登录）、Token存储策略与XSS/CSRF防护；明确H5回跳签名的签发方、验签材料获取与轮换。优化轮询：增加指数退避与抖动、页面不可见暂停、429/5xx处理、单用户多标签页去重（BroadcastChannel/SharedWorker）并给出停止条件与终态枚举。细化业务规则：明确各场景的参与方约束、名单来源、限额/校验、手续费与到账模式的可选范围与默认规则；补充批量文件上传接口、模板与校验、部分失败重试的交互与状态机。补充关键时序图：至少增加交易发起与状态查询、批量部分失败重试、对账单查询/下载的mermaid时序图。

---

## 批判迭代 #1 - 2026-01-22 17:46:43

**模块**: 钱包APP/商服平台

**分数**: 0.60 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Interface Design' content (TBD).
- Missing required section 'Data Model' content (TBD).
- Missing required section 'Error Handling' content (TBD).
- Inconsistency: Module is described as a front-end application but includes backend-like 'Data Model' and 'Business Logic' sections, creating confusion about its architectural role.
- Inconsistency: '下游模块' is marked as TBD, but the glossary defines many downstream systems (e.g., 三代, 行业钱包, 账户系统). The design does not clarify its downstream dependencies.
- Missing key logic consideration: The business logic section lacks details on how user roles (总部, 门店, 一般接收方) and permissions (机构号, APPID) are enforced in the UI and API calls.
- Missing key logic consideration: No clear strategy for handling eventual consistency or idempotency for operations like '分账发起' which may be retried.
- Ambiguous statement: '它是业务指令的发起端和结果展示端，不处理核心业务逻辑.' contradicts the inclusion of a '业务逻辑' section that describes workflows and validations. The scope of logic this module handles is unclear.
- Diagram validity: The sequence diagram is incomplete. It shows a successful flow but does not depict any error paths, retry logic, or interactions with other critical dependencies mentioned (e.g., 电子签约平台, 认证系统, 对账单系统).


### 改进建议
1. Replace all TBD sections with concrete designs. Define API endpoints, request/response structures, and data models (even if they are view models for the frontend). 2. Clarify the module's architectural role: Is it a frontend app, a BFF (Backend for Frontend), or a service? Adjust section content accordingly. 3. Explicitly list downstream modules/services it calls (e.g., 三代, 电子签约平台) and define the interaction contracts. 4. Expand business logic with detailed permission checks, state management for asynchronous operations, and idempotency keys for retries. 5. Update the sequence diagram to include alternative flows for errors and interactions with all key dependencies for the primary use case. 6. Ensure the 'Error Handling' section maps specific error scenarios from downstream systems to user-friendly messages and recovery actions.

---

## 批判迭代 #2 - 2026-01-22 17:47:38

**模块**: 钱包APP/商服平台

**分数**: 0.75 / 1.0

**结果**: ✅ 通过


### 发现的问题

- Section 'Interface Design' contains hollow content: 'Request/Response structure: TBD (由各后端服务定义).'
- Section 'Data Model' is incomplete for a frontend application: lacks details on how view models are structured, populated, and persisted (e.g., local storage for operation status).
- Inconsistency with glossary: The design states '本模块是一个前端应用' and does not directly publish events, but the glossary lists '业务核心' as a downstream module that '接收并存储天财分账等交易数据'. The design's data flow to '业务核心' is unclear.
- Missing key logic consideration for feasibility: No specification for handling session expiration during long-running operations (e.g., status polling, H5 signing flow).
- Missing key logic consideration for feasibility: The '状态一致性' logic mentions polling but does not define polling interval, stop conditions, or handling of app background/foreground transitions.
- Diagram validity issue: The Mermaid sequence diagram includes a participant 'W as 行业钱包' which is mentioned in the glossary but its interaction with the 'G3' participant and the flow of '内部处理分账逻辑' is overly abstract and lacks clarity on error paths.
- Clarity issue: The term '三代' is used throughout as a system role/service but its exact boundaries and responsibilities relative to '行业钱包', '清结算', etc., are ambiguous in the context of this frontend module's interactions.


### 改进建议
1. Replace 'TBD' in the Interface Design with example request/response structures or references to concrete API documentation. 2. Elaborate the Data Model section with example structures for key view models and describe state persistence strategy. 3. Clarify the data flow to '业务核心' - is it via the '三代' interface or a separate call? Update the diagram or description accordingly. 4. Add concrete logic for session management during asynchronous flows and define the polling mechanism (interval, max attempts, stop on success/failure). 5. Refine the sequence diagram to show explicit error return paths from '行业钱包' and other services back to 'G3' and then to the APP.

---

