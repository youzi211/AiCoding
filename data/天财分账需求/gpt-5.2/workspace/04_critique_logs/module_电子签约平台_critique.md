# 批判日志: 电子签约平台

## 批判迭代 #1 - 2026-01-21 18:13:09

**模块**: 电子签约平台

**分数**: 0.00 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口设计为空（请求/响应结构TBD，事件TBD）。请至少给出签约发起、查询状态、回调确认、模板管理等核心API的路径、方法、鉴权、请求字段、响应字段、错误码与幂等策略。
- 数据模型为空（表/集合TBD，关键字段TBD）。请定义签约流程表、协议模板表、签约实例与认证流水关联字段、状态字段、索引与数据保留策略。
- 与上游认证系统的对接细节缺失。认证系统已定义API Key鉴权、Idempotency-Key、verification_id与状态机；电子签约平台未说明如何传递幂等键、如何保存verification_id、轮询还是回调、回调验签与重放防护。
- 签约状态机缺失。仅描述'标记成功/失败'，未定义中间态（INIT、SMS_SENT、H5_OPENED、VERIFYING、CALLBACK_PENDING等）、状态迁移条件、幂等更新与并发控制，容易导致重复回调或状态回退。
- 回调通知钱包系统的可靠性设计不足。仅写'回调失败'，未给出重试策略、退避、死信/补偿任务、回调幂等键、签名校验、超时与最终一致性方案。
- 协议模板选择规则过于抽象。仅提到'场景、资金用途'，未定义枚举、优先级、版本管理、灰度发布、模板生效时间与审计要求，无法落地实现。
- 安全与合规要求缺失。涉及短信、H5、身份认证与协议，需明确TLS、敏感字段加密/脱敏、访问控制、签约证据链（时间戳、IP、UA、签名摘要）、数据留存与删除策略。
- 错误处理不够可执行。未定义错误码、可重试与不可重试分类、对认证系统错误码的映射、用户可见提示与运营可观测字段（trace_id、request_id）。
- 关键边界场景未覆盖：重复发起同一签约（幂等）、用户多端同时操作、认证结果回调晚到/乱序、认证过期、用户取消后认证成功回调、模板变更导致的签约实例一致性。
- 接口与事件均未定义，导致与其他模块集成不可评审。文档声明RESTful但没有任何端点清单，无法验证可行性与一致性。


### 改进建议
按可交付标准补齐最小闭环设计：1）补全REST API清单：签约发起POST /signings、查询GET /signings/{id}、获取H5链接GET /signings/{id}/h5、接收认证回调POST /callbacks/auth、回调钱包系统的出站回调规范（签名、幂等、重试）；为每个接口给出字段、示例、错误码、鉴权与幂等键（request_id或Idempotency-Key）。2）定义数据模型：agreement_template（id、scene、fund_purpose、version、status、content_hash、effective_at）、signing_flow（signing_id、wallet_request_id、user_id、scene、fund_purpose、template_id、status、auth_type、verification_id、callback_status、created_at/updated_at）、outbound_callback_log等，并给出索引与唯一约束（wallet_request_id唯一）。3）明确与认证系统对接：使用API Key鉴权；发起打款验证时透传Idempotency-Key并保存verification_id；优先采用认证系统回调，轮询作为兜底；处理回调验签、重放防护与乱序（基于状态机条件更新）。4）补齐签约状态机与并发控制：定义状态与迁移、终态不可逆、重复请求返回同一signing_id；回调通知钱包系统采用可靠投递（重试+退避+死信+人工补偿），并要求钱包系统回调幂等。5）补齐安全合规与证据链：短信与H5链接短期有效、一次性token；签约证据（时间、IP、UA、模板hash、认证结果摘要）落库；PII加密与日志脱敏；数据留存周期。6）补齐可观测性：trace_id贯穿、关键指标（签约成功率、认证耗时、回调成功率）、告警阈值与审计日志。

---

## 批判迭代 #2 - 2026-01-21 18:14:18

**模块**: 电子签约平台

