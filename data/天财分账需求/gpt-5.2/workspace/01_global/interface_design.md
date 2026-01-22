## 4.1 对外接口
系统对外部调用方（如天财平台、ISV等）暴露的接口。

| Method | Path | Module | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/third-generation/merchants/audit | 三代 | 接收并处理商户开户申请 | TBD |
| PUT | /api/v1/third-generation/merchants/{institution_no}/settlement-config | 三代 | 接收并处理商户结算模式配置申请 | TBD |
| GET | /api/v1/third-generation/merchants/{institution_no} | 三代 | 查询商户审核状态与基本信息 | TBD |
| POST | /api/v1/verification/payment | 认证系统 | 发起打款验证请求 | TBD |
| POST | /api/v1/verification/payment/confirm | 认证系统 | 提交并验证回填金额 | TBD |
| POST | /api/v1/verification/face | 认证系统 | 发起人脸验证请求 | TBD |
| GET | /api/v1/verification/{request_id} | 认证系统 | 查询认证结果 | TBD |
| POST | /api/v1/sign/initiate | 电子签约平台 | 发起签约流程 | TBD |
| GET | /api/v1/sign/status/{signing_id} | 电子签约平台 | 查询签约状态 | TBD |
| GET | /api/v1/sign/contract/{signing_id} | 电子签约平台 | 获取已签署协议内容 | TBD |
| GET | /api/v1/statements | 对账单系统 | 查询对账单列表 | TBD |
| GET | /api/v1/statements/{statement_id}/download | 对账单系统 | 获取对账单文件下载链接 | TBD |
| POST | /api/v1/statements/regenerate | 对账单系统 | 手动触发对账单重新生成（补单） | TBD |

## 4.2 模块间接口
系统内部各模块之间相互调用的接口。

| Method | Path | Module (调用方) | Description | Request/Response |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/v1/wallet/users | 行业钱包 | 创建钱包用户（开户） | TBD |
| POST | /api/v1/wallet/relations | 行业钱包 | 发起关系绑定 | TBD |
| GET | /api/v1/wallet/relations/{relation_id} | 行业钱包 | 查询关系绑定状态 | TBD |
| POST | /api/v1/wallet/validations/split | 行业钱包 | 校验分账请求 | TBD |
| PUT | /api/v1/wallet/settlement-configs | 行业钱包 | 更新结算配置 | TBD |
| POST | /api/v1/accounts | 账户系统 | 用于开户 | TBD |
| POST | /api/v1/accounts/{accountNo}/balance/operate | 账户系统 | 用于资金操作 | TBD |
| POST | /api/v1/accounts/{accountNo}/freeze | 账户系统 | 用于冻结/解冻 | TBD |
| POST | /api/v1/accounting/entries | 账务核心 | 用于接收记账指令 | TBD |
| POST | /api/v1/fee/calculate | 计费中台 | 核心计费接口，接收计费请求，返回计费结果 | TBD |
| GET | /api/v1/fee/rules/{ruleId} | 计费中台 | 查询特定费率规则详情 | TBD |
| POST | /api/v1/settlement/process | 清结算 | 用于触发结算处理 | TBD |
| POST | /api/v1/settlement/freeze/apply | 清结算 | 用于处理冻结申请 | TBD |
| POST | /api/v1/risk/transaction/check | 风控 | 用于交易风险判定 | TBD |
| POST | /api/v1/risk/merchant/freeze/apply | 风控 | 用于商户冻结申请 | TBD |
| GET | /api/v1/risk/rules | 风控 | 查询生效的风险规则列表 | TBD |
| POST | /api/v1/risk/rules/reload | 风控 | 触发风险规则热重载 | TBD |