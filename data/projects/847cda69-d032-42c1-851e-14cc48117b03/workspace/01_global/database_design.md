## 5.1 ER图
```mermaid
erDiagram
    tiancai_accounts {
        string account_id PK
        string merchant_id FK
        string account_type
        string status
        string capabilities
    }

    tiancai_merchant_configs {
        string merchant_id PK
        string account_id FK
        string settlement_config
        string fee_config
        string status
    }

    tiancai_business_relationships {
        string relationship_id PK
        string payer_account_id FK
        string payee_account_id FK
        string scene_type
        string status
        string sign_request_id FK
    }

    tiancai_ledger_records {
        string record_id PK
        string relationship_id FK
        string amount
        string status
        string scene_type
    }

    tiancai_split_record {
        string record_id PK
        string ledger_record_id FK
        string amount
        string status
    }

    verification_requests {
        string id PK
        string request_type
        string status
        string external_id
    }

    payment_attempts {
        string id PK
        string verification_id FK
        string amount
        string status
    }

    sign_requests {
        string sign_request_id PK
        string business_scene
        string status
        string merchant_id FK
    }

    sign_records {
        string id PK
        string sign_request_id FK
        string signer_info
        string signed_at
    }

    auth_attempts {
        string id PK
        string sign_request_id FK
        string auth_type
        string auth_result
    }

    settlement_config {
        string id PK
        string account_id FK
        string config_data
    }

    account_freeze_record {
        string id PK
        string account_id FK
        string operation
        string operated_at
    }

    billing_sync_log {
        string id PK
        string transaction_ref
        string fee_info
        string synced_at
    }

    fee_rule {
        string id PK
        string scene
        string rule_config
    }

    fee_transaction_log {
        string id PK
        string request_ref
        string calculated_fee
        string calculated_at
    }

    tiancai_statements {
        string statement_id PK
        string merchant_id FK
        string period
        string file_url
    }

    tiancai_statement_items {
        string id PK
        string statement_id FK
        string item_type
        string amount
    }

    tiancai_accounts ||--o{ tiancai_merchant_configs : "配置"
    tiancai_accounts ||--o{ tiancai_business_relationships : "作为付方"
    tiancai_accounts ||--o{ tiancai_business_relationships : "作为收方"
    tiancai_accounts ||--o{ settlement_config : "拥有"
    tiancai_accounts ||--o{ account_freeze_record : "被操作"
    tiancai_merchant_configs }o--|| tiancai_accounts : "关联"
    tiancai_business_relationships }o--|| sign_requests : "关联签约"
    tiancai_business_relationships ||--o{ tiancai_ledger_records : "发起"
    tiancai_ledger_records ||--o{ tiancai_split_record : "对应"
    verification_requests ||--o{ payment_attempts : "包含"
    sign_requests ||--o{ sign_records : "产生"
    sign_requests ||--o{ auth_attempts : "包含"
    tiancai_statements ||--o{ tiancai_statement_items : "包含"
```
*注：部分实体间关系（如`tiancai_merchant_configs`与`sign_requests`）因信息缺失，暂未在图中体现。*

## 5.2 表结构

| 表名 | 所属模块 | 主要字段（简述） | 关联关系（简述） |
| :--- | :--- | :--- | :--- |
| `tiancai_accounts` | 账户系统 | `account_id`(主键), `merchant_id`, `account_type`, `status`, `capabilities` | 被`tiancai_merchant_configs`、`tiancai_business_relationships`、`settlement_config`、`account_freeze_record`关联 |
| `tiancai_merchant_configs` | 三代系统 | `merchant_id`(主键), `account_id`, `settlement_config`, `fee_config`, `status` | 关联`tiancai_accounts`表 |
| `tiancai_business_relationships` | 行业钱包系统 | `relationship_id`(主键), `payer_account_id`, `payee_account_id`, `scene_type`, `status`, `sign_request_id` | 关联`tiancai_accounts`（付方/收方）、`sign_requests`、`tiancai_ledger_records`表 |
| `tiancai_ledger_records` | 行业钱包系统 | `record_id`(主键), `relationship_id`, `amount`, `status`, `scene_type` | 关联`tiancai_business_relationships`、`tiancai_split_record`表 |
| `tiancai_split_record` | 业务核心系统 | `record_id`(主键), `ledger_record_id`, `amount`, `status` | 关联`tiancai_ledger_records`表 |
| `verification_requests` | 认证系统 | `id`(主键), `request_type`, `status`, `external_id` | 关联`payment_attempts`表 |
| `payment_attempts` | 认证系统 | `id`(主键), `verification_id`, `amount`, `status` | 关联`verification_requests`表 |
| `sign_requests` | 电子签约平台 | `sign_request_id`(主键), `business_scene`, `status`, `merchant_id` | 关联`tiancai_business_relationships`、`sign_records`、`auth_attempts`表 |
| `sign_records` | 电子签约平台 | `id`(主键), `sign_request_id`, `signer_info`, `signed_at` | 关联`sign_requests`表 |
| `auth_attempts` | 电子签约平台 | `id`(主键), `sign_request_id`, `auth_type`, `auth_result` | 关联`sign_requests`表 |
| `settlement_config` | 清结算系统 | `id`(主键), `account_id`, `config_data` | 关联`tiancai_accounts`表 |
| `account_freeze_record` | 清结算系统 | `id`(主键), `account_id`, `operation`, `operated_at` | 关联`tiancai_accounts`表 |
| `billing_sync_log` | 清结算系统 | `id`(主键), `transaction_ref`, `fee_info`, `synced_at` | TBD |
| `fee_rule` | 计费中台 | `id`(主键), `scene`, `rule_config` | TBD |
| `fee_transaction_log` | 计费中台 | `id`(主键), `request_ref`, `calculated_fee`, `calculated_at` | TBD |
| `tiancai_statements` | 对账单系统 | `statement_id`(主键), `merchant_id`, `period`, `file_url` | 关联`tiancai_statement_items`表 |
| `tiancai_statement_items` | 对账单系统 | `id`(主键), `statement_id`, `item_type`, `amount` | 关联`tiancai_statements`表 |