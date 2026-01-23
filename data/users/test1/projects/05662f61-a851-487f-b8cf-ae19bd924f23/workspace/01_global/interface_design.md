## 4.1 对外接口
本系统对外部（如天财平台、商户客户端）暴露的接口如下。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/tiancai/ledger | 天财 | 发起分账请求 | TBD |
| POST | /api/tiancai/account/open | 天财 | 发起开户请求 | TBD |
| POST | /api/tiancai/relationship/bind | 天财 | 发起关系绑定请求 | TBD |
| GET | /api/tiancai/requests/{requestId} | 天财 | 查询业务请求状态 | TBD |
| POST | /api/v1/merchant/register | 三代 | 接收天财提交的商户入驻申请 | TBD |
| POST | /api/v1/merchant/audit | 三代 | 提交商户审核结果 | TBD |
| POST | /api/v1/business/config | 三代 | 接收天财的业务配置请求（如开通分账、归集） | TBD |
| GET | /api/v1/merchant/{merchantId} | 三代 | 查询商户信息及状态 | TBD |
| PUT | /api/v1/merchant/{merchantId}/info | 三代 | 更新商户信息 | TBD |
| POST | /api/v1/biz-core/transactions/split | 业务核心 | 处理天财分账请求 | TBD |
| POST | /api/v1/biz-core/transactions/collection | 业务核心 | 处理资金归集请求 | TBD |
| GET | /api/v1/biz-core/transactions/{transactionId} | 业务核心 | 查询交易状态 | TBD |
| POST | /api/v1/transactions/split | 交易系统 | 处理单笔分账请求 | TBD |
| POST | /api/v1/transactions/collect | 交易系统 | 处理资金归集请求 | TBD |
| POST | /api/v1/transactions/member_settlement | 交易系统 | 处理会员结算请求 | TBD |
| POST | /api/v1/transactions/batch_payment | 交易系统 | 处理批量付款请求 | TBD |
| GET | /api/v1/transactions/{transaction_id} | 交易系统 | 查询交易状态 | TBD |
| POST | /api/v1/batch-payments | 代付系统 | 创建并提交一个新的批量付款请求 | TBD |
| GET | /api/v1/batch-payments/{batchId} | 代付系统 | 根据批次号查询批量付款的详细状态和结果 | TBD |
| POST | /api/v1/batch-payments/{batchId}/retry-failed-items | 代付系统 | 对指定批次中失败的付款项进行重试 | TBD |
| POST | /api/v1/user-id | 用户中心 | 生成用户标识 | TBD |
| POST | /api/auth/login | 钱包APP/商服平台 | 用户认证与会话 | TBD |
| POST | /api/auth/refresh-token | 钱包APP/商服平台 | 用户认证与会话 | TBD |
| GET | /api/accounts/{accountId} | 钱包APP/商服平台 | 账户信息查询 | TBD |
| GET | /api/accounts/list | 钱包APP/商服平台 | 账户信息查询 | TBD |
| POST | /api/relationship/initiate | 钱包APP/商服平台 | 关系绑定流程（发起绑定） | TBD |
| GET | /api/relationship/status/{requestId} | 钱包APP/商服平台 | 关系绑定流程（查询状态） | TBD |
| POST | /api/transactions/split | 钱包APP/商服平台 | 交易发起（发起分账） | TBD |
| POST | /api/transactions/batch-payment | 钱包APP/商服平台 | 交易发起（发起批量付款） | TBD |
| GET | /api/agreement/url | 钱包APP/商服平台 | 协议签署（获取电子签章H5页面URL） | TBD |
| POST | /api/agreement/callback | 钱包APP/商服平台 | 协议签署（接收签署结果回调） | TBD |
| GET | /api/transactions/history | 钱包APP/商服平台 | 交易记录查询 | TBD |

## 4.2 模块间接口
本系统内部各模块之间相互调用的接口如下。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/settlement/orders | 清结算 | 接收业务核心发起的结算请求 | TBD |
| POST | /api/v1/freeze/requests | 清结算 | 接收行业钱包发起的商户冻结或交易冻结申请 | TBD |
| GET | /api/v1/accounts/{accountNo}/balance | 清结算 | 从账户系统同步指定账户的余额与状态信息 | TBD |
| POST | /api/v1/statements/details | 清结算 | 向对账单系统推送动账明细 | TBD |
| POST | /api/v1/accounts | 账户系统 | 创建账户（开户） | TBD |
| PATCH | /api/v1/accounts/{accountId}/status | 账户系统 | 更新账户状态（如冻结/解冻） | TBD |
| POST | /api/v1/accounts/{accountId}/debit | 账户系统 | 执行资金扣减 | TBD |
| POST | /api/v1/accounts/{accountId}/credit | 账户系统 | 执行资金增加 | TBD |
| GET | /api/v1/accounts/{accountId}/balance | 账户系统 | 查询账户余额 | TBD |
| POST | /api/v1/accounting/entry | 账务核心 | 执行单笔记账 | TBD |
| POST | /api/v1/accounting/batch-entry | 账务核心 | 执行批量记账 | TBD |
| POST | /v1/statements/generate | 对账单系统 | 提交对账单生成请求 | TBD |
| GET | /v1/statements/{statement_id} | 对账单系统 | 查询对账单生成状态与详情 | TBD |
| GET | /v1/statements/{statement_id}/download | 对账单系统 | 获取对账单文件的下载链接或文件流 | TBD |
| POST | /api/v1/fee/calculate | 计费中台 | 手续费计算。接收业务请求，返回手续费计算结果及清分方案 | TBD |
| POST | /api/v1/settlement/execute | 计费中台 | 清分执行。根据已确定的清分方案，驱动账务核心与账户系统完成资金划转 | TBD |
| POST | /api/v1/authentication/payment | 认证系统 | 发起打款验证 | TBD |
| POST | /api/v1/authentication/face | 认证系统 | 发起人脸验证 | TBD |
| GET | /api/v1/authentication/result/{request_id} | 认证系统 | 查询认证结果 | TBD |
| POST | /v1/agreements | 电子签章系统 | 发起协议签署。接收业务方请求，创建签署会话 | TBD |
| GET | /v1/agreements/{agreementId} | 电子签章系统 | 查询协议签署状态及详情 | TBD |
| POST | /v1/agreements/{agreementId}/cancel | 电子签章系统 | 取消进行中的签署流程 | TBD |
| POST | /v1/templates | 电子签章系统 | 上传或更新协议模板（内部管理接口） | TBD |
| GET | /v1/templates/{templateId} | 电子签章系统 | 获取协议模板内容 | TBD |
| POST | /api/v1/risk/dispose | 风控 | 接收风险处置请求 | TBD |
| GET | /api/v1/risk/freeze-records/{id} | 风控 | 查询冻结记录详情 | TBD |