**分数**: 0.20 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- 接口与状态机存在关键矛盾：状态机定义SUCCESS为终态且不可逆，但业务逻辑写明SUCCESS后状态置为CALLBACK_PENDING；同时signing_flow.status枚举包含CALLBACK_PENDING，导致终态定义与实现冲突。需明确CALLBACK_PENDING是否为独立状态字段（如callback_status）或调整状态机终态定义。
- 回调鉴权字段不一致：模块总体鉴权写API Key，但回调接口鉴权写X-API-Key与X-Signature；同时对外API使用API Key但未说明签名算法/密钥来源/重放窗口。需统一鉴权规范并补充签名计算方式（canonical string、HMAC算法、密钥轮换、时间窗）。
- 与上游认证系统接口对接不一致：电子签约平台文档仅描述'调用认证系统接口'，但未给出将auth_type映射到认证系统具体端点（payment/initiate、face/verify等）的请求字段（银行卡、人脸数据等）来源与传递方式；当前POST /signings请求体也缺少认证所需关键字段。需补齐发起认证所需入参与数据获取方案。
- 幂等设计不完整：POST /signings声明使用Idempotency-Key，但同时又以wallet_request_id做幂等；未定义两者冲突时的优先级与返回语义（同wallet_request_id不同Idempotency-Key或反之）。需给出幂等键选择规则与唯一约束策略。
- 时间与有效期定义冲突/不清：H5链接有效期15分钟，但signing_flow数据保留180天且expires_at字段未明确与15分钟关系；认证系统也有15分钟有效期，未说明两者如何对齐以及过期任务触发条件。需明确各expires_at含义与计算来源。
- 回调钱包系统可靠投递缺少关键细节：仅描述指数退避与最大重试，但未定义哪些HTTP状态码/响应体判定为成功或可重试；未定义超时、幂等冲突、签名校验失败的处理。需补充重试判定矩阵与死信补偿流程。
- 事件设计不完整：消费事件为TBD，但模块依赖消息队列执行异步回调任务；未定义内部任务消息的topic、payload、幂等与去重策略。需补齐事件/消息契约或明确不对外发布仅内部使用。
- 数据模型缺少关键约束与字段定义：signing_flow.evidence为JSON但未定义schema版本与必填字段；sms_token未说明存储形式（明文/哈希）、唯一性与使用次数控制；user_mobile加密但查询/索引策略未说明。需补充字段约束与安全存储方案。
- 状态迁移并发控制描述不足：提到基于status和updated_at的乐观锁，但未给出具体更新条件与失败重试策略；回调重复、轮询与用户多端同时操作可能导致竞争，需定义每个入口的CAS更新规则与幂等返回。
- Mermaid图与文档存在一致性问题：状态机图将CALLBACK_PENDING到[*]标注为'回调成功'，但数据模型还有callback_status字段，且outbound_callback_log也有状态；三者职责边界不清，导致图虽可渲染但语义与实现不一致。需统一以一个状态机表达或拆分为签约状态机+回调投递状态机两张图。


### 改进建议
先做一次'状态与字段归一化'：将签约结果状态（SUCCESS/FAILED/EXPIRED）与回调投递状态（PENDING/SUCCESS/FAILED/RETRYING/DEAD）彻底拆分，签约状态机终态保持不可逆，回调投递用callback_status与outbound_callback_log驱动；同时更新Mermaid状态机与时序图以匹配。其次补齐与认证系统的对接契约：明确auth_type到认证端点的映射、POST /signings需要的认证入参（或说明由钱包系统/用户H5采集并通过哪个接口提交），并给出字段来源与加密传输要求。最后统一安全与幂等：定义API Key与签名的统一规范（算法、header、重放窗口、nonce存储/TTL、密钥轮换），并明确wallet_request_id与Idempotency-Key的优先级与唯一约束；补充回调重试判定矩阵（按HTTP码/业务码）、超时与死信补偿流程、sms_token存储为哈希及一次性校验的原子更新实现。

---

## 批判迭代 #1 - 2026-01-22 16:12:05

**模块**: 电子签约平台

**分数**: 0.60 / 1.0

**结果**: ❌ 未通过


### 发现的问题

- Missing required section 'Interface Design' (API endpoints, request/response, events are TBD).
- Missing required section 'Data Model' (tables, fields are TBD).
- Inconsistent upstream module naming: design mentions '行业钱包/业务核心', glossary lists '业务核心' and '行业钱包' as separate entities.
- Missing key logic consideration: No details on how to select or manage protocol templates.
- Missing key logic consideration: No details on how to generate or manage the unique signing ID and H5 link.
- Missing key logic consideration: No details on how to handle protocol versioning when content changes.
- Ambiguous statement: '边界止于协议生成、签署流程引导、验证集成与签署结果记录' contradicts the design which shows the module itself generates the protocol.
- Diagram validity issue: Sequence diagram is present but lacks critical details like error handling paths and retry logic.


### 改进建议
1. Define concrete API endpoints (e.g., POST /api/v1/sign/initiate, GET /api/v1/sign/status). 2. Define data models (e.g., `signing_contracts` table with fields for id, template_id, parties, status, verification_request_id, signed_at). 3. Clarify the relationship with '行业钱包' and '业务核心' as separate upstream callers. 4. Detail the template selection logic, H5 link generation (including expiration), and protocol versioning strategy. 5. Update the sequence diagram to include error handling branches for failed SMS sending and verification retries.

---

## 批判迭代 #2 - 2026-01-22 16:13:42

**模块**: 电子签约平台

**分数**: 0.80 / 1.0

**结果**: ✅ 通过


### 发现的问题

- Missing explicit 'Error Handling' section in the design document.
- Data model 'parties' field is a JSON blob; lacks a defined schema for validation and querying.
- The 'verification_status' field in the status response is defined as a string but lacks an enumerated type or clear definition.
- The 'SigningCompletedEvent' is published but the consuming modules are listed as 'TBD', creating an incomplete dependency picture.
- The 'protocol_templates' table has a 'party_type' field, but the business logic suggests templates are matched by both 'business_scene' and 'party_type'; the design does not clarify if a template can serve multiple party types.
- The 'verification_request_id' field in 'signing_contracts' is mentioned but its population logic (when and how it's set) is not detailed in the business logic.


### 改进建议
1. Add a dedicated 'Error Handling' section summarizing the error codes and strategies. 2. Define a structured schema (e.g., a separate table or a JSON Schema) for the 'parties' field to ensure data integrity. 3. Define the possible values (enum) for the 'verification_status' field in the API response. 4. Specify which modules are expected to consume the 'SigningCompletedEvent' (e.g., '行业钱包', '业务核心') to complete the dependency graph. 5. Clarify the template matching logic: can one template have multiple 'party_type' values, or is a separate template required for each type? 6. Detail in the business logic when the 'verification_request_id' is populated (e.g., after calling the authentication system) and how it links to the verification record.

---

