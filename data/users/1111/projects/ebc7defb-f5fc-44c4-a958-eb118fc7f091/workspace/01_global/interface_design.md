## 4.1 对外接口
系统对外部业务方（如天财、三代）暴露的接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/fund/allocate | 天财 | 发起分账请求 | TBD |
| POST | /api/v1/fund/member-settlement | 天财 | 发起会员结算请求 | TBD |
| POST | /api/v1/fund/batch-payment | 天财 | 发起批量付款请求 | TBD |
| GET | /api/v1/fund/requests/{request_id} | 天财 | 查询业务请求状态 | TBD |
| POST | /api/v1/fund/requests/{request_id}/retry | 天财 | 重试指定请求 | TBD |
| POST | /api/v1/merchant/onboarding | 三代 | 接收商户入网及天财业务开通申请 | TBD |
| POST | /api/v1/merchant/audit | 三代 | 提交商户资质审核结果 | TBD |
| GET | /api/v1/agency/number/{merchantId} | 三代 | 查询商户分配的机构号 | TBD |
| POST | /api/v1/sync/agency-info | 三代 | 手动触发机构号信息同步 | TBD |
| GET | /api/v1/account/summary | 钱包APP | 获取当前登录商户的账户概览信息 | TBD |
| POST | /api/v1/withdrawal/apply | 钱包APP | 提交提现申请 | TBD |
| GET | /api/merchant/{merchantId}/profile | 商服平台 | 获取商户基本信息（含机构号、风控状态） | TBD |
| GET | /api/merchant/{merchantId}/account | 商服平台 | 获取商户账户详情（余额、动账明细） | TBD |
| GET | /api/merchant/{merchantId}/statements?date={date}&type={type} | 商服平台 | 获取对账单列表或下载链接 | TBD |
| POST | /api/merchant/{merchantId}/withdraw | 商服平台 | 发起提现申请（受业务规则控制） | TBD |

## 4.2 模块间接口
系统内部各模块之间调用的接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/account/open | 行业钱包 | 开户接口。接收来自业务核心的开户请求 | TBD |
| POST | /api/v1/binding/initiate | 行业钱包 | 关系绑定发起接口。接收绑定请求 | TBD |
| POST | /api/v1/transfer/request | 行业钱包 | 分账请求接口。接收天财的分账请求 | TBD |
| GET | /api/v1/account/{accountId}/status | 行业钱包 | 账户状态查询接口 | TBD |
| GET | /api/v1/binding/{bindingId}/status | 行业钱包 | 关系绑定状态查询接口 | TBD |
| POST | /api/v1/accounts | 账户系统 | 开立账户 | TBD |
| PUT | /api/v1/accounts/{accountNo}/upgrade | 账户系统 | 升级账户 | TBD |
| POST | /api/v1/accounts/{accountNo}/actions/debit | 账户系统 | 执行扣款 | TBD |
| POST | /api/v1/accounts/{accountNo}/actions/credit | 账户系统 | 执行加款 | TBD |
| POST | /api/v1/accounts/{accountNo}/actions/freeze | 账户系统 | 执行资金冻结 | TBD |
| POST | /api/v1/accounts/{accountNo}/actions/unfreeze | 账户系统 | 执行资金解冻 | TBD |
| GET | /api/v1/accounts/{accountNo}/balance | 账户系统 | 查询账户余额 | TBD |
| POST | /api/v1/journal/entries | 账务核心 | 接收记账请求，创建会计分录 | TBD |
| GET | /api/v1/journal/entries/{request_id} | 账务核心 | 根据请求ID查询记账结果 | TBD |
| POST | /api/v1/disburse | 代付系统 | 接收代付指令 | TBD |
| GET | /api/v1/disburse/{orderNo}/status | 代付系统 | 查询代付单状态 | TBD |
| POST | /api/v1/disburse/callback | 代付系统 | 接收银行通道异步回调 | TBD |
| POST | /api/v1/verification/payment | 认证系统 | 发起打款验证 | TBD |
| POST | /api/v1/verification/face | 认证系统 | 发起人脸验证 | TBD |
| POST | /api/v1/verification/confirm | 认证系统 | 提交验证信息进行确认 | TBD |
| GET | /api/v1/verification/record/{id} | 认证系统 | 查询验证记录状态 | TBD |
| POST | /v1/agreement/initiate | 电子签章系统 | 接收签约请求，发起签约流程 | TBD |
| GET | /v1/agreement/{agreementId}/status | 电子签章系统 | 查询指定协议的签署状态 | TBD |
| POST | /v1/agreement/{agreementId}/resend-sms | 电子签章系统 | 重新发送签约短信 | TBD |
| POST | /v1/h5/sign/verify | 电子签章系统 | H5页面调用的身份验证接口 | TBD |
| POST | /v1/h5/sign/confirm | 电子签章系统 | H5页面调用的最终签署确认接口 | TBD |
| POST | /api/v1/fee/calculate | 计费中台 | 接收计费请求，计算手续费并返回结果 | TBD |
| POST | /api/v1/statements/generate | 对账单系统 | 触发按需生成对账单 | TBD |
| GET | /api/v1/statements | 对账单系统 | 查询对账单列表 | TBD |
| GET | /api/v1/statements/{statementId}/download | 对账单系统 | 下载对账单文件 | TBD |
| POST | /api/v1/tiancai/split | 业务核心 | 处理天财分账请求 | TBD |
| POST | /api/v1/tiancai/member-settlement | 业务核心 | 处理会员结算请求 | TBD |
| POST | /api/v1/tiancai/batch-payment | 业务核心 | 处理批量付款请求 | TBD |
| POST | /api/internal/risk/freeze | 业务核心 | 接收风控系统发起的账户冻结指令 | TBD |
| POST | /api/v1/transaction/split | 交易系统 | 发起分账/转账 | TBD |
| POST | /api/v1/transaction/collection | 交易系统 | 发起资金归集 | TBD |
| POST | /api/v1/transaction/member-settlement | 交易系统 | 发起会员结算 | TBD |
| POST | /api/v1/transaction/batch-payment | 交易系统 | 发起批量付款 | TBD |
| GET | /api/v1/transaction/{transactionId} | 交易系统 | 查询交易状态 | TBD |
| POST | /users | 用户中心 | 创建或更新用户信息 | TBD |
| GET | /users/{userId} | 用户中心 | 查询用户基础信息 | TBD |
| POST | /users/{userId}/bindings/institutions | 用户中心 | 绑定用户与机构关系 | TBD |
| POST | /users/{userId}/bindings/merchants | 用户中心 | 绑定用户与商户关系 | TBD |
| POST | /users/{userId}/bindings/accounts | 用户中心 | 绑定用户与账户关系 | TBD |
| PUT | /users/{userId}/roles | 用户中心 | 分配或更新用户角色 | TBD |
| GET | /users/{userId}/authentication-records | 用户中心 | 查询用户认证记录 | TBD |
| POST | /users/{userId}/authentication-records | 用户中心 | 发起用户认证流程 | TBD |
| POST | /api/v1/disburse/orders | 代付通道 | 创建代付订单 | TBD |
| GET | /api/v1/disburse/orders/{order_id} | 代付通道 | 查询代付订单状态 | TBD |
| POST | /api/v1/disburse/callback/{channel_code} | 代付通道 | 接收外部通道的异步回调 | TBD |