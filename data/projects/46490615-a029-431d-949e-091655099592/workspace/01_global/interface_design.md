# 4. 接口设计

## 4.1 对外接口
指系统向外部商户、合作伙伴或前端应用（如钱包App、商服平台）提供的服务接口。

### 4.1.1 商户与账户管理
| 接口路径 | 方法 | 所属模块 | 功能说明 | 请求/响应格式 |
| :--- | :--- | :--- | :--- | :--- |
| `/api/external/tiancai/v1/merchants` | POST | 三代系统 | 商户入驻，为天财商龙创建收单商户。 | 请求：商户基础信息<br>响应：商户号(`merchantNo`)等 |
| `/api/v1/tiancai/accounts` | POST | 天财分账模块 | 为商户或用户创建天财专用账户。 | 请求：开户主体信息<br>响应：账户号(`accountNo`)等 |
| `/api/v1/tiancai/accounts/{accountNo}` | GET | 天财分账模块 | 查询指定天财账户的详情。 | 响应：账户状态、余额、绑定信息等 |
| `/api/v1/accounts/{accountNo}` | GET | 账户系统 | 查询账户详情（内部数据结构）。 | 响应：账户核心信息、状态、能力等 |
| `/api/v1/accounts/{accountNo}/validation` | GET | 账户系统 | 校验指定账户的有效性（如状态是否正常）。 | 响应：是否有效、无效原因等 |

### 4.1.2 关系绑定与认证
| 接口路径 | 方法 | 所属模块 | 功能说明 | 请求/响应格式 |
| :--- | :--- | :--- | :--- | :--- |
| `/api/external/tiancai/v1/bindings` | POST | 三代系统 | 发起分账关系绑定申请，触发签约与认证流程。 | 请求：付款方、收款方信息<br>响应：绑定申请ID(`bindingId`) |
| `/api/v1/tiancai/relationships/bind` | POST | 天财分账模块 | 发起关系绑定流程（面向前端）。 | 请求：绑定关系信息<br>响应：绑定请求号(`bindRequestNo`) |
| `/api/v1/tiancai/relationships` | GET | 天财分账模块 | 查询当前用户的关系绑定列表。 | 响应：关系列表，包含状态、对方信息等 |
| `/api/v1/tiancai/relationship/query/{bindRequestNo}` | GET | 业务核心系统 | 查询关系绑定请求的详细状态。 | 响应：流程状态、认证结果、失败原因等 |
| `/api/v1/auth/requests` | POST | 认证系统 | 发起一个新的关系绑定或开通付款认证流程（内部编排用）。 | 请求：认证场景、参与方信息<br>响应：认证请求ID(`authRequestId`) |
| `/api/v1/auth/requests/{authRequestId}` | GET | 认证系统 | 查询指定认证请求的详细状态和结果。 | 响应：认证状态、签署链接、验证结果等 |
| `/api/v1/contract/tasks` | POST | 电子签章系统 | 创建电子协议签约任务。 | 请求：协议模板、签署方信息<br>响应：签约任务ID(`contractTaskId`) |
| `/api/v1/contract/tasks/{contractTaskId}/signers/{signerId}/url` | GET | 电子签章系统 | 获取指定签署方的H5签署链接。 | 响应：签署页URL |

### 4.1.3 资金流转
| 接口路径 | 方法 | 所属模块 | 功能说明 | 请求/响应格式 |
| :--- | :--- | :--- | :--- | :--- |
| `/api/external/tiancai/v1/transfers/split` | POST | 三代系统 | 发起分账/归集/付款指令，是业务入口。 | 请求：业务类型、金额、参与方<br>响应：分账订单号(`orderNo`) |
| `/api/v1/tiancai/fund/transfer` | POST | 业务核心系统 | 处理天财分账资金转账请求（归集、批量付款、会员结算）。 | 请求：转账业务参数<br>响应：受理成功，返回业务流水号 |
| `/api/v1/settlement/tiancai/split` | POST | 清结算系统 | 处理天财分账交易，执行资金清算与结算。 | 请求：清结算订单信息<br>响应：受理成功，返回结算订单号 |

