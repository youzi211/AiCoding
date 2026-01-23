# 批判日志: 认证系统

## 批判迭代 #1 - 2026-01-21 18:10:52

**模块**: 认证系统

**分数**: 0.00 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口设计为空（API端点、请求/响应结构、事件均为TBD）。请补齐至少打款验证发起、回填校验、人脸核验的具体HTTP方法、路径、鉴权方式、请求字段、响应字段、错误码与幂等策略。
- 数据模型为空（表/集合、关键字段均为TBD）。请定义验证流水（verification_id）、用户标识、银行卡要素、随机打款金额、状态机、重试次数、过期时间、第三方渠道流水号、审计字段等，并说明索引与唯一约束。
- 打款验证关键逻辑缺失：未定义金额生成范围与规则、回填次数上限、锁定与解锁策略、有效期与超时处理、重复发起的幂等键、并发回填的竞态处理。请补齐状态流转与边界条件。
- 人脸验证关键逻辑缺失：未定义活体检测要求、相似度阈值与可配置性、失败重试与冷却时间、图片/视频格式与大小限制、超时与回调模式、第三方不可用降级策略。请补齐可执行的校验与风控规则。
- 安全与合规要求缺失：未说明敏感信息（身份证号、人脸影像、银行卡号）的加密存储/传输、脱敏日志、访问控制、数据保留与删除策略、审计追踪。请补齐安全控制与合规约束。
- 与上游电子签约平台的交互契约不清：未定义同步/异步模式、回调或轮询机制、状态查询接口、幂等与重放保护。请明确契约与时序（含状态查询与回调）。
- 错误处理不够可落地：仅描述原则，缺少标准化错误码体系、可重试判定、重试退避策略、告警与监控指标（成功率、延迟、渠道错误率）。请补齐错误码与可观测性设计。


### 改进建议
按可交付标准补齐TBD部分并落地为可实现的接口与数据：1）定义REST接口清单：发起打款（含幂等键）、查询状态、提交回填、发起人脸核验、查询人脸结果；为每个接口给出字段级请求/响应示例与错误码。2）建立验证流水数据模型与状态机（INIT, TRANSFER_PENDING, TRANSFER_SUCCESS, VERIFY_SUCCESS, VERIFY_FAILED, EXPIRED, LOCKED等），明确过期时间、回填次数上限、并发控制与幂等规则。3）补齐人脸核验的活体、阈值、重试与降级策略，以及媒体格式限制与超时策略。4）补齐安全合规：PII加密、KMS密钥管理、日志脱敏、最小权限、审计与数据保留周期。5）补齐可观测性与运维：指标、日志、链路追踪、告警阈值、渠道熔断与重试退避。6）在时序图中补充状态查询/回调与失败分支，确保与接口契约一致。

---

## 批判迭代 #2 - 2026-01-21 18:12:29

**模块**: 认证系统

**分数**: 0.35 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口鉴权仅描述API Key，缺少密钥生命周期与安全控制（签名机制、时间戳与重放防护、Key轮换与权限范围），无法满足高风险认证接口的安全要求；需补充请求签名（如HMAC）、nonce或timestamp校验、Key分级与最小权限策略。
- 幂等设计不一致：仅在打款发起接口声明Idempotency-Key，但数据模型又以request_id做唯一索引且称与幂等键关联；需明确幂等键的唯一来源与优先级（Idempotency-Key或request_id），并规定冲突处理与返回语义（重复请求返回同一verification_id与状态）。
- 回调机制定义不完整：callback_url存在但未定义回调事件类型、回调payload、签名验签、重试策略、幂等与去重、回调失败补偿；当前仅写TBD，导致异步链路不可落地。
- 人脸核验接口与流程矛盾：接口名为POST /verification/face/verify且响应为已受理PROCESSING，但业务逻辑又称支持同步返回和异步回调两种模式且由callback_url指定；需拆分为同步与异步两种明确契约（例如sync=true或单独endpoint），并定义在10秒超时下的返回码与状态。
- 人脸媒体字段定义不清：face_image_data声明可为image或video frame，但又允许MP4视频；缺少字段区分（image_base64与video_base64或media_url）、编码格式、分片上传方案与大小校验错误码，难以实现与测试。
- 打款验证关键外部依赖未定义：未说明与银行或第三方打款通道的交互协议、回执字段（渠道流水号、到账确认方式）、以及TRANSFER_SUCCESS的判定依据；需明确是以渠道返回成功即视为成功，还是以到账回执/对账确认后才进入TRANSFER_SUCCESS。
- 金额与精度处理存在风险：filled_amount为字符串且未定义精度与比较规则（分为单位、四舍五入、前导零、币种）；random_amount加密存储但未说明如何进行安全比较（解密后比较或哈希），易引入精度与安全漏洞。
- 状态机与接口缺少约束：未明确哪些状态允许调用verify接口、重复verify如何处理、以及查询接口在不同状态下的字段返回（例如random_amount是否永不返回）；需给出状态到接口的允许矩阵与错误码映射。
- 人脸失败冷却与并发控制未落地：仅描述同一用户1分钟内不允许再次发起，但数据模型与索引未支持快速判定（缺少按user_id+type+created_at或last_attempt_at索引/字段），也未说明分布式并发下的原子校验方式。
- 数据合规描述缺少可执行细节：提到7天删除原始人脸图像，但数据模型未包含存储位置或是否落库；需明确是否存对象存储、存储key、删除任务与审计记录字段，否则无法验证合规执行。
- 错误码体系缺少HTTP状态码映射与可重试语义：仅列出业务码，未规定4xx/5xx、以及哪些错误可重试（例如THIRD_PARTY_ERROR是否返回503并携带retry_after），影响调用方实现。
- 接口示例时间与有效期不一致：示例expires_at为固定日期（2023-10-27）但业务规则为创建后15分钟有效；需在示例中体现相对有效期或说明示例为静态样例，避免误导。
- 事件发布/消费为TBD但模块依赖任务调度与回调，缺少最小可用的事件或任务定义（过期清理、回调投递、渠道结果回写）；需补齐至少核心事件或任务清单与触发条件。


