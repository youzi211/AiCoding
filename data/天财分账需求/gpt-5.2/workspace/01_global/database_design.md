# 5. 数据库设计

## 5.1 ER图

```mermaid
erDiagram
    %% 账户与商户核心
    account {
        varchar account_no PK "账户号"
        decimal balance "余额"
        varchar status "状态"
        varchar capability_flags "能力标记"
    }

    tiancai_account {
        varchar tiancai_account_id PK "天财账户ID"
        varchar account_no FK "关联底层账户号"
        varchar account_type "账户类型"
        varchar institution_code "所属机构代码"
        varchar status "状态"
    }

    tiancai_merchant_config {
        varchar merchant_no PK "商户号"
        varchar status "天财业务开通状态"
        timestamp enabled_at "开通时间"
    }

    merchant_account_mapping {
        varchar id PK
        varchar merchant_no FK "商户号"
        varchar tiancai_account_id FK "天财账户ID"
    }

    %% 关系绑定与认证
    account_relationship {
        varchar id PK
        varchar source_account_id FK "源账户ID"
        varchar target_account_id FK "目标账户ID"
        varchar relation_type "关系类型"
        varchar status "状态"
        varchar contract_process_id FK "签约流程ID"
    }

    verification_record {
        varchar verification_id PK "验证ID"
        varchar business_type "业务类型"
        varchar target_account_id FK "目标账户ID"
        varchar status "状态"
        json verification_data "验证数据"
    }

    contract_process {
        varchar process_id PK "流程ID"
        varchar business_type "业务类型"
        varchar business_id "关联业务ID"
        varchar status "状态"
        varchar signed_document_id FK "已签署文件ID"
    }

    %% 业务流程与订单
    business_process {
        varchar business_id PK "业务ID"
        varchar business_type "业务类型"
        varchar merchant_no FK "商户号"
        varchar status "状态"
        varchar result "结果"
    }

    tiancai_split_order {
        varchar split_order_id PK "分账订单ID"
        varchar business_id FK "关联业务ID"
        varchar split_order_no "分账订单号"
        varchar order_type "订单类型"
        decimal total_amount "总金额"
        varchar status "状态"
    }

    split_order_detail {
        varchar id PK
        varchar split_order_id FK "分账订单ID"
        varchar payee_account_id FK "收款方账户ID"
        decimal amount "分账金额"
        varchar status "状态"
    }

    %% 账务与计费
    account_transaction {
        varchar transaction_id PK "交易流水ID"
        varchar account_no FK "账户号"
        varchar business_order_no "业务订单号"
        decimal amount "金额"
        varchar transaction_type "交易类型"
        timestamp transaction_time "交易时间"
    }

    billing_order {
        varchar billing_order_id PK "计费订单ID"
        varchar business_order_no "关联业务订单号"
        decimal total_fee "总费用"
        varchar fee_status "费用状态"
        varchar settlement_instruction_id FK "结算指令ID"
    }

    settlement_instruction {
        varchar instruction_id PK "指令ID"
        varchar business_order_no "关联业务订单号"
        decimal amount "结算金额"
        varchar payer_account_id FK "付款方账户ID"
        varchar payee_account_id FK "收款方账户ID"
        varchar status "状态"
    }

    %% 对账与文件
    account_ledger {
        varchar ledger_id PK "流水ID"
        varchar tiancai_account_id FK "天财账户ID"
        varchar business_order_no "业务订单号"
        decimal amount "金额"
        varchar ledger_type "流水类型"
        date business_date "业务日期"
    }

    reconciliation_file {
        varchar file_id PK "文件ID"
        varchar institution_code "机构代码"
        date reconciliation_date "对账日期"
        varchar file_type "文件类型"
        varchar file_path "文件路径"
        varchar status "状态"
    }

    %% 关系定义
    account ||--o{ tiancai_account : "映射为"
    tiancai_merchant_config ||--o{ merchant_account_mapping : "拥有"
    tiancai_account ||--o{ merchant_account_mapping : "被映射"
    tiancai_account ||--o{ account_relationship : "作为源"
    tiancai_account ||--o{ account_relationship : "作为目标"
    account_relationship }o--|| contract_process : "通过"
    verification_record }o--|| tiancai_account : "验证"
    business_process ||--o{ tiancai_split_order : "产生"
    tiancai_split_order ||--o{ split_order_detail : "包含"
    tiancai_split_order }o--|| account_transaction : "生成"
    tiancai_split_order }o--|| billing_order : "关联"
    billing_order }o--|| settlement_instruction : "驱动"
    tiancai_account ||--o{ account_ledger : "拥有流水"
    tiancai_split_order }o--|| account_ledger : "对应"
```

