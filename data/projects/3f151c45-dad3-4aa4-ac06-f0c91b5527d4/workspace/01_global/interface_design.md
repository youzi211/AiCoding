## 4.1 对外接口
系统对外暴露的API接口，主要供上游业务系统（如三代系统）和外部商户（通过钱包APP/商服平台）调用。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/tiancai/account/open | 三代系统 | 向行业钱包系统发起天财专用账户开户请求 | TBD |
| POST | /api/v1/tiancai/relation/bind | 三代系统 | 向行业钱包系统发起分账关系绑定请求 | TBD |
| POST | /api/v1/tiancai/split/trigger | 三代系统 | 触发分账处理（归集/批量付款/会员结算） | TBD |
| POST | /api/v1/tiancai/payment/open | 三代系统 | 向行业钱包系统发起开通付款请求 | TBD |
| GET | /api/v1/tiancai/relation/status | 三代系统 | 查询分账关系绑定状态 | TBD |
| GET | /api/v1/tiancai/split/status | 三代系统 | 查询分账指令状态 | TBD |
| POST | /api/v1/tiancai/config/sync | 三代系统 | 同步门店分账配置至行业钱包系统 | TBD |
| POST | /api/v1/auth/payment | 认证系统 | 发起打款验证请求 | TBD |
| POST | /api/v1/auth/payment/verify | 认证系统 | 验证用户回填的打款信息 | TBD |
| POST | /api/v1/auth/face | 认证系统 | 发起人脸验证请求 | TBD |
| GET | /api/v1/auth/record/{auth_id} | 认证系统 | 查询认证记录 | TBD |
| GET | /api/v1/statements/account-journal | 对账单系统 | 查询账户动账明细账单 | TBD |
| GET | /api/v1/statements/transaction | 对账单系统 | 查询交易账单（结算/退货） | TBD |
| GET | /api/v1/statements/split-order | 对账单系统 | 查询分账指令账单 | TBD |
| POST | /api/v1/statements/export | 对账单系统 | 异步生成并导出对账单文件 | TBD |

## 4.2 模块间接口
系统内部各模块之间相互调用的接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/account/open | 行业钱包系统 | 接收三代系统指令，开立天财专用账户。 | TBD |
| POST | /api/v1/relation/bind | 行业钱包系统 | 接收三代系统指令，发起分账关系绑定流程。 | TBD |
| POST | /api/v1/split/initiate | 行业钱包系统 | 发起分账处理（归集/批量付款/会员结算）。 | TBD |
| POST | /api/v1/payment/open | 行业钱包系统 | 发起开通付款流程。 | TBD |
| GET | /api/v1/relation/{relationId} | 行业钱包系统 | 查询分账关系绑定状态。 | TBD |
| GET | /api/v1/split/{orderId} | 行业钱包系统 | 查询分账指令状态。 | TBD |
| POST | /api/v1/callback/agreement-sign | 行业钱包系统 | 接收电子签章系统回调，处理协议签署结果。 | TBD |
| POST | /api/v1/billing/calculate | 计费中台 | 计算转账手续费 | TBD |
| POST | /api/v1/agreement/generate | 电子签章系统 | 生成待签署协议 | TBD |
| GET | /api/v1/agreement/{agreement_id} | 电子签章系统 | 查询协议详情 | TBD |
| POST | /api/v1/agreement/{agreement_id}/send-sms | 电子签章系统 | 发送签署通知短信 | TBD |
| GET | /api/v1/agreement/h5-page | 电子签章系统 | H5页面获取协议及认证信息接口 | TBD |
| POST | /api/v1/agreement/{agreement_id}/init-auth | 电子签章系统 | 发起身份认证 | TBD |
| POST | /api/v1/agreement/{agreement_id}/verify-auth | 电子签章系统 | 验证认证结果 | TBD |
| POST | /api/v1/agreement/{agreement_id}/sign | 电子签章系统 | 提交协议签署 | TBD |
| POST | /api/v1/agreement/notify/sign-result | 电子签章系统 | 接收业务系统签署结果通知（回调接口） | TBD |
| POST | /api/v1/settlement | 清结算 | 触发并处理交易结算 | TBD |
| POST | /api/v1/refund | 清结算 | 处理退货扣款请求 | TBD |
| GET | /api/v1/transactions | 清结算 | 为对账单系统提供交易明细查询 | TBD |