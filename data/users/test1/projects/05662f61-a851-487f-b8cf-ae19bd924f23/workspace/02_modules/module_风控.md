# 模块设计: 风控

生成时间: 2026-01-23 17:18:16
批判迭代: 2

---

# 风控模块设计文档

## 1. 概述
- **目的与范围**: 本模块负责接收风险判定请求，根据风险类型与等级执行处置策略，并触发对商户账户或交易资金的冻结。其核心职责是作为风险处置的执行器，协调调用下游系统完成冻结操作。模块边界为接收请求、执行处置逻辑、调用冻结接口并返回结果。
- **设计原则**: 高可用、最终一致性、操作可追溯。

## 2. 接口设计
- **API端点 (REST)**:
    - `POST /api/v1/risk/dispose`: 接收风险处置请求。
    - `GET /api/v1/risk/freeze-records/{id}`: 查询冻结记录详情。
- **请求/响应结构**:
    - **风险处置请求 (Request)**:
        ```json
        {
          "requestId": "string, 唯一请求ID",
          "riskEventId": "string, 风险事件ID",
          "riskType": "MERCHANT|TRANSACTION",
          "riskLevel": "HIGH|MEDIUM|LOW",
          "targetId": "string, 目标ID（商户ID或交易ID）",
          "triggerSource": "RULE_ENGINE|MANUAL",
          "extraInfo": "object, 扩展信息"
        }
        ```
    - **风险处置响应 (Response)**:
        ```json
        {
          "code": "string, 响应码",
          "message": "string, 响应消息",
          "data": {
            "disposeId": "string, 处置记录ID",
            "status": "PROCESSING|SUCCESS|FAILED",
            "freezeRecordId": "string, 冻结记录ID（如已生成）"
          }
        }
        ```
- **发布/消费的事件**:
    - **消费事件**: TBD（例如，来自风控规则引擎的风险事件消息）
    - **发布事件**:
        - `RiskDisposeInitiated`: 风险处置已发起。
        - `FreezeApplied`: 冻结申请已提交至清结算。
        - `RiskDisposeCompleted`: 风险处置完成（成功或最终失败）。

## 3. 数据模型
- **表/集合**:
    1.  **风险处置记录表 (risk_dispose_record)**:
        - 记录每一次风险处置请求的执行过程和结果。
    2.  **冻结记录表 (freeze_record)**:
        - 记录发起的每一笔冻结申请，与处置记录关联。
- **关键字段**:
    - **risk_dispose_record**:
        - `id` (主键), `request_id` (唯一), `risk_event_id`, `risk_type`, `risk_level`, `target_id`, `trigger_source`, `status`, `dispose_strategy`, `request_payload`, `result_payload`, `retry_count`, `error_message`, `created_at`, `updated_at`。
    - **freeze_record**:
        - `id` (主键), `freeze_apply_no` (冻结申请流水号), `dispose_record_id`, `account_type` (账户类型), `account_no` (账户号), `freeze_amount` (冻结金额，交易冻结时使用), `freeze_type` (ACCOUNT_FREEZE|FUND_FREEZE), `freeze_status` (APPLIED|SUCCESS|FAILED|THAWED), `apply_response`, `created_at`。
- **与其他模块的关系**:
    - 通过 `risk_event_id` 与风控规则引擎的风险事件关联。
    - 通过 `freeze_apply_no` 与清结算系统的冻结申请关联。
    - `target_id` 可关联至业务核心的商户或交易数据。

## 4. 业务逻辑
- **核心工作流**:
    1.  **请求接收与验证**: 接收风险处置请求，校验必填字段与枚举值，生成处置记录，状态置为`PROCESSING`。
    2.  **处置策略决策**: 根据`riskType`和`riskLevel`映射到具体的处置策略。
        - **策略映射表**:
            | 风险类型 | 风险等级 | 处置动作 | 目标系统 |
            |---|---|---|---|
            | MERCHANT | HIGH | 冻结账户 | 清结算 |
            | MERCHANT | MEDIUM | 告警并监控 | (内部) |
            | TRANSACTION | HIGH | 冻结资金 | 清结算 |
            | TRANSACTION | MEDIUM | 延迟结算 | TBD |
    3.  **执行处置动作**:
        - **商户冻结**: 根据`targetId`（商户ID）获取其对应的`天财收款账户`信息，组装冻结申请请求，调用**清结算系统**的冻结申请接口。
        - **交易冻结**: 根据`targetId`（交易ID）查询交易详情及已结算的`天财收款账户`，组装资金冻结申请，调用**清结算系统**的冻结申请接口。
    4.  **结果处理与持久化**: 接收清结算系统的响应，更新`freeze_record`状态。若申请成功，更新处置记录状态为`SUCCESS`；若失败，进入重试或失败终态处理。
    5.  **事件发布**: 根据处置结果，发布相应领域事件。