### 4.1.4 能力开通与状态管理
| 接口路径 | 方法 | 所属模块 | 功能说明 | 请求/响应格式 |
| :--- | :--- | :--- | :--- | :--- |
| `/api/external/tiancai/v1/bindings/{bindingId}/open-payment` | POST | 三代系统 | 为已认证的绑定关系开通付款能力。 | 请求：绑定关系ID<br>响应：开通结果 |
| `/api/v1/tiancai/payment/enable` | POST | 业务核心系统 | 为付款方开通付款能力（内部流程触发）。 | 请求：付款方账户、关系ID<br>响应：开通结果 |
| `/api/v1/accounts/{accountNo}/status` | PATCH | 账户系统 | 更新账户状态（如冻结、解冻、注销）。 | 请求：目标状态<br>响应：更新结果 |

### 4.1.5 查询与对账服务
| 接口路径 | 方法 | 所属模块 | 功能说明 | 请求/响应格式 |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/settlement/accounts/{accountNo}/balance` | GET | 清结算系统 | 查询账户实时余额。 | 响应：可用余额、冻结余额等 |
| `/api/v1/statements/transactions` | GET | 对账单系统 | 查询账户动账明细列表。 | 请求：账户、时间范围、分页<br>响应：动账流水列表 |
| `/api/v1/statements/business` | GET | 对账单系统 | 查询业务对账单列表（按机构、周期）。 | 请求：商户、对账周期<br>响应：对账单概要列表 |
| `/api/v1/statements/transactions/export` | POST | 对账单系统 | 异步导出动账明细文件。 | 请求：导出条件<br>响应：导出任务ID |

### 4.1.6 退货处理
| 接口路径 | 方法 | 所属模块 | 功能说明 | 请求/响应格式 |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/refund-pre/query` | POST | 退货前置模块 | 退货前置查询，校验可退余额及有效期。 | 请求：原交易信息<br>响应：可退金额、有效期 |
| `/api/v1/refund-pre/deduct` | POST | 退货前置模块 | 退货前置扣减，执行资金预扣减。 | 请求：扣减请求信息<br>响应：扣减结果、预扣记录ID |

### 4.1.7 风险控制
| 接口路径 | 方法 | 所属模块 | 功能说明 | 请求/响应格式 |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/risk/decision` | POST | 风控系统 | 通用风险决策入口，供业务在关键节点同步调用。 | 请求：业务场景、实体信息、交易数据<br>响应：风险等级、处置建议、是否通过 |

### 4.1.8 回调接口
| 接口路径 | 方法 | 所属模块 | 功能说明 | 请求/响应格式 |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/tiancai/relationships/{bindId}/auth-callback` | POST | 天财分账模块 | 接收认证系统的最终结果回调，更新前端状态。 | 请求：绑定ID、认证结果 |
| `/api/v1/tiancai/relationship/bind/callback` | POST | 业务核心系统 | 接收电子签约或认证系统的异步回调，驱动业务流程。 | 请求：回调类型、请求号、结果状态 |
| `/api/h5/callback/sign` | POST | 电子签章系统 | 接收H5签署页面的签署完成回调。 | 请求：签约任务ID、签署方ID、签署结果 |
| `/api/callback/esign` | POST | 认证系统 | 接收电子签约平台推送的协议签署状态变更通知。 | 请求：协议ID、签署状态、时间戳 |
| `/api/callback/verification` | POST | 认证系统 | 接收打款验证金额核验结果。 | 请求：认证请求ID、核验金额、结果 |

## 4.2 模块间接口
指系统内部各微服务或模块之间相互调用的接口，通常通过内部API或消息队列(MQ)进行通信。

