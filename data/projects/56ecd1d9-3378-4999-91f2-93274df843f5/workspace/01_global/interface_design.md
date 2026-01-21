## 4.1 对外接口
本系统对外部（如商户、合作伙伴）暴露的API接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/accounts | 账户系统 | 创建天财专用账户 | TBD |
| PUT | /api/v1/accounts/{accountId}/status | 账户系统 | 变更账户状态（如冻结、解冻） | TBD |
| PUT | /api/v1/accounts/{accountId}/abilities | 账户系统 | 控制账户能力（如支付、收款开关） | TBD |
| GET | /api/v1/accounts/{accountId} | 账户系统 | 查询账户详情 | TBD |
| POST | /api/v1/fee/calculate | 计费中台 | 计算单笔转账手续费 | TBD |
| POST | /api/v1/settlement/config | 清结算系统 | 接收结算账户配置 | TBD |
| GET | /api/v1/settlement/account/query | 清结算系统 | 查询退货终点账户信息 | TBD |
| POST | /api/v1/account/freeze | 清结算系统 | 执行专用账户冻结操作 | TBD |
| POST | /api/v1/account/unfreeze | 清结算系统 | 执行专用账户解冻操作 | TBD |
| POST | /api/v1/verification/payment | 认证系统 | 发起打款验证 | TBD |
| POST | /api/v1/verification/face | 认证系统 | 发起人脸验证 | TBD |
| GET | /api/v1/verification/records/{requestId} | 认证系统 | 查询认证记录状态 | TBD |
| POST | /api/v1/account/guide | 钱包app/商服平台 | 获取账户开通引导信息 | TBD |
| POST | /api/v1/binding/initiate | 钱包app/商服平台 | 发起关系绑定请求 | TBD |
| GET | /api/v1/binding/status/{bindingId} | 钱包app/商服平台 | 查询关系绑定状态 | TBD |
| POST | /api/v1/instruction/collect | 钱包app/商服平台 | 发起归集指令 | TBD |
| POST | /api/v1/instruction/batch-payment | 钱包app/商服平台 | 发起批量付款指令 | TBD |
| POST | /api/v1/instruction/member-settlement | 钱包app/商服平台 | 发起会员结算指令 | TBD |
| GET | /api/v1/instruction/{instructionId}/result | 钱包app/商服平台 | 查询指令执行结果 | TBD |
| GET | /api/v1/bill/query | 钱包app/商服平台 | 查询账单 | TBD |
| POST | /api/v1/payment/activate | 钱包app/商服平台 | 发起开通付款流程 | TBD |
| POST | /api/v1/agreement/initiate | 电子签章系统 | 接收上游系统发起的签约请求，启动签约流程 | TBD |
| GET | /api/v1/agreement/{agreementId} | 电子签章系统 | 根据协议ID查询协议详情及签署状态 | TBD |
| POST | /api/v1/agreement/callback/sign | 电子签章系统 | 接收H5页面签署完成后的回调 | TBD |
| GET | /api/v1/template/agreement/{templateId} | 电子签章系统 | 查询协议模板详情 | TBD |
| POST | /api/v1/template/agreement | 电子签章系统 | 创建或更新协议模板 | TBD |
| POST | /api/v1/account/open | 行业钱包系统 | 接收三代系统的开户请求，进行校验并调用账户系统 | TBD |
| POST | /api/v1/relationship/bind | 行业钱包系统 | 发起关系绑定流程，调用电子签章系统 | TBD |
| POST | /api/v1/transfer | 行业钱包系统 | 处理分账请求（归集、批量付款、会员结算） | TBD |
| GET | /api/v1/account/{accountId}/status | 行业钱包系统 | 查询账户状态及绑定关系 | TBD |
| POST | /api/v1/tiancai/account/open | 三代系统 | 发起天财专用账户开户请求 | TBD |
| POST | /api/v1/tiancai/settlement/config | 三代系统 | 配置商户的结算账户模式 | TBD |
| POST | /api/v1/tiancai/relationship/bind | 三代系统 | 发起分账关系绑定（签约与认证） | TBD |
| GET | /api/v1/tiancai/merchant/{merchantId}/status | 三代系统 | 查询商户的天财分账业务开通状态 | TBD |
| POST | /api/v1/tiancai/callback/wallet | 三代系统 | 接收行业钱包系统的异步回调（用于开户、关系绑定状态更新） | TBD |
| POST | /api/v1/transfer/execute | 业务核心 | 接收行业钱包系统的分账（资金划转）请求 | TBD |
| GET | /api/v1/statement/tiancai/transfer | 对账单系统 | 查询天财分账账单 | TBD |
| GET | /api/v1/statement/withdrawal | 对账单系统 | 查询提款账单 | TBD |
| GET | /api/v1/statement/acquiring | 对账单系统 | 查询收单账单 | TBD |
| GET | /api/v1/statement/settlement | 对账单系统 | 查询结算账单 | TBD |
| POST | /api/v1/statement/generate | 对账单系统 | 触发账单生成任务 | TBD |

## 4.2 模块间接口
本系统内部各模块之间相互调用的接口。

| Method | Path | Module (调用方) | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| TBD | TBD | 行业钱包系统 -> 账户系统 | 调用账户系统创建或管理天财专用账户 | TBD |
| TBD | TBD | 行业钱包系统 -> 电子签章系统 | 发起关系绑定的签约与认证流程 | TBD |
| TBD | TBD | 行业钱包系统 -> 计费中台 | 计算分账交易的手续费 | TBD |
| TBD | TBD | 行业钱包系统 -> 清结算系统 | 查询退货账户或执行账户冻结 | TBD |
| TBD | TBD | 行业钱包系统 -> 业务核心 | 发起分账资金划转请求 | TBD |
| TBD | TBD | 三代系统 -> 行业钱包系统 | 发起开户、关系绑定等请求 | TBD |
| TBD | TBD | 三代系统 -> 清结算系统 | 配置结算账户 | TBD |
| TBD | TBD | 电子签章系统 -> 认证系统 | 发起打款验证或人脸验证 | TBD |
| TBD | TBD | 钱包app/商服平台 -> 行业钱包系统 | 发起业务请求（如指令、状态查询） | TBD |
| TBD | TBD | 钱包app/商服平台 -> 三代系统 | 查询商户状态或发起配置请求 | TBD |
| TBD | TBD | 钱包app/商服平台 -> 电子签章系统 | 获取协议签署链接或状态 | TBD |
| TBD | TBD | 钱包app/商服平台 -> 对账单系统 | 查询账单数据 | TBD |
| TBD | TBD | 业务核心 -> 支付系统 | 调用底层支付通道执行资金划转 | TBD |
| TBD | TBD | 业务核心 -> 清结算系统 | 调用清结算通道执行资金划转 | TBD |
| TBD | TBD | 对账单系统 -> 业务核心 | 监听或拉取分账交易事件 | TBD |
| TBD | TBD | 对账单系统 -> 清结算系统 | 监听或拉取结算相关事件 | TBD |
| TBD | TBD | 对账单系统 -> 行业钱包系统 | 监听或拉取账户及分账事件 | TBD |
| TBD | TBD | 对账单系统 -> 三代系统 | 监听或拉取商户配置事件 | TBD |