## 5.2 表结构

### 5.2.1 账户与商户核心表

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **account** | 账户系统 | `account_no` (PK): 账户号，唯一标识一个底层资金账户。<br>`balance`: 当前账户余额。<br>`status`: 账户状态（如：ACTIVE, FROZEN, CLOSED）。<br>`capability_flags`: 账户能力标记（如：可收款、可付款、可分账）。 | 1. 被 `tiancai_account` 表通过 `account_no` 关联。 |
| **tiancai_account** | 账户系统 | `tiancai_account_id` (PK): 天财业务专用账户ID。<br>`account_no` (FK): 关联的底层标准账户号。<br>`account_type`: 账户类型（如：总部、门店、会员）。<br>`institution_code`: 所属天财机构代码。<br>`status`: 天财账户状态。 | 1. 外键 `account_no` 关联 `account` 表。<br>2. 被 `merchant_account_mapping`、`account_relationship`、`account_ledger` 等多表关联。 |
| **tiancai_merchant_config** | 三代系统 | `merchant_no` (PK): 收单商户号。<br>`status`: 该商户的天财分账业务开通状态。<br>`enabled_at`: 业务开通时间。 | 1. 被 `merchant_account_mapping` 表通过 `merchant_no` 关联。 |
| **merchant_account_mapping** | 业务核心/三代系统 | `id` (PK): 主键。<br>`merchant_no` (FK): 商户号。<br>`tiancai_account_id` (FK): 天财账户ID。 | 1. 外键 `merchant_no` 关联 `tiancai_merchant_config` 表。<br>2. 外键 `tiancai_account_id` 关联 `tiancai_account` 表。 |

### 5.2.2 关系绑定与认证表

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **account_relationship** | 账户系统/行业钱包系统 | `id` (PK): 主键。<br>`source_account_id` (FK): 源天财账户ID（如：门店）。<br>`target_account_id` (FK): 目标天财账户ID（如：总部）。<br>`relation_type`: 关系类型（如：归集授权）。<br>`status`: 绑定状态。<br>`contract_process_id` (FK): 关联的电子签约流程ID。 | 1. 外键 `source_account_id` 和 `target_account_id` 均关联 `tiancai_account` 表。<br>2. 外键 `contract_process_id` 关联 `contract_process` 表。 |
| **verification_record** | 认证系统 | `verification_id` (PK): 验证记录唯一ID。<br>`business_type`: 验证业务类型（打款、人脸等）。<br>`target_account_id` (FK): 被验证的天财账户ID。<br>`status`: 验证状态。<br>`verification_data`: 验证过程数据（JSON格式）。 | 1. 外键 `target_account_id` 关联 `tiancai_account` 表。 |
| **contract_process** | 电子签约平台 | `process_id` (PK): 签约流程ID。<br>`business_type`: 关联业务类型（如：账户绑定）。<br>`business_id`: 关联的业务ID（如：`account_relationship.id`）。<br>`status`: 签约流程状态。<br>`signed_document_id`: 已签署的文件ID。 | 1. 被 `account_relationship` 表通过 `contract_process_id` 关联。 |

### 5.2.3 业务流程与订单表

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **business_process** | 业务核心 | `business_id` (PK): 业务流程唯一ID。<br>`business_type`: 业务类型（开通、绑定、分账）。<br>`merchant_no` (FK): 发起业务的商户号。<br>`status`: 业务流程状态。<br>`result`: 最终处理结果。 | 1. 外键 `merchant_no` 关联 `tiancai_merchant_config` 表。<br>2. 被 `tiancai_split_order` 表通过 `business_id` 关联。 |
| **tiancai_split_order** | 三代系统/行业钱包系统/账务核心系统 | `split_order_id` (PK): 分账订单主键ID。<br>`business_id` (FK): 关联的业务流程ID。<br>`split_order_no`: 分账订单号，用于外部展示和关联。<br>`order_type`: 订单类型（归集、批量付款、会员结算）。<br>`total_amount`: 分账总金额。<br>`status`: 订单状态。 | 1. 外键 `business_id` 关联 `business_process` 表。<br>2. 被 `split_order_detail`、`account_transaction`、`account_ledger` 等表关联。 |
| **split_order_detail** | 行业钱包系统 | `id` (PK): 主键。<br>`split_order_id` (FK): 所属分账订单ID。<br>`payee_account_id` (FK): 收款方天财账户ID。<br>`amount`: 分给该收款方的金额。<br>`status`: 该笔分账明细的状态。 | 1. 外键 `split_order_id` 关联 `tiancai_split_order` 表。<br>2. 外键 `payee_account_id` 关联 `tiancai_account` 表。 |