### 改进建议
优先补齐可落地的契约与安全控制：1）统一幂等策略（明确Idempotency-Key与request_id关系、唯一性范围、重复请求返回规则）并在所有可重试接口支持幂等；2）定义回调规范（回调endpoint、payload字段、签名算法与密钥、重试与退避、去重键、回调失败补偿与死信处理）；3）明确人脸核验同步/异步模式（参数或拆分接口），给出10秒超时下的状态与返回码；4）补充与打款通道/人脸通道的交互与状态判定依据（TRANSFER_SUCCESS与到账确认、渠道流水号字段使用）；5）完善金额与精度规则（以分为单位的整数传输与存储，比较规则与错误码），并说明加密比较实现；6）给出接口-状态允许矩阵与错误码/HTTP映射；7）为冷却与并发增加可执行的数据字段与索引（last_attempt_at或基于created_at的原子校验），并说明分布式锁或条件更新策略；8）把合规要求落到存储与删除实现（人脸数据是否落库或对象存储、存储key、删除任务与审计字段）。

---

## 批判迭代 #1 - 2026-01-22 16:11:11

**模块**: 认证系统

**分数**: 0.55 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Completeness: Missing required 'Interface Design' section content (API endpoints, request/response structures, events). Deduct -0.2.
- Completeness: Missing required 'Data Model' section content (tables, key fields). Deduct -0.2.
- Completeness: 'Error Handling' section lacks specific error codes, retry limits, and fallback strategies. Deduct -0.1.
- Consistency: Module name '认证系统' is not found in the provided global glossary of system roles/participants. Deduct -0.15.
- Consistency: The document mentions '第三方人脸比对服务' as a downstream dependency, but this entity is not defined in the glossary. Deduct -0.15.
- Feasibility: The '人脸验证流程' lacks technical details on how identity information (name, ID) is obtained and matched with the face image. Deduct -0.2.
- Feasibility: The '关键边界情况处理' for face verification mentions '降级策略' but does not specify what the fallback is. Deduct -0.2.
- Clarity: The 'Overview' states the module's boundary '不涉及具体的电子签约协议生成', yet the 'Data Model' section says it interacts with the electronic signing platform. This is contradictory regarding scope. Deduct -0.1.
- Diagram Validity: The provided Mermaid sequence diagram only covers the '打款验证' flow. A critical diagram for the '人脸验证' flow is missing. Deduct -0.2.


### 改进建议
1) Populate the 'Interface Design' section with concrete API endpoints (e.g., POST /api/v1/verification/payment, POST /api/v1/verification/face), request/response payloads, and event definitions. 2) Define the core data model: tables like `verification_records` with fields for request_id, user_id, type (PAYMENT/FACE), status, result, external_ref_id, etc. 3) Align module naming and dependencies with the glossary; consider if '认证系统' is a sub-component of another defined system like '行业钱包'. 4) Specify the technical integration for face verification: how to call the third-party service, data format, and concrete fallback actions (e.g., fallback to manual review). 5) Add a sequence diagram for the face verification workflow involving the business core, this module, the electronic signing platform, and the face service. 6) Elaborate error handling with specific error codes, retry policies (e.g., max 3 retries with exponential backoff), and user communication strategies.

---

## 批判迭代 #2 - 2026-01-22 16:11:39

**模块**: 认证系统

**分数**: 0.80 / 1.0

**结果**: ✅ 通过


### 发现的问题

