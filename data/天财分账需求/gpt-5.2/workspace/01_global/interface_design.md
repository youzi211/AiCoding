# 4. 接口设计

## 4.1 对外接口

本节描述系统向外部业务方（如商户、机构用户、前端应用）提供的服务接口。

### 4.1.1 商户业务开通与管理
| 接口路径 | 方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/tiancai/merchants/{merchant_no}/enable` | POST | 三代系统 | 为指定收单商户开通天财分账业务能力，触发天财专用账户创建流程。 |
| `/api/v1/tiancai/business/open` | POST | 业务核心 | 为指定商户开通天财分账业务（业务编排入口）。 |

### 4.1.2 账户管理
| 接口路径 | 方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/tiancai/accounts` | POST | 账户系统 | 创建天财专用账户。 |
| `/api/v1/tiancai/accounts` | GET | 账户系统 | 根据条件查询天财账户列表。 |
| `/api/v1/tiancai/accounts/{tiancai_account_id}` | GET | 账户系统 | 查询天财账户详情。 |
| `/api/v1/accounts` | GET | 钱包APP/商服平台模块 | 获取当前登录用户有权查看的天财专用账户列表。 |

### 4.1.3 关系绑定与认证
| 接口路径 | 方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/tiancai/accounts/{tiancai_account_id}/relationships` | POST | 账户系统 | 建立天财账户间的关系绑定。 |
| `/api/v1/relation-bindings/initiate` | POST | 钱包APP/商服平台模块 | 发起关系绑定流程，获取签约或认证链接。 |
| `/api/v1/tiancai/business/bindings` | POST | 业务核心 | 发起账户关系绑定业务请求。 |
| `/api/v1/verification/transfer-payment` | POST | 认证系统 | 发起打款验证，验证账户控制权。 |
| `/api/v1/verification/transfer-payment/{verificationId}/confirm` | POST | 认证系统 | 提交用户回填的打款金额，完成验证。 |
| `/api/v1/verification/face` | POST | 认证系统 | 发起人脸识别验证请求。 |
| `/api/v1/verification/{verificationId}` | GET | 认证系统 | 同步查询某次验证的详细状态和结果。 |

### 4.1.4 分账业务
| 接口路径 | 方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/tiancai/split-orders` | POST | 三代系统 | 天财发起分账指令的统一入口（归集、批量付款、会员结算）。 |
| `/api/v1/tiancai/split-orders` | POST | 钱包APP/商服平台模块 | 发起分账指令（归集、批量付款、会员结算）。 |
| `/api/v1/tiancai/business/split-orders` | POST | 业务核心 | 发起分账业务请求。 |
| `/api/v1/tiancai/split-orders/{split_order_id}` | GET | 三代系统 | 查询分账指令处理状态。 |
| `/api/v1/split-orders` | GET | 钱包APP/商服平台模块 | 分页查询分账订单列表。 |

### 4.1.5 结算与资金处理
| 接口路径 | 方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/settlement/instructions` | POST | 清结算系统 | 接收结算指令，将资金从待结算账户结算至目标天财收款账户。 |
| `/api/v1/refund/fund-adjustments` | POST | 清结算系统 | 处理天财场景的退货资金调拨。 |
| `/api/v1/settlement/instructions/{instruction_id}` | GET | 清结算系统 | 查询结算指令状态。 |
| `/api/v1/settlement/records` | GET | 清结算系统 | 查询结算记录。 |
| `/api/v1/refund/adjustments` | GET | 清结算系统 | 查询退货资金调拨记录。 |

### 4.1.6 对账与查询
| 接口路径 | 方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/tiancai/reconciliations` | GET | 对账单系统 | 查询对账单列表，支持多维度筛选。 |
| `/api/v1/tiancai/reconciliations/generate` | POST | 对账单系统 | 触发对账文件的即时生成。 |
| `/api/v1/tiancai/accounts/{tiancai_account_id}/ledger` | GET | 对账单系统 | 查询指定天财账户的资金变动明细。 |
| `/api/v1/tiancai/institutions/{institution_code}/summary` | GET | 对账单系统 | 查询天财机构在指定日期的各类业务汇总数据。 |
| `/api/v1/tiancai/business/reconciliations` | POST | 业务核心 | 按机构、日期、业务类型生成对账文件。 |

### 4.1.7 电子签约
| 接口路径 | 方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/contracts/processes` | POST | 电子签约平台 | 创建签约流程。 |
| `/api/v1/contracts/processes/{processId}` | GET | 电子签约平台 | 查询签约流程状态。 |
| `/api/v1/contracts/templates/preview` | GET | 电子签约平台 | 生成协议预览。 |

### 4.1.8 用户与权限
| 接口路径 | 方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/user/current` | GET | 钱包APP/商服平台模块 | 获取当前登录用户身份、机构及权限信息。 |

### 4.1.9 计费试算
| 接口路径 | 方法 | 所属模块 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/v1/billing/calculate` | POST | 计费中台 | 计费试算接口，在业务发起前预先计算并返回费用明细。 |

## 4.2 模块间接口

本节描述系统内部各微服务模块之间的关键调用接口。

### 4.2.1 账户系统
| 接口路径 | 方法 | 调用方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/accounts/{account_no}/ledger/entries` | POST | 账务核心系统、计费中台等 | 执行原子化的账务记账（内部调用）。 |

### 4.2.2 三代系统
| 接口路径 | 方法 | 调用方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/internal/tiancai/callback/process` | POST | 行业钱包系统、电子签约平台等 | 供下游系统回调，通知异步流程状态变更。 |

### 4.2.3 行业钱包系统
| 接口路径 | 方法 | 调用方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/internal/tiancai/split-orders` | POST | 三代系统、业务核心 | 处理分账指令（内部接口）。 |

### 4.2.4 账务核心系统
| 接口路径 | 方法 | 调用方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/tiancai/settlement-trigger` | POST | 清结算系统 | 由清结算系统调用，触发将待结算账户资金结算至天财收款账户。 |
| `/api/v1/tiancai/refund-adjustment` | POST | 清结算系统 | 处理涉及天财收款账户的退货资金调整。 |

### 4.2.5 计费中台
| 接口路径 | 方法 | 调用方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/v1/billing/confirm` | POST | 业务核心、三代系统 | 费用确认与冻结接口，在业务正式执行前确认并冻结费用。 |
| `/internal/v1/billing/settle` | POST | 调度任务 | 费用结算指令生成接口（内部），由调度任务触发，对已冻结费用生成结算指令。 |

### 4.2.6 电子签约平台
| 接口路径 | 方法 | 调用方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/webhook/verification` | POST | 认证系统 | 接收认证系统回调，更新签约流程状态。 |

### 4.2.7 对账单系统
| 接口路径 | 方法 | 调用方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/internal/tiancai/reconciliations/verify` | POST | 调度任务 | 触发指定日期和业务类型的数据一致性校验。 |

### 4.2.8 业务核心
| 接口路径 | 方法 | 调用方 | 功能说明 |
| :--- | :--- | :--- | :--- |
| `/api/v1/tiancai/business/{business_id}` | GET | 钱包APP/商服平台模块 | 查询具体业务请求的详细状态和结果。 |

**请求/响应格式说明：**
以上接口的请求和响应格式，通常遵循系统统一的RESTful API规范。请求体多为JSON格式，包含业务参数；响应体包含状态码、消息和业务数据。具体字段定义需参考各接口的详细设计文档。关键内部接口（如账务记账、分账指令处理）会定义严格的数据契约，以确保资金处理的准确性和一致性。