### 5.2.4 账务、计费与结算表

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **account_transaction** | 账务核心系统 | `transaction_id` (PK): 交易流水ID。<br>`account_no` (FK): 发生交易的底层账户号。<br>`business_order_no`: 关联的业务订单号（如分账订单号）。<br>`amount`: 交易金额。<br>`transaction_type`: 交易类型（支出、收入）。<br>`transaction_time`: 交易时间。 | 1. 外键 `account_no` 关联 `account` 表。<br>2. 通过 `business_order_no` 与 `tiancai_split_order.split_order_no` 逻辑关联。 |
| **billing_order** | 计费中台 | `billing_order_id` (PK): 计费订单ID。<br>`business_order_no`: 关联的业务订单号。<br>`total_fee`: 计算出的总费用。<br>`fee_status`: 费用状态（待确认、已冻结、已结算）。<br>`settlement_instruction_id` (FK): 关联的结算指令ID。 | 1. 通过 `business_order_no` 与业务订单逻辑关联。<br>2. 外键 `settlement_instruction_id` 关联 `settlement_instruction` 表。 |
| **settlement_instruction** | 计费中台/清结算系统 | `instruction_id` (PK): 结算指令ID。<br>`business_order_no`: 关联的业务订单号。<br>`amount`: 需要结算的金额。<br>`payer_account_id` (FK): 付款方天财账户ID。<br>`payee_account_id` (FK): 收款方天财账户ID。<br>`status`: 指令状态。 | 1. 外键 `payer_account_id` 和 `payee_account_id` 关联 `tiancai_account` 表。<br>2. 被 `billing_order` 表关联。 |

### 5.2.5 对账与文件表

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **account_ledger** | 对账单系统 | `ledger_id` (PK): 账户流水明细ID。<br>`tiancai_account_id` (FK): 天财账户ID。<br>`business_order_no`: 引起流水的业务订单号。<br>`amount`: 流水金额。<br>`ledger_type`: 流水类型（如：分账收入、结算支出）。<br>`business_date`: 业务发生日期。 | 1. 外键 `tiancai_account_id` 关联 `tiancai_account` 表。<br>2. 通过 `business_order_no` 与 `tiancai_split_order` 等业务订单表逻辑关联。 |
| **reconciliation_file** | 对账单系统 | `file_id` (PK): 对账文件ID。<br>`institution_code`: 所属机构代码。<br>`reconciliation_date`: 对账日期。<br>`file_type`: 文件类型（日账单、交易明细等）。<br>`file_path`: 文件在对象存储中的路径。<br>`status`: 文件生成状态。 | 1. 通过 `institution_code` 与 `tiancai_account.institution_code` 逻辑关联。 |

### 5.2.6 其他辅助表

*   **`user` (钱包APP/商服平台模块)**: 存储平台用户信息、所属机构及权限。
*   **`frontend_split_order` (钱包APP/商服平台模块)**: 记录前端发起的订单草稿及展示状态，与后端的 `tiancai_split_order` 关联。
*   **`billing_rule` (计费中台)**: 存储计费规则。
*   **`billing_detail` (计费中台)**: 记录计费订单的明细构成。
*   **`tiancai_process_flow` (三代系统)**: 记录异步业务流程的步骤状态。
*   **`settlement_record` (清结算系统)**: 记录结算指令执行后的资金划转结果。
*   **`refund_fund_adjustment` (清结算系统)**: 记录退货资金调拨明细。
*   **`contract_document` (电子签约平台)**: 存储已签署的协议文件。
*   **`daily_summary` (对账单系统)**: 存储业务的日终汇总数据。