- Section 'Dependencies' is missing from the required sections list, causing a completeness deduction.
- The 'verification_type' field in the data model uses values (PAYMENT, FACE) which are inconsistent with the glossary terms ('打款验证', '人脸验证') and the API naming ('payment', 'face'). This is a minor inconsistency.
- The business logic for '打款验证流程' mentions generating a random amount but does not specify where or how this amount is stored for later verification, which is a missing key logic consideration.
- The '消费事件: TBD' in the interface design is ambiguous and lacks detail, constituting an ambiguous statement.
- The '人脸验证流程' diagram does not explicitly show the 'VerificationCompletedEvent' being published, which is a key part of the interface design.


### 改进建议
1. Add a 'Dependencies' section to the document structure to improve completeness. 2. Align the 'verification_type' enum values with the glossary or API naming (e.g., 'PAYMENT_VERIFICATION', 'FACE_VERIFICATION'). 3. Clarify in the business logic or data model where the generated random amount for payment verification is stored (e.g., in 'request_data' or a dedicated field). 4. Specify the events to be consumed, even if preliminary, instead of 'TBD'. 5. Update the sequence diagrams to include the publication of the 'VerificationCompletedEvent' upon success/failure to show the complete flow.

---

## 批判迭代 #1 - 2026-01-22 17:46:47

**模块**: 认证系统

**分数**: 0.35 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section: Interface Design (API endpoints, request/response structures, events). Deduct 0.2.
- Missing required section: Data Model (tables, key fields, relationships). Deduct 0.2.
- Business Logic section lacks concrete algorithms, state management (e.g., pending verification status), and specific retry/fallback details. Deduct 0.2.
- Inconsistent with glossary: Module states it's called by '电子签约平台', but glossary defines '电子签约平台' as a system that calls '认证系统'. This is a minor alignment but the design lacks details on how this interaction is structured (e.g., API contracts). Deduct 0.15.
- Feasibility issue: No consideration for data persistence of verification attempts, audit trails, or idempotency for retries. Deduct 0.2.
- Clarity issue: 'TBD' (To Be Determined) is used extensively, making the design hollow and non-actionable. Deduct 0.1 for each of Interface and Data Model sections (total 0.2).
- Diagram validity: Sequence diagram is present and correctly formatted, but it's overly simplistic and omits critical steps like request validation, result persistence, and error flows. Deduct 0.1.


### 改进建议
1. Define concrete REST/GraphQL endpoints (e.g., POST /api/v1/verification/payment, POST /api/v1/verification/face). 2. Specify request/response payloads with example fields and data types. 3. Design data models for storing verification requests, results, and evidence (e.g., verification_id, user_info, status, amount, transaction_id, facial_match_score, created_at). 4. Elaborate business logic: detail the steps for generating/validating random amounts, integrating with third-party services, handling user lockouts after failed attempts. 5. Expand the sequence diagram to include validation, async callbacks from bank services, and database interactions.

---

## 批判迭代 #2 - 2026-01-22 17:47:45

**模块**: 认证系统

**分数**: 0.75 / 1.0

**结果**: ✅ 通过


### 发现的问题

- Missing required section: 'Dependencies' is not explicitly listed as a section in the document structure, though content exists. Deduct for completeness.
- Inconsistency with glossary: The document states the module is called by '电子签约平台', but the glossary defines '电子签约平台' as the system responsible for calling the authentication system. This is not an inconsistency but a correct dependency. However, the module's role is defined as a 'system' in the glossary, but the design doc refers to it as a 'module'. This is a minor terminology inconsistency.
- Feasibility issue: The business logic for '人脸验证' returns a result immediately in the response, but the status is set to 'PROCESSING'. This is contradictory; a synchronous call returning a result should have a final status (SUCCESS/FAILED). The asynchronous flow implied by 'PROCESSING' is not aligned with the described API response.
- Feasibility issue: The data model for 'face_verification_details' includes 'id_card_no' which is redundant as it should be linkable via 'verification_id' to the main request or user info. This is a design smell but not a critical flaw.
- Clarity issue: The '业务规则与验证' mentions locking a user after N failures, but does not define what constitutes '短时间内' or specify the lock duration ('如1小时') as a configurable parameter, leaving ambiguity.
- Clarity issue: The '发布/消费的事件' section lists '消费事件: TBD.' This is an incomplete placeholder, reducing clarity.
- Diagram validity: The Mermaid sequence diagram is present and correctly formatted. No issues.


### 改进建议
1. Add an explicit 'Dependencies' section header to the document structure for completeness. 2. Clarify the '人脸验证' API flow: either make it truly asynchronous (return a PROCESSING status and provide results via event/polling) or make it synchronous (return final result and status in the initial response). Update the data model and sequence diagram accordingly. 3. Define concrete time windows and configurable parameters for user lockout rules. 4. Replace 'TBD' in the events section with concrete events this module would consume, if any. 5. Consider removing redundant fields (e.g., id_card_no) from detail tables to normalize the data model.

---

