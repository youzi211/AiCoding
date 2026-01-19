# 4. 接口设计

## 4.1 对外接口
本节列出系统对外部业务方（如天财商龙、商户、运营人员等）暴露的API接口。

### 4.1.1 商户与账户管理
此类接口主要用于商户注册、账户开通与管理，主要由三代系统、钱包APP/商服平台对外提供。

| 接口路径与方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/api/v1/merchants` | 三代系统 | 创建/注册商户，作为业务关系的权威数据源。 |
| **POST** `/api/v1/merchants/{merchantId}/accounts/apply` | 三代系统 | 为指定商户申请开通天财专用账户。 |
| **POST** `/api/v1/accounts/open` | 钱包APP/商服平台 | 开通天财专用账户（面向商户的便捷入口）。 |
| **POST** `/api/v1/accounts/{accountNo}/bank-cards` | 钱包APP/商服平台 | 为天财账户绑定提现银行卡。 |
| **GET** `/api/v1/merchant/accounts` | 钱包APP/商服平台 | 查询商户名下的账户概览信息。 |

### 4.1.2 业务关系与认证
此类接口用于建立和管理商户间的业务关系及身份认证流程，主要由认证系统、钱包APP/商服平台对外提供。

| 接口路径与方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/api/v1/auth/bindings` | 认证系统 | 发起商户间的资金流转关系绑定流程，创建认证实例。 |
| **GET** `/api/v1/auth/bindings/{bindingId}` | 认证系统 | 查询指定绑定关系的详细信息与当前状态。 |
| **POST** `/api/v1/merchant/business-relationships/initiate` | 钱包APP/商服平台 | 发起业务关系绑定流程（面向商户的便捷入口）。 |
| **GET** `/api/v1/sign/agreements/preview` | 电子签章系统 | H5页面调用，获取待签署的协议预览内容。 |
| **POST** `/api/v1/sign/callbacks/{signTaskId}` | 电子签章系统 | 接收来自H5页面或CA机构的签署结果异步回调。 |

### 4.1.3 资金流转与交易
此类接口是“天财分账”业务的核心，用于发起和处理各类资金流转指令。

| 接口路径与方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/tiancai/api/v1/split` | 三代系统 | **核心接口**。供天财商龙调用，发起分账等资金流转请求。 |
| **POST** `/api/v1/transfers/tiancai-split` | 钱包APP/商服平台 | **核心内部接口**。执行天财分账，通常由三代系统调用。 |
| **POST** `/api/v1/transactions/batch-payment` | 业务核心 | 发起批量付款任务（异步处理）。 |
| **GET** `/api/v1/transactions/{transactionNo}` | 业务核心 | 查询单笔交易的详情。 |
| **GET** `/api/v1/transactions/batches/{batchNo}` | 业务核心 | 查询批量付款任务的详情。 |
| **POST** `/api/v1/transactions/{transactionNo}/reverse` | 业务核心 | 对指定交易进行冲正。 |

### 4.1.4 结算与对账
此类接口用于资金结算、查询及账单服务，主要面向商户和运营人员。

| 接口路径与方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/api/v1/settlements/instructions` | 清结算系统 | 创建结算指令，触发单笔或批量资金的结算划拨。 |
| **GET** `/api/v1/settlements/merchants/{merchantId}` | 清结算系统 | 查询指定商户的结算记录。 |
| **GET** `/api/v1/statements/accounts/{accountNo}/transactions` | 对账单系统 | 查询指定账户在特定时间范围内的所有资金变动明细。 |
| **GET** `/api/v1/statements/merchants/{merchantId}/summary` | 对账单系统 | 查询指定商户在特定结算周期内的资金结算汇总情况。 |
| **POST** `/api/v1/statements/export` | 对账单系统 | 根据复杂查询条件导出账单数据为文件（如Excel）。 |

### 4.1.5 计费服务
此类接口用于手续费的计算与查询。

| 接口路径与方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/api/v1/fee/calculate` | 计费中台 | 核心计费接口，根据交易信息计算手续费及承担方。 |
| **GET** `/api/v1/fee/result/{feeRequestId}` | 计费中台 | 根据计费请求ID查询详细的计费结果。 |

## 4.2 模块间接口
本节列出系统内部各微服务模块之间的主要调用接口，这些接口通常不直接对外暴露。

### 4.2.1 账户与资金操作
账户系统作为底层服务，为多个上层模块提供原子化的账户与资金操作。

| 接口路径与方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/api/v1/accounts` | 行业钱包系统 -> 账户系统 | 为指定商户开立新的天财专用账户。 |
| **POST** `/api/v1/accounts/{accountNo}/upgrade-to-tiancai` | 三代系统 -> 账户系统 | 将已有账户升级标记为天财专用账户。 |
| **POST** `/api/v1/accounts/{accountNo}/status` | 行业钱包系统/三代系统 -> 账户系统 | 冻结、解冻或注销账户。 |
| **POST** `/api/v1/accounts/transactions` | 行业钱包系统/业务核心 -> 账户系统 | **核心内部接口**。执行原子化的资金操作（入账、出账、冻结、解冻）。 |
| **GET** `/api/v1/accounts/{accountNo}` | 多个模块 -> 账户系统 | 查询账户核心信息。 |

