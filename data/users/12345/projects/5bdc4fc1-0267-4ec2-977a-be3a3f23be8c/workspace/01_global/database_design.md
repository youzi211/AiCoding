## 5.1 ER图
```mermaid
erDiagram
    wallet_account {
        string account_id PK
        string merchant_id
        string account_type
        string status
        string institution_id
    }

    binding_relationship {
        string binding_id PK
        string payer_account_id FK
        string receiver_account_id FK
        string relationship_type
        string status
    }

    split_order {
        string order_id PK
        string payer_account_id FK
        string receiver_account_id FK
        string amount
        string fee_bearer
        string status
    }

    account {
        string account_id PK
        string account_type
        string balance
        string special_mark
        string status
    }

    account_balance {
        string account_id FK
        string balance_type
        bigint amount
    }

    transaction_ledger {
        string transaction_id PK
        string from_account_id FK
        string to_account_id FK
        bigint amount
        string transaction_type
    }

    signing_records {
        string contract_id PK
        string payer_account_id FK
        string receiver_account_id FK
        string auth_type
        string status
    }

    evidence_chain {
        string evidence_id PK
        string contract_id FK
        string evidence_type
        string evidence_data
    }

    auth_request {
        string request_id PK
        string contract_id FK
        string auth_type
        string status
    }

    fee_ledger {
        string fee_id PK
        string order_id FK
        string fee_type
        bigint amount
    }

    statement_job {
        string job_id PK
        string institution_id
        string date_range
        string status
    }

    statement_record {
        string record_id PK
        string job_id FK
        string file_url
    }

    tiancai_split_transaction {
        string transaction_id PK
        string institution_id
        string payer_account_id FK
        string receiver_account_id FK
        bigint amount
        string business_scene
    }

    batch_payment_orders {
        string batch_id PK
        string payer_account_id FK
        string total_amount
        string status
    }

    payment_items {
        string item_id PK
        string batch_id FK
        string receiver_account_id FK
        bigint amount
    }

    user_session {
        string session_id PK
        string user_id
        string flow_type
        string step_data
    }

    idempotent_record {
        string idempotent_key PK
        string business_type
        string result_data
    }

    wallet_account ||--o{ binding_relationship : "作为付方绑定"
    wallet_account ||--o{ binding_relationship : "作为收方绑定"
    wallet_account ||--o{ split_order : "作为付方发起"
    wallet_account ||--o{ split_order : "作为收方接收"
    account ||--|| wallet_account : "对应底层账户"
    account ||--o{ account_balance : "拥有余额"
    account ||--o{ transaction_ledger : "作为转出方"
    account ||--o{ transaction_ledger : "作为转入方"
    wallet_account ||--o{ signing_records : "作为付方签约"
    wallet_account ||--o{ signing_records : "作为收方签约"
    signing_records ||--o{ evidence_chain : "产生证据"
    signing_records ||--o{ auth_request : "发起认证"
    split_order ||--o{ fee_ledger : "产生费用"
    statement_job ||--o{ statement_record : "生成文件"
    tiancai_split_transaction }o--|| wallet_account : "涉及付方账户"
    tiancai_split_transaction }o--|| wallet_account : "涉及收方账户"
    batch_payment_orders ||--o{ payment_items : "包含明细"
    batch_payment_orders }o--|| wallet_account : "由付方发起"
    payment_items }o--|| wallet_account : "支付给收方"
```

## 5.2 表结构

| 表名 | 所属模块 | 主要字段（简述） | 关联关系（简述） |
| :--- | :--- | :--- | :--- |
| wallet_account | 行业钱包 | 账户ID(PK)、商户ID、账户类型、状态、机构号 | 与`account`表一对一关联；与`binding_relationship`表一对多（作为付方/收方）；与`split_order`表一对多（作为付方/收方） |
| binding_relationship | 行业钱包 | 绑定关系ID(PK)、付方账户ID(FK)、收方账户ID(FK)、关系类型、状态 | 关联`wallet_account`表（付方和收方） |
| split_order | 行业钱包 | 订单ID(PK)、付方账户ID(FK)、收方账户ID(FK)、金额、手续费承担方、状态 | 关联`wallet_account`表（付方和收方）；关联`fee_ledger`表 |
| idempotent_record | 行业钱包 | 幂等键(PK)、业务类型、结果数据 | TBD |
| account | 账户系统 | 账户ID(PK)、账户类型、余额、特殊标记、状态 | 与`wallet_account`表一对一关联；与`account_balance`表一对多；与`transaction_ledger`表一对多（转出/转入） |
| account_balance | 账户系统 | 账户ID(FK)、余额类型、金额 | 关联`account`表 |
| transaction_ledger | 账户系统 | 交易流水ID(PK)、转出账户ID(FK)、转入账户ID(FK)、金额、交易类型 | 关联`account`表（转出方和转入方） |
| account_freeze_record | 账户系统 | TBD | TBD |
| signing_records | 电子签约平台 | 签约ID(PK)、付方账户ID(FK)、收方账户ID(FK)、认证类型、状态 | 关联`wallet_account`表（付方和收方）；关联`evidence_chain`表；关联`auth_request`表 |
| evidence_chain | 电子签约平台 | 证据ID(PK)、签约ID(FK)、证据类型、证据数据 | 关联`signing_records`表 |
| sms_template_config | 电子签约平台 | TBD | TBD |
| h5_template_config | 电子签约平台 | TBD | TBD |
| auth_request | 认证系统 | 请求ID(PK)、签约ID(FK)、认证类型、状态 | 关联`signing_records`表 |
| payment_verification | 认证系统 | TBD | TBD |
| face_verification | 认证系统 | TBD | TBD |
| fee_ledger | 计费中台 | 费用ID(PK)、订单ID(FK)、费用类型、金额 | 关联`split_order`表 |
| statement_job | 对账单系统 | 任务ID(PK)、机构号、日期范围、状态 | 关联`statement_record`表 |
| statement_record | 对账单系统 | 记录ID(PK)、任务ID(FK)、文件URL | 关联`statement_job`表 |
| tiancai_split_transaction | 业务核心 | 交易ID(PK)、机构号、付方账户ID(FK)、收方账户ID(FK)、金额、业务场景 | 关联`wallet_account`表（付方和收方） |
| batch_payment_orders | 代付系统 | 批次ID(PK)、付方账户ID(FK)、总金额、状态 | 关联`wallet_account`表；关联`payment_items`表 |
| payment_items | 代付系统 | 明细ID(PK)、批次ID(FK)、收方账户ID(FK)、金额 | 关联`batch_payment_orders`表；关联`wallet_account`表 |
| user_session | 钱包APP/商服平台 | 会话ID(PK)、用户ID、流程类型、步骤数据 | TBD |
| api_cache | 钱包APP/商服平台 | TBD | TBD |
| idempotency_key | 钱包APP/商服平台 | TBD | TBD |
| 商户信息表 | 三代 | TBD | TBD |
| 计费配置表 | 三代 | TBD | TBD |
| 机构信息表 | 三代 | TBD | TBD |
| transaction_log | 账务核心 | TBD | TBD |