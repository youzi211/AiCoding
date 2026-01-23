## 4.1 对外接口
系统对外部（如天财平台、商户前端应用）暴露的接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | TBD | 三代 | 接收天财发起的业务指令（如开户、分账、关系绑定等） | TBD |
| GET | TBD | 三代 | 查询业务指令执行状态 | TBD |
| POST | `/api/v3/account/open` | 钱包APP/商服平台 | 发起开户申请 | TBD |
| POST | `/api/v3/relation/bind` | 钱包APP/商服平台 | 发起关系绑定请求 | TBD |
| POST | `/api/v3/split/apply` | 钱包APP/商服平台 | 发起分账/归集/批量付款请求 | TBD |
| POST | `/api/v3/withdraw/apply` | 钱包APP/商服平台 | 发起提现申请 | TBD |
| GET | `/api/v3/account/balance` | 钱包APP/商服平台 | 查询账户余额 | TBD |
| GET | `/api/v3/transactions` | 钱包APP/商服平台 | 查询交易流水 | TBD |
| GET | `/api/v3/operation/status` | 钱包APP/商服平台 | 查询异步操作状态 | TBD |
| GET | `/esign/h5/url` | 钱包APP/商服平台 | 获取协议签署H5页面地址 | TBD |
| GET | `/auth/h5/url` | 钱包APP/商服平台 | 获取打款验证或人脸验证H5页面地址 | TBD |
| GET | `/statement/download/url` | 钱包APP/商服平台 | 获取对账单文件下载链接 | TBD |
| GET | `/user/profile` | 钱包APP/商服平台 | 获取当前用户身份信息 | TBD |

## 4.2 模块间接口
系统内部各模块之间的调用接口。

| Method | Path | Module (调用方) | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/settlement/transfer` | 清结算 | 处理分账/转账请求 | TBD |
| POST | `/api/v1/settlement/batch-payment` | 清结算 | 处理批量付款请求 | TBD |
| POST | `/api/v1/settlement/member-settlement` | 清结算 | 处理会员结算请求 | TBD |
| POST | `/api/v1/settlement/refund` | 清结算 | 处理退货资金扣减请求 | TBD |
| POST | `/api/v1/settlement/freeze` | 清结算 | 处理风控发起的账户/交易冻结请求 | TBD |
| GET | `/api/v1/settlement/orders/{orderId}` | 清结算 | 查询清结算订单状态 | TBD |
| POST | `/api/v1/accounts` | 账户系统 | 创建账户 | TBD |
| GET | `/api/v1/accounts/{accountId}` | 账户系统 | 查询账户信息 | TBD |
| POST | `/api/v1/accounts/{accountId}/debit` | 账户系统 | 执行资金扣减 | TBD |
| POST | `/api/v1/accounts/{accountId}/credit` | 账户系统 | 执行资金增加 | TBD |
| POST | `/api/v1/accounts/{accountId}/freeze` | 账户系统 | 冻结账户 | TBD |
| POST | `/api/v1/accounts/{accountId}/unfreeze` | 账户系统 | 解冻账户 | TBD |
| POST | `/v1/agreements/initiate` | 电子签约平台 | 发起签约流程 | TBD |
| GET | `/v1/agreements/sessions/{sessionId}` | 电子签约平台 | 查询签约会话状态及详情 | TBD |
| POST | `/v1/agreements/sessions/{sessionId}/resend-sms` | 电子签约平台 | 重新发送签约短信 | TBD |
| POST | `/v1/agreements/callback/authentication` | 电子签约平台 | 认证系统完成验证后的回调接口 | TBD |
| GET | `/v1/agreements/{agreementId}` | 电子签约平台 | 查询已签署的协议及证据链信息 | TBD |
| POST | `/api/v1/verification/payment` | 认证系统 | 发起打款验证请求 | TBD |
| POST | `/api/v1/verification/face` | 认证系统 | 发起人脸验证请求 | TBD |
| POST | `/api/v1/verification/{verification_id}/confirm` | 认证系统 | 确认打款验证（回填金额） | TBD |
| GET | `/api/v1/verification/{verification_id}` | 认证系统 | 查询验证状态与结果 | TBD |
| POST | `/api/v1/fee/calculate` | 计费中台 | 计算手续费接口 | TBD |
| GET | `/api/v1/fee/record/{recordId}` | 计费中台 | 查询计费流水详情接口 | TBD |
| POST | `/api/v1/statements/generate` | 对账单系统 | 触发账单生成任务 | TBD |
| GET | `/api/v1/statements` | 对账单系统 | 查询账单列表 | TBD |
| GET | `/api/v1/statements/{statementId}/download` | 对账单系统 | 获取指定账单的下载链接 | TBD |
| GET | `/api/v1/statements/reconciliation/{date}` | 对账单系统 | 触发指定日期的对账核对，并返回核对结果摘要 | TBD |
| POST | `/api/v1/risk/assessment/manual` | 风控 | 手动触发对指定商户或交易的风险评估 | TBD |
| GET | `/api/v1/risk/rules` | 风控 | 查询当前生效的风险规则列表 | TBD |
| POST | `/api/v1/risk/rules` | 风控 | 创建新的风险规则（需授权） | TBD |
| PUT | `/api/v1/risk/rules/{ruleId}` | 风控 | 更新指定风险规则（需授权） | TBD |
| POST | `/api/v1/freeze/manual` | 风控 | 人工发起冻结指令（覆盖自动风控） | TBD |
| POST | `/api/v1/unfreeze/request` | 风控 | 发起解冻申请（需审核） | TBD |
| POST | `/v1/users` | 用户中心 | 创建用户标识 | TBD |
| GET | `/v1/users/{userid}` | 用户中心 | 根据用户标识查询用户信息 | TBD |
| GET | `/v1/users` | 用户中心 | 根据来源系统标识和外部业务唯一标识查询用户标识 | TBD |
| POST | `/api/v1/payout/execute` | 代付系统 | 接收提现出款指令 | TBD |
| POST | `/api/v1/payout/callback/{channel}` | 代付系统 | 接收代付通道的异步回调 | TBD |
| GET | `/api/v1/payout/records/{payout_id}` | 代付系统 | 查询出款记录状态 | TBD |