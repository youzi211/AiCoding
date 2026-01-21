## 4.1 对外接口
系统对外部（如商户、合作伙伴）暴露的API接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/v1/accounts` | 账户系统 | 创建天财专用账户 | TBD |
| GET | `/v1/accounts/{accountId}` | 账户系统 | 查询账户详情 | TBD |
| PATCH | `/v1/accounts/{accountId}/status` | 账户系统 | 更新账户状态 | TBD |
| POST | `/api/v1/payment-verification/initiate` | 认证系统 | 发起打款验证 | TBD |
| POST | `/api/v1/payment-verification/confirm` | 认证系统 | 确认（回填）打款验证 | TBD |
| POST | `/api/v1/face-verification` | 认证系统 | 发起人脸验证 | TBD |
| GET | `/api/v1/verifications/{id}` | 认证系统 | 查询验证请求状态 | TBD |
| POST | `/api/v1/settlement/config` | 清结算系统 | 创建或更新结算配置 | TBD |
| GET | `/api/v1/account/refund/{accountId}` | 清结算系统 | 查询用于退货/退款的天财专用账户信息 | TBD |
| POST | `/api/v1/account/freeze` | 清结算系统 | 对天财专用账户执行冻结或解冻操作 | TBD |
| POST | `/api/v1/billing/sync` | 清结算系统 | 同步单笔交易的计费信息 | TBD |
| POST | `/api/v1/fee/calculate` | 计费中台 | 计算手续费 | TBD |
| POST | `/api/v1/tiancai/split-record` | 业务核心系统 | 接收行业钱包系统推送的分账交易记录 | TBD |
| POST | `/v1/merchants/tiancai-config` | 三代系统 | 为商户配置天财业务并请求开户 | TBD |
| GET | `/v1/merchants/{merchantId}/tiancai-config` | 三代系统 | 查询商户的天财业务配置信息 | TBD |
| PATCH | `/v1/merchants/{merchantId}/settlement-config` | 三代系统 | 更新商户的结算账户与手续费配置 | TBD |
| POST | `/api/v1/sign/initiate` | 电子签约平台 | 上游系统（行业钱包系统/三代系统）发起签约流程 | TBD |
| GET | `/api/v1/sign/status/{signRequestId}` | 电子签约平台 | 查询签约流程状态 | TBD |
| POST | `/v1/relationship/bind` | 行业钱包系统 | 发起关系绑定（签约与认证） | TBD |
| GET | `/v1/relationship/{relationshipId}` | 行业钱包系统 | 查询关系绑定状态 | TBD |
| POST | `/v1/ledger/split` | 行业钱包系统 | 发起分账（归集、会员结算、批量付款） | TBD |
| GET | `/v1/ledger/records/{recordId}` | 行业钱包系统 | 查询分账记录详情 | TBD |
| GET | `/api/v1/statements` | 对账单系统 | 查询对账单列表 | TBD |
| GET | `/api/v1/statements/{statementId}/download` | 对账单系统 | 下载指定对账单文件 | TBD |
| POST | `/api/v1/statements/generate` | 对账单系统 | 触发对账单生成（如按日/月批量生成） | TBD |

## 4.2 模块间接口
系统内部各模块之间的调用接口。

| Method | Path | Module (Caller) | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| TBD | TBD | 三代系统 | 调用账户系统接口为商户开立天财专用账户 | TBD |
| TBD | TBD | 行业钱包系统 | 调用电子签约平台发起签约流程 | TBD |
| TBD | TBD | 电子签约平台 | 调用认证系统发起打款验证 | TBD |
| TBD | TBD | 电子签约平台 | 调用认证系统发起人脸验证 | TBD |
| POST | `/api/v1/sign/callback/payment` | 认证系统 | 向电子签约平台回调打款验证结果 | TBD |
| POST | `/api/v1/sign/callback/face` | 认证系统 | 向电子签约平台回调人脸验证结果 | TBD |
| TBD | TBD | 行业钱包系统 | 调用计费中台计算手续费 | TBD |
| TBD | TBD | 清结算系统 | 调用计费中台获取计费信息 | TBD |
| TBD | TBD | 业务核心系统 | 调用计费中台计算手续费 | TBD |
| TBD | TBD | 业务核心系统 | 调用清结算系统触发结算流程 | TBD |
| TBD | TBD | 行业钱包系统 | 调用清结算系统同步计费信息 | TBD |
| TBD | TBD | 行业钱包系统 | 向业务核心系统推送分账交易记录 | TBD |
| TBD | TBD | 对账单系统 | 从业务核心系统消费交易数据 | TBD |
| TBD | TBD | 对账单系统 | 从清结算系统消费结算数据 | TBD |
| TBD | TBD | 对账单系统 | 从账户系统消费账户数据 | TBD |
| TBD | TBD | 对账单系统 | 从行业钱包系统消费分账数据 | TBD |
| TBD | TBD | 对账单系统 | 从三代系统消费商户配置数据 | TBD |