### 4.2.2 业务控制与校验
三代系统作为业务控制中心，提供商户、关系和业务请求的校验服务。

| 接口路径与方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/api/v1/business-relationships/validate` | 业务核心/行业钱包系统 -> 三代系统 | **核心内部接口**。在发起交易前，校验业务关系的有效性、状态及权限。 |
| **POST** `/api/v1/business-relationships` | 认证系统 -> 三代系统 | 创建业务关系授权记录。 |

### 4.2.3 认证与签约流程
认证系统与电子签章系统协同，完成身份认证与协议签署流程。

| 接口路径与方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/api/v1/sign/tasks` | 认证系统 -> 电子签章系统 | 创建电子协议签署任务。 |
| **GET** `/api/v1/sign/tasks/{signTaskId}` | 认证系统 -> 电子签章系统 | 查询签署任务状态。 |
| **POST** `/api/v1/auth/callbacks/{authFlowId}` | 电子签约/支付系统 -> 认证系统 | 接收来自外部系统的异步回调，更新认证流程状态。 |
| **POST** `/api/v1/auth/bindings/{bindingId}/enable-payment` | 业务核心 -> 认证系统 | 在关系绑定完成后，为批量付款等场景触发“开通付款”流程。 |

### 4.2.4 资金流转执行
行业钱包系统作为桥梁，协调执行具体的资金划转操作。

| 接口路径与方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/api/v1/wallet/accounts/open` | 三代系统/钱包APP -> 行业钱包系统 | 协调开通天财专用账户的完整流程。 |
| **POST** `/api/v1/wallet/relationships/initiate-auth` | 三代系统 -> 行业钱包系统 | 发起关系绑定的身份认证流程。 |
| **POST** `/api/v1/wallet/transfers/execute` | 业务核心 -> 行业钱包系统 | **核心接口**。执行具体的资金划转操作，内部会调用账户系统完成记账。 |
| **GET** `/api/v1/wallet/accounts/{accountNo}/relationships` | 业务核心 -> 行业钱包系统 | 查询账户的关联业务关系。 |

### 4.2.5 计费与结算联动
计费中台和清结算系统在交易和结算过程中被调用，以计算费用并完成资金划拨。

| 接口路径与方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- |
| **POST** `/api/v1/fee/calculate` | 业务核心/清结算系统 -> 计费中台 | 在交易或结算时，计算应收手续费。 |
| **POST** `/api/v1/settlements/instructions` | 业务核心 -> 清结算系统 | 交易完成后，创建结算指令以触发资金的实际划拨。 |
| **POST** `/api/v1/settlements/{instructionNo}/retry` | (内部调度/运营) -> 清结算系统 | 对失败的结算指令进行重试。 |

### 4.2.6 数据依赖与查询
各模块为对账单系统等提供数据查询接口，或依赖其他模块获取基础数据。

| 接口路径与方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- |
| **GET** `/api/v1/statements/accounts/{accountNo}/transactions` | 对账单系统 -> 账户系统 | 拉取账户流水明细，用于生成账单。 |
| **GET** `/api/v1/statements/merchants/{merchantId}/summary` | 对账单系统 -> 清结算系统 | 拉取商户结算汇总数据。 |
| **POST** `/api/v1/auth/verifications/remit` | 认证系统 -> 支付系统/清结算系统 | 请求向对公账户发起小额打款验证。 |
| **GET** `/api/v1/sign/agreements/{agreementId}` | 业务核心/认证系统 -> 电子签章系统 | 下载或验证已签署的协议文件。 |

**请求/响应格式说明**：
以上接口的请求与响应格式通常采用JSON，遵循公司统一的API规范。请求头需包含用于链路追踪的`Trace-Id`、认证令牌`Authorization`等。响应体包含标准字段如`code`、`message`、`data`。具体接口的详细字段定义需参考各模块的API设计文档。内部接口为提高性能，可能采用RPC调用，但其逻辑映射与上述HTTP接口一致。