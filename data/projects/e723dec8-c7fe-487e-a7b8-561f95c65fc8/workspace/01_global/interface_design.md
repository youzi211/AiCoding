## 4.1 对外接口
系统对外暴露的API接口，主要面向商户客户端（如钱包app/商服平台）或外部合作系统。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/accounts/tiancai` | 账户系统 | 开立天财专用账户 | TBD |
| PUT | `/api/v1/accounts/{accountId}/status` | 账户系统 | 更新账户状态（如冻结/解冻） | TBD |
| GET | `/api/v1/accounts/{accountId}` | 账户系统 | 查询账户详情 | TBD |
| POST | `/api/v1/auth/payment-verification` | 认证系统 | 发起打款验证 | TBD |
| POST | `/api/v1/auth/payment-verification/confirm` | 认证系统 | 确认打款验证 | TBD |
| POST | `/api/v1/auth/face-verification` | 认证系统 | 发起人脸验证 | TBD |
| POST | `/api/v1/merchants/{merchantId}/tiancai-accounts` | 三代系统 | 为指定商户开立天财专用账户 | TBD |
| POST | `/api/v1/merchants/{merchantId}/settlement-mode` | 三代系统 | 配置商户的结算模式（主动结算/被动结算） | TBD |
| POST | `/api/v1/relationship/bind` | 三代系统 | 建立分账关系绑定（签约与认证） | TBD |
| GET | `/api/v1/merchants/{merchantId}/relationship` | 三代系统 | 查询商户的绑定关系 | TBD |
| POST | `/api/v1/batch-payment` | 三代系统 | 发起批量付款指令 | TBD |
| POST | `/api/v1/member-settlement` | 三代系统 | 发起会员结算指令 | TBD |
| POST | `/api/v1/collection` | 三代系统 | 发起归集指令 | TBD |
| POST | `/api/v1/esign/contract/generate` | 电子签约平台 | 生成签约协议并初始化流程 | TBD |
| POST | `/api/v1/esign/contract/sign` | 电子签约平台 | 提交签约确认 | TBD |
| GET | `/api/v1/esign/contract/{contractId}` | 电子签约平台 | 查询协议状态与详情 | TBD |
| POST | `/api/v1/wallet/relationship/bind` | 行业钱包系统 | 接收并处理分账关系绑定请求 | TBD |
| POST | `/api/v1/wallet/transfer` | 行业钱包系统 | 接收并处理分账转账请求（归集、批量付款、会员结算） | TBD |
| GET | `/api/v1/wallet/accounts/{walletAccountNo}` | 行业钱包系统 | 查询天财专用账户详情及状态 | TBD |
| POST | `/api/v1/wallet/accounts/{walletAccountNo}/withdraw-cards` | 行业钱包系统 | 绑定或设置默认提现卡（用于天财接收方账户） | TBD |
| PUT | `/api/v1/wallet/accounts/{walletAccountNo}/status` | 行业钱包系统 | 更新账户业务状态（如暂停/恢复分账能力） | TBD |
| POST | `/api/v1/statement/generate` | 对账单系统 | 触发生成指定类型和周期的对账单 | TBD |
| GET | `/api/v1/statement/download/{statementId}` | 对账单系统 | 下载已生成的对账单文件 | TBD |
| GET | `/api/v1/statement/query` | 对账单系统 | 查询对账单生成记录及状态 | TBD |
| POST | `/api/v1/statement/reconcile` | 对账单系统 | 发起对账任务，比对内部交易记录与外部渠道数据 | TBD |
| GET | `/api/v1/statement/reconcile/task/{taskId}` | 对账单系统 | 查询对账任务结果 | TBD |

## 4.2 模块间接口
系统内部各模块之间相互调用的接口。

| Method | Path | Module (调用方) | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/accounts/{accountId}/tags` | 三代系统 | 为账户添加标记 | TBD |
| POST | `/api/settlement/account/freeze` | 行业钱包系统 | 对指定的天财专用账户执行资金冻结或解冻操作。 | TBD |
| GET | `/api/refund/account` | 行业钱包系统 | 根据交易信息查询对应的原收款账户（天财收款账户）。 | TBD |
| POST | `/api/settlement/config/sync` | 三代系统 | 接收并处理由三代系统同步的商户结算模式配置。 | TBD |
| POST | `/api/settlement/fee/sync` | 清结算系统 | 向计费中台同步涉及手续费的交易信息。 | TBD |
| POST | `/api/v1/esign/verification/initiate` | 三代系统 | 发起身份验证流程 | TBD |
| POST | `/api/v1/esign/verification/callback` | 认证系统 | 接收认证结果回调 | TBD |
| POST | `/api/v1/transaction/process` | 行业钱包系统 | 处理天财分账交易请求 | TBD |
| POST | `/api/v1/transaction/query` | 行业钱包系统 | 查询交易处理状态 | TBD |