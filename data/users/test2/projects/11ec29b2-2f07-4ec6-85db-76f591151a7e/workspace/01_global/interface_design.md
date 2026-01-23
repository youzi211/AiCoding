## 4.1 对外接口
本系统对外部系统（天财）暴露的接口如下。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | TBD | 三代 | 接收天财发起的开户请求。 | TBD |
| POST | TBD | 三代 | 接收天财发起的账户关系绑定请求。 | TBD |
| POST | TBD | 三代 | 接收天财发起的业务开通（如开通付款）请求。 | TBD |
| POST | /api/v1/transactions/split | 交易系统 | 接收天财发起的单笔分账请求。 | TBD |
| POST | /api/v1/transactions/member-settlement | 交易系统 | 接收天财发起的会员结算请求。 | TBD |
| POST | /api/v1/transactions/batch-payment | 交易系统 | 接收天财发起的批量付款请求。 | TBD |
| GET | /api/v1/transactions/{transactionId} | 交易系统 | 供天财查询交易处理状态。 | TBD |

## 4.2 模块间接口
本系统内部各模块之间的关键调用接口如下。

| Method | Path | Module (调用方) | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /v1/accounts | 三代 -> 行业钱包 | 调用钱包系统为商户开立天财收款账户或天财接收方账户。 | TBD |
| POST | /v1/bindings | 三代 -> 行业钱包 | 调用钱包系统建立总部与门店、或付款方与接收方之间的绑定关系。 | TBD |
| POST | /v1/split-requests | 业务核心 -> 行业钱包 | 调用钱包系统执行分账处理。 | TBD |
| GET | /v1/accounts/{accountNo}/balance | 行业钱包 -> 账户系统 | 查询指定账户的余额。 | TBD |
| PUT | /v1/accounts/{accountNo}/status | 行业钱包 -> 账户系统 | 更新账户状态（如冻结/解冻）。 | TBD |
| POST | /api/v1/settlement/execute | 交易系统 -> 清结算 | 请求执行交易清分与结算。 | TBD |
| POST | /api/v1/freeze/account | 风控 -> 清结算 | 请求执行商户账户冻结。 | TBD |
| POST | /api/v1/freeze/transaction | 风控 -> 清结算 | 请求执行特定交易资金冻结。 | TBD |
| GET | /api/v1/statement/data | 对账单系统 -> 清结算 | 查询对账单所需的原始数据。 | TBD |
| POST | /api/v1/accounting/entries | 账户系统 -> 账务核心 | 提交记账指令。 | TBD |
| POST | /api/v1/accounting/reversals/{original_biz_no} | 清结算 -> 账务核心 | 对指定原业务流水号的交易发起冲正。 | TBD |
| POST | /v1/contracts | 行业钱包 -> 电子签约平台 | 发起签约流程（用于关系绑定或开通付款）。 | TBD |
| POST | /v1/contracts/{contractId}/callback/auth | 电子签约平台 -> 认证系统 | 回调认证结果。 | TBD |
| POST | /v1/fee/calculate | 行业钱包 -> 计费中台 | 计算手续费。 | TBD |
| POST | /v1/fee/deduct | 计费中台 -> 账户系统 | 发起手续费扣减。 | TBD |
| POST | /api/v1/split-order | 交易系统 -> 业务核心 | 转发天财发起的单笔分账请求。 | TBD |
| POST | /api/v1/split-order/batch | 交易系统 -> 业务核心 | 转发天财发起的批量分账请求。 | TBD |
| POST | /api/v1/verify/payment | 电子签约平台 -> 认证系统 | 请求进行打款验证。 | TBD |
| POST | /api/v1/verify/face | 电子签约平台 -> 认证系统 | 请求进行人脸验证。 | TBD |
| POST | /api/v1/batch-payments | 交易系统 -> 代付系统 | 转发批量付款请求。 | TBD |