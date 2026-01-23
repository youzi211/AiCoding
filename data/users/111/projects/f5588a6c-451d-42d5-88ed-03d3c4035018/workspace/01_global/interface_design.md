## 4.1 对外接口
系统对外部业务方（如天财）暴露的接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/institution/create | 三代 | 接收天财提交的机构开户申请。 | TBD |
| POST | /api/v1/audit/submit | 三代 | 提交业务审核（开户、关系绑定）。 | TBD |
| GET | /api/v1/audit/result/{auditNo} | 三代 | 查询审核结果。 | TBD |
| POST | /api/v1/split | 业务核心 | 用于处理分账请求。 | TBD |
| POST | /v1/batch-payments | 代付系统 | 创建并提交批量付款批次。 | TBD |
| GET | /v1/batch-payments/{batchId} | 代付系统 | 查询批量付款批次状态及详情。 | TBD |
| GET | /v1/batch-payments/{batchId}/items | 代付系统 | 查询批次内所有付款明细项状态。 | TBD |
| POST | /api/v1/statements/generate | 对账单系统 | 异步生成对账单。 | TBD |
| GET | /api/v1/statements | 对账单系统 | 查询对账单列表。 | TBD |
| GET | /api/v1/statements/{statementId}/download | 对账单系统 | 下载对账单文件。 | TBD |
| GET | /api/v1/statements/{statementId}/status | 对账单系统 | 查询对账单生成状态。 | TBD |

## 4.2 模块间接口
系统内部各模块之间相互调用的接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/auth/validate | 三代 | （内部）接口调用鉴权验证。 | TBD |
| GET | /api/v1/institution/{institutionId}/permissions | 三代 | 查询机构接口权限。 | TBD |
| POST | /api/v1/settlement/process | 清结算 | 处理分账交易结算。 | TBD |
| POST | /api/v1/settlement/refund/deduct | 清结算 | 执行退货扣款。 | TBD |
| POST | /api/v1/settlement/freeze | 清结算 | 执行账户冻结。 | TBD |
| GET | /api/v1/settlement/statement/generate | 清结算 | 触发结算单生成。 | TBD |
| POST | /api/v1/signing/process | 电子签约平台 | 创建签约流程。 | TBD |
| GET | /api/v1/signing/process/{process_id} | 电子签约平台 | 查询签约流程状态。 | TBD |
| POST | /api/v1/signing/template | 电子签约平台 | 上传协议模板。 | TBD |
| POST | /api/v1/verification/payment | 认证系统 | 发起打款验证。 | TBD |
| POST | /api/v1/verification/face | 认证系统 | 发起人脸验证。 | TBD |
| GET | /api/v1/verification/result/{requestId} | 认证系统 | 查询验证结果。 | TBD |
| POST | /api/v1/fee/calculate | 计费中台 | 手续费计算接口。 | TBD |
| GET | /api/v1/fee/rules/{ruleId} | 计费中台 | 查询费率规则详情接口。 | TBD |
| POST | /api/v1/risk/assessment | 风控 | 接收风险判定请求。 | TBD |
| GET | /api/v1/risk/freeze-orders/{freezeOrderId} | 风控 | 查询冻结指令状态。 | TBD |
| POST | /api/v1/risk/rules | 风控 | 创建风险规则（管理接口）。 | TBD |
| PUT | /api/v1/risk/rules/{ruleId} | 风控 | 更新风险规则（管理接口）。 | TBD |