### 4.2.1 账户与资金服务
| 接口路径 | 方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `POST /api/v1/accounts/tiancai` | POST | 三代系统/天财分账模块 -> 账户系统 | 请求创建天财专用账户。 |
| `POST /api/v1/accounts/bindings/validation` | POST | 业务核心系统/风控系统 -> 账户系统 | 批量校验账户绑定关系的有效性。 |
| `GET /api/internal/v1/accounts/{accountNo}/detail` | GET | 行业钱包系统 -> 账户系统 | 查询账户的业务详情（含扩展信息）。 |
| `GET /api/internal/v1/accounts/{accountNo}/open-payment-status` | GET | 行业钱包系统 -> 账户系统 | 查询指定账户的开通付款状态。 |
| `POST /api/v1/settlement/accounts/batch-balance` | POST | 对账单系统/业务核心系统 -> 清结算系统 | 批量查询多个账户的实时余额。 |
| `POST /api/v1/settlement/refund/query` | POST | 退货前置模块 -> 清结算系统 | 查询指定交易的可退余额（退货前置查询）。 |
| `POST /api/v1/settlement/refund/deduct` | POST | 退货前置模块 -> 清结算系统 | 执行退货资金的预扣减（退货前置扣减）。 |

### 4.2.2 业务逻辑编排与执行
| 接口路径 | 方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `POST /api/internal/v1/bindings` | POST | 三代系统 -> 行业钱包系统 | 建立分账绑定关系（签约完成后回调触发）。 |
| `GET /api/internal/v1/bindings/validation` | GET | 清结算系统/业务核心系统 -> 行业钱包系统 | 在资金流转前校验绑定关系及付款能力。 |
| `POST /api/internal/v1/transfers/split` | POST | 三代系统 -> 行业钱包系统 | 处理分账/归集/付款指令，执行业务逻辑。 |
| `GET /api/internal/v1/merchants/{merchantNo}` | GET | 账户系统/计费中台 -> 三代系统 | 查询商户详情，作为商户信息的权威源。 |

### 4.2.3 计费与对账
| 接口路径 | 方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `POST /api/v1/fee/calculate` | POST | 清结算系统 -> 计费中台 | 在清算前计算单笔交易的手续费及分摊详情。 |
| `POST /api/v1/fee/settle` | POST | 清结算系统 -> 计费中台 | 触发实际的手续费扣收和记账操作（幂等）。 |
| `GET /api/v1/fee/settlement/daily` | GET | 对账单系统 -> 计费中台 | 获取指定日期的计费汇总与明细文件，用于对账。 |
| `GET /api/v1/fee/transactions/{transactionId}` | GET | 运营平台 -> 计费中台 | 查询指定交易的手续费计算和结算详情。 |

### 4.2.4 风险与监控
| 接口路径 | 方法 | 调用方 -> 提供方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `POST /api/v1/risk/decision/batch` | POST | 清结算系统（批量付款） -> 风控系统 | 对批量交易进行风险决策。 |
| `GET /api/v1/risk/lists/check` | GET | 认证系统/账户系统 -> 风控系统 | 检查商户、用户等实体是否命中风险名单。 |
| `GET /api/v1/risk/monitor/dashboard` | GET | 运营平台 -> 风控系统 | 获取风险监控大盘数据。 |

### 4.2.5 异步消息与事件
*说明：以下交互主要通过消息队列(MQ)实现，进行解耦的异步通知。*
| 消息主题/事件 | 发布方 -> 订阅方 | 功能说明 |
| :--- | :--- | :--- |
| **账户变动事件** | 账户系统 -> 对账单系统、行业钱包系统(`wallet_account_cache`) | 当账户余额、状态发生变更时，通知相关系统更新缓存或生成动账记录。 |
| **交易清算完成事件** | 清结算系统 -> 业务核心系统、对账单系统、计费中台 | 通知下游系统交易资金处理已完成，可更新业务状态、生成对账明细。 |
| **关系绑定状态变更事件** | 认证系统 -> 三代系统、业务核心系统、行业钱包系统 | 通知各系统绑定关系的认证结果，驱动后续流程（如开通付款）。 |
| **风险事件告警** | 风控系统 -> 运营平台、业务核心系统 | 当触发高风险规则时，发送告警消息，可能触发业务拦截。 |