## 4.1 对外接口
本系统对外部合作方（天财）暴露的API接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| TBD | TBD | 三代 | 商户入网审核接口 | TBD |
| TBD | TBD | 三代 | 计费配置管理接口 | TBD |
| TBD | TBD | 三代 | 业务状态查询接口 | TBD |
| POST | /v1/contract/initiate | 电子签约平台 | 三代系统调用，用于发起签约流程 | TBD |
| GET | /v1/contract/{contractId}/status | 电子签约平台 | 三代系统调用，用于查询签约状态 | TBD |
| POST | /api/v1/batch-payments | 代付系统 | 接收批量付款指令 | TBD |
| POST | /api/v1/account/open | 钱包APP/商服平台 | 发起开户申请 | TBD |
| POST | /api/v1/binding/initiate | 钱包APP/商服平台 | 初始化关系绑定流程 | TBD |
| POST | /api/v1/binding/submit-auth | 钱包APP/商服平台 | 提交认证信息 | TBD |
| POST | /api/v1/binding/confirm | 钱包APP/商服平台 | 确认并完成绑定 | TBD |
| POST | /api/v1/split/instruction | 钱包APP/商服平台 | 发起分账指令 | TBD |
| POST | /api/v1/payment/enable | 钱包APP/商服平台 | 开通付款能力 | TBD |
| GET | /api/v1/transactions | 钱包APP/商服平台 | 查询交易记录 | TBD |
| GET | /api/v1/account/info | 钱包APP/商服平台 | 查询账户信息 | TBD |

## 4.2 模块间接口
系统内部各模块之间的调用接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /v1/accounts | 账户系统 | 创建账户。接收行业钱包的指令，创建天财专用账户。 | TBD |
| POST | /v1/accounts/{accountId}/upgrade | 账户系统 | 账户升级。将普通账户升级为天财专用账户。 | TBD |
| POST | /v1/transfers | 账户系统 | 执行转账。处理账户间的资金划转。 | TBD |
| GET | /v1/accounts/{accountId}/balance | 账户系统 | 查询账户余额。 | TBD |
| POST | /v1/accounts/{accountId}/freeze | 账户系统 | 冻结账户。 | TBD |
| POST | /v1/accounts/{accountId}/unfreeze | 账户系统 | 解冻账户。 | TBD |
| POST | /v1/contract/{contractId}/callback | 电子签约平台 | 认证系统回调，通知认证结果。 | TBD |
| POST | /v1/internal/evidence/query | 电子签约平台 | 内部接口，供其他模块查询证据链。 | TBD |
| POST | /api/v1/auth/payment | 认证系统 | 发起打款验证 | TBD |
| POST | /api/v1/auth/face | 认证系统 | 发起人脸验证 | TBD |
| POST | /api/v1/auth/verify-payment | 认证系统 | 验证用户回填的打款金额 | TBD |
| GET | /api/v1/auth/status/{requestId} | 认证系统 | 查询认证请求状态 | TBD |
| POST | /api/v1/fee/calculate | 计费中台 | 计费计算与流水生成接口 | TBD |
| POST | /api/v1/statements/generate | 对账单系统 | 触发生成对账单任务。 | TBD |
| GET | /api/v1/statements/{jobId} | 对账单系统 | 查询对账单生成任务状态。 | TBD |
| GET | /api/v1/statements/{jobId}/download | 对账单系统 | 下载生成的对账单文件。 | TBD |
| GET | /api/v1/tiancai-split-transactions | 业务核心 | 为下游对账单系统提供处理后的天财分账交易数据，支持按机构号、时间范围分页查询。 | TBD |
| POST | /api/v1/accounts | 账务核心 | 创建账户 | TBD |
| POST | /api/v1/transfers | 账务核心 | 执行转账 | TBD |
| GET | /api/v1/accounts/{accountId} | 账务核心 | 查询账户信息 | TBD |
| POST | /api/v1/accounts/{accountId}/freeze | 账务核心 | 冻结账户 | TBD |
| POST | /api/v1/accounts/{accountId}/unfreeze | 账务核心 | 解冻账户 | TBD |