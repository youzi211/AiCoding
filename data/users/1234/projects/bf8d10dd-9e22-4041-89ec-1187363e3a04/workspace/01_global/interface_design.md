## 4.1 对外接口
系统对外部合作方（天财）暴露的接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /v1/merchant/register | 三代 | 接收天财提交的商户入网申请 | TBD |
| GET | /v1/merchant/status/{applicationId} | 三代 | 查询商户入网申请状态 | TBD |
| POST | /v1/account/open | 三代 | 触发天财专用账户开户流程 | TBD |
| POST | /api/v1/split-account/execute | 业务核心 | 执行分账交易 | TBD |
| GET | /v1/statements | 对账单系统 | 查询账单列表 | TBD |
| GET | /v1/statements/{statement_id} | 对账单系统 | 获取指定账单的元数据信息 | TBD |
| GET | /v1/statements/{statement_id}/download | 对账单系统 | 下载账单文件 | TBD |
| POST | /v1/statements/regenerate | 对账单系统 | 触发历史账单重新生成 | TBD |

## 4.2 模块间接口
系统内部各模块之间的调用接口。

| Method | Path | Module (调用方) | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/wallet/accounts | 三代 | 创建天财专用账户（收款账户或接收方账户）。 | TBD |
| POST | /api/v1/wallet/transfers | 业务核心 | 处理天财分账（转账）请求。 | TBD |
| GET | /api/v1/wallet/accounts/{accountNo}/status | 业务核心/认证系统 | 查询账户状态。 | TBD |
| GET | /api/v1/wallet/relationships | 业务核心/代付系统 | 查询付方与收方之间的绑定关系状态。 | TBD |
| POST | /v1/accounts | 行业钱包 | 开立天财专用账户。 | TBD |
| POST | /v1/accounts/{accountId}/upgrade | 行业钱包 | 升级账户状态或权限。 | TBD |
| GET | /v1/accounts/{accountId}/balance | 行业钱包/清结算 | 查询账户余额。 | TBD |
| POST | /v1/transfers | 行业钱包/清结算 | 执行账户间资金划转。 | TBD |
| POST | /v1/accounts/{accountId}/freeze | 风控 | 冻结账户资金。 | TBD |
| POST | /v1/accounts/{accountId}/unfreeze | 风控 | 解冻账户资金。 | TBD |
| POST | /api/v1/settlement/initiate | 业务核心 | 发起结算处理。 | TBD |
| GET | /api/v1/settlement/query/{settlement_id} | 业务核心 | 查询结算单状态。 | TBD |
| GET | /api/v1/refund-account/{merchant_id} | 行业钱包 | 查询商户退货账户信息。 | TBD |
| POST | /api/v1/signing/initiate | 行业钱包/认证系统 | 接收行业钱包发起的签约请求，返回签约任务ID和状态。 | TBD |
| GET | /api/v1/signing/task/{taskId} | 行业钱包/认证系统 | 查询指定签约任务的当前状态和详情。 | TBD |
| POST | /api/v1/verification/callback/{type} | 银行通道/人脸识别服务 | 接收银行通道打款验证结果回调或人脸识别服务比对结果回调。 | TBD |
| POST | /api/v1/template/query | 行业钱包 | 供内部管理或行业钱包查询可用的协议模板。 | TBD |
| POST | /api/v1/fee/calculate | 清结算 | 核心计费接口 | TBD |
| POST | /api/v1/bindings | 行业钱包 | 发起关系绑定请求 | TBD |
| POST | /api/v1/verifications | 电子签约平台 | 发起特定认证（打款/人脸）请求 | TBD |
| GET | /api/v1/bindings/{bindingId} | 行业钱包 | 查询关系绑定状态 | TBD |
| POST | /api/v1/payment-activations | 代付系统 | 发起开通付款流程 | TBD |
| POST | /api/v1/batch-payments | 天财 | 接收并处理批量付款请求。 | TBD |
| POST | /api/v1/risk/transaction/check | 业务核心 | 交易风险检查接口。 | TBD |
| POST | /api/v1/risk/contract/check | 业务核心 | 签约风险检查接口。 | TBD |
| POST | /api/v1/risk/review/callback | 运营后台 | 人工审核结果回调接口。 | TBD |
| POST | /api/v1/auth-relationships | 行业钱包 | 创建授权关系 | TBD |
| GET | /api/v1/auth-relationships/{relationshipId} | 业务核心/代付系统 | 查询授权关系详情 | TBD |
| GET | /api/v1/auth-relationships/validate | 业务核心/代付系统 | 校验授权关系有效性 | TBD |
| PUT | /api/v1/auth-relationships/{relationshipId}/status | 电子签约平台 | 更新授权状态（内部/异步通知使用） | TBD |
| GET | /api/v1/merchants/{merchantId} | 业务核心 | 查询商户详情 | TBD |
| GET | /api/v1/receivers/{receiverId} | 业务核心/代付系统 | 查询接收方详情 | TBD |
| POST | /api/v1/sync/merchants | 三代 | 同步商户信息（供上游系统调用） | TBD |
| POST | /api/v1/sync/receivers | 三代 | 同步接收方信息（供上游系统调用） | TBD |