- **业务规则与验证**:
    - 同一`riskEventId`原则上只应触发一次有效处置，需做幂等校验。
    - 发起冻结前，需通过查询确认目标账户状态（如是否已冻结），避免重复操作。
    - 处置策略可配置化（未来扩展）。
- **关键边界情况处理**:
    - **下游调用失败**: 采用指数退避策略进行重试（如最多3次）。超过重试次数后，将处置记录状态置为`FAILED`，并记录详细错误信息。
    - **补偿机制**: 对于最终失败的处置，发布`RiskDisposeFailed`事件，供监控或人工介入处理。考虑引入死信队列存储需人工处理的失败请求。
    - **数据一致性**: 本地记录状态与调用下游系统的操作保证最终一致性。通过定期对账（与清结算系统）修复不一致状态。

## 5. 时序图

```mermaid
sequenceDiagram
    participant 风控规则引擎
    participant 风控模块
    participant DB as 风控数据库
    participant 清结算系统
    participant MQ as 消息队列

    风控规则引擎->>风控模块: POST /dispose (风险处置请求)
    风控模块->>DB: 创建处置记录(PROCESSING)
    风控模块-->>风控规则引擎: 202 Accepted

    par 主流程
        风控模块->>风控模块: 决策处置策略
        风控模块->>DB: 查询/校验目标状态
        风控模块->>清结算系统: 申请冻结账户/资金
        alt 调用成功
            清结算系统-->>风控模块: 返回冻结申请结果
            风控模块->>DB: 创建/更新冻结记录
            风控模块->>DB: 更新处置记录(SUCCESS)
            风控模块->>MQ: 发布FreezeApplied事件
        else 调用失败
            清结算系统-->>风控模块: 返回错误
            风控模块->>风控模块: 判断是否重试
            loop 最多重试3次
                风控模块->>清结算系统: 重试冻结申请
                alt 重试成功
                    清结算系统-->>风控模块: 成功
                    break
                end
            end
            alt 最终成功
                风控模块->>DB: 更新记录(SUCCESS)
                风控模块->>MQ: 发布FreezeApplied事件
            else 最终失败
                风控模块->>DB: 更新处置记录(FAILED)
                风控模块->>MQ: 发布RiskDisposeFailed事件
            end
        end
    end
    风控模块->>MQ: 发布RiskDisposeCompleted事件
```

## 6. 错误处理
- **预期错误情况**:
    1.  **请求无效**: 参数缺失、枚举值错误、格式错误。
    2.  **依赖系统异常**: 清结算系统服务超时、不可用、返回业务失败。
    3.  **数据异常**: 目标账户不存在、账户状态不允许冻结。
    4.  **重复请求**: 同一风险事件被重复触发。
- **处理策略**:
    - **输入错误**: 立即返回`400`错误，并在日志中记录。
    - **下游系统错误**: 采用指数退避重试机制。对于连接超时、5xx错误进行重试；对于明确的业务失败（如账户不存在，4xx错误），不重试，直接记录失败。
    - **幂等性**: 通过`requestId`或`riskEventId`保证接口幂等，避免重复处置。
    - **监控与告警**: 对失败率、重试次数、下游系统健康度设置监控指标和告警阈值。
    - **日志**: 所有关键步骤、请求和响应、错误堆栈均需记录结构化日志，便于追踪。

## 7. 依赖关系
- **上游模块/系统**:
    - **风控规则引擎**: 提供风险判定触发，是本模块的主要调用方。
- **下游模块/系统**:
    - **清结算系统**: 根据本模块的申请，执行对`天财收款账户`或特定交易资金的冻结操作。**（根据术语表修正，冻结申请统一通过清结算系统处理）**
    - **业务核心** (间接): 用于查询交易或商户的详细信息（如需）。
- **内部依赖**:
    - 数据库、消息队列。