## 5.1 ER图

```mermaid
erDiagram
    biz_instruction {
        bigint id PK
        varchar instruction_type
        varchar status
        jsonb content
        datetime created_at
        datetime updated_at
    }

    merchant_status {
        bigint id PK
        varchar merchant_id
        varchar freeze_status
        datetime synced_at
    }

    relationship_record {
        bigint id PK
        varchar payer_userid
        varchar payee_userid
        varchar relation_type
        varchar agreement_id
        datetime bound_at
    }

    settlement_orders {
        bigint id PK
        varchar order_no
        varchar order_type
        varchar status
        decimal amount
        varchar payer_account_id
        varchar payee_account_id
        datetime created_at
    }

    fee_records {
        bigint id PK
        varchar fee_no
        bigint order_id FK
        decimal fee_amount
        varchar fee_bearer
        datetime created_at
    }

    settlement_batch_details {
        bigint id PK
        bigint batch_order_id FK
        varchar detail_no
        varchar payee_account_id
        decimal amount
        varchar status
    }

    retry_logs {
        bigint id PK
        varchar biz_id
        varchar biz_type
        varchar status
        text error_msg
        datetime created_at
    }

    account {
        bigint id PK
        varchar account_no
        varchar userid
        varchar account_type
        decimal balance
        varchar status
        datetime created_at
    }

    journal_entries {
        bigint id PK
        varchar request_id
        varchar biz_type
        varchar status
        datetime accounting_date
    }

    journal_entry_items {
        bigint id PK
        bigint journal_entry_id FK
        varchar account_no
        decimal debit_amount
        decimal credit_amount
    }

    idempotency_control {
        bigint id PK
        varchar request_id
        varchar biz_key
        varchar status
        datetime created_at
    }

    agreement_template {
        bigint id PK
        varchar template_code
        varchar template_name
        text template_content
        varchar status
    }

    signing_session {
        bigint id PK
        varchar session_id
        varchar template_code
        jsonb parties_info
        varchar status
        datetime expires_at
    }

    signed_agreement {
        bigint id PK
        varchar agreement_id
        bigint session_id FK
        text signed_content
        datetime signed_at
    }

    evidence_record {
        bigint id PK
        bigint agreement_id FK
        jsonb evidence_data
        datetime created_at
    }

    verification_requests {
        bigint id PK
        varchar verification_id
        varchar verification_type
        varchar status
        datetime created_at
    }

    payment_verification_details {
        bigint id PK
        bigint verification_id FK
        varchar bank_card_no
        decimal verification_amount
        varchar confirm_status
    }

    face_verification_details {
        bigint id PK
        bigint verification_id FK
        varchar id_card_no
        varchar name
        varchar face_compare_result
    }

    fee_rule {
        bigint id PK
        varchar rule_code
        varchar biz_scene
        decimal fee_rate
        varchar fee_bearer
        varchar status
    }

    fee_record {
        bigint id PK
        varchar fee_record_no
        varchar rule_code
        decimal calculated_fee
        varchar status
    }

    statement_metadata {
        bigint id PK
        varchar statement_no
        varchar statement_type
        date statement_date
        varchar status
        datetime generated_at
    }

    statement_line_item {
        bigint id PK
        bigint statement_id FK
        varchar item_type
        decimal amount
        varchar account_no
        datetime biz_time
    }

    reconciliation_log {
        bigint id PK
        date recon_date
        varchar source_system
        varchar recon_result
        text discrepancy_detail
        datetime executed_at
    }

    risk_rules {
        bigint id PK
        varchar rule_code
        text rule_condition
        varchar action
        varchar status
    }

    risk_events {
        bigint id PK
        varchar event_id
        varchar target_type
        varchar target_id
        varchar risk_level
        datetime triggered_at
    }

    freeze_instructions {
        bigint id PK
        varchar instruction_id
        varchar target_type
        varchar target_id
        varchar freeze_type
        varchar status
    }

    merchant_risk_profiles {
        bigint id PK
        varchar merchant_id
        jsonb risk_tags
        datetime updated_at
    }

    user_identifiers {
        bigint id PK
        bigint userid
        varchar source_system
        varchar external_id
        datetime created_at
    }

    payout_instruction {
        bigint id PK
        varchar instruction_id
        varchar account_no
        decimal amount
        varchar status
        datetime received_at
    }

    payout_record {
        bigint id PK
        bigint instruction_id FK
        varchar channel_order_no
        varchar channel
        varchar final_status
        datetime completed_at
    }

    biz_instruction ||--o{ settlement_orders : "生成"
    settlement_orders ||--o{ fee_records : "关联计费"
    settlement_orders ||--o{ settlement_batch_details : "包含明细"
    account ||--o{ journal_entry_items : "记录分录"
    journal_entries ||--o{ journal_entry_items : "包含明细"
    signing_session ||--o{ signed_agreement : "生成协议"
    signed_agreement ||--o|| evidence_record : "关联证据"
    verification_requests ||--o{ payment_verification_details : "包含打款详情"
    verification_requests ||--o{ face_verification_details : "包含人脸详情"
    statement_metadata ||--o{ statement_line_item : "包含明细"
    risk_events ||--o{ freeze_instructions : "触发冻结"
    payout_instruction ||--o{ payout_record : "生成出款记录"
    relationship_record }o--o| user_identifiers : "关联付款方/收款方"
    account }o--o| user_identifiers : "属于用户"
```

## 5.2 表结构

| 表名 | 所属模块 | 主要字段（简述） | 关联关系（简述） |
| :--- | :--- | :--- | :--- |
| biz_instruction | 三代 | id, instruction_type, status, content, created_at | 生成清结算订单(settlement_orders) |
| merchant_status | 三代 | id, merchant_id, freeze_status, synced_at | TBD |
| relationship_record | 三代 | id, payer_userid, payee_userid, relation_type, agreement_id, bound_at | 关联用户标识(user_identifiers) |
| settlement_orders | 清结算 | id, order_no, order_type, status, amount, payer_account_id, payee_account_id, created_at | 被biz_instruction生成，关联fee_records |
| fee_records | 清结算 | id, fee_no, order_id, fee_amount, fee_bearer, created_at | 关联settlement_orders |
| settlement_batch_details | 清结算 | id, batch_order_id, detail_no, payee_account_id, amount, status | 关联settlement_orders |
| retry_logs | 清结算 | id, biz_id, biz_type, status, error_msg, created_at | TBD |
| account | 账户系统 | id, account_no, userid, account_type, balance, status, created_at | 属于用户(user_identifiers)，记录分录(journal_entry_items) |
| journal_entries | 账务核心 | id, request_id, biz_type, status, accounting_date | 包含明细(journal_entry_items) |
| journal_entry_items | 账务核心 | id, journal_entry_id, account_no, debit_amount, credit_amount | 关联journal_entries和account |
| idempotency_control | 账务核心 | id, request_id, biz_key, status, created_at | TBD |
| agreement_template | 电子签约平台 | id, template_code, template_name, template_content, status | TBD |
| signing_session | 电子签约平台 | id, session_id, template_code, parties_info, status, expires_at | 生成协议(signed_agreement) |
| signed_agreement | 电子签约平台 | id, agreement_id, session_id, signed_content, signed_at | 关联signing_session和evidence_record |
| evidence_record | 电子签约平台 | id, agreement_id, evidence_data, created_at | 关联signed_agreement |
| verification_requests | 认证系统 | id, verification_id, verification_type, status, created_at | 包含payment_verification_details和face_verification_details |
| payment_verification_details | 认证系统 | id, verification_id, bank_card_no, verification_amount, confirm_status | 关联verification_requests |
| face_verification_details | 认证系统 | id, verification_id, id_card_no, name, face_compare_result | 关联verification_requests |
| fee_rule | 计费中台 | id, rule_code, biz_scene, fee_rate, fee_bearer, status | TBD |
| fee_record | 计费中台 | id, fee_record_no, rule_code, calculated_fee, status | TBD |
| statement_metadata | 对账单系统 | id, statement_no, statement_type, statement_date, status, generated_at | 包含明细(statement_line_item) |
| statement_line_item | 对账单系统 | id, statement_id, item_type, amount, account_no, biz_time | 关联statement_metadata |
| reconciliation_log | 对账单系统 | id, recon_date, source_system, recon_result, discrepancy_detail, executed_at | TBD |
| risk_rules | 风控 | id, rule_code, rule_condition, action, status | TBD |
| risk_events | 风控 | id, event_id, target_type, target_id, risk_level, triggered_at | 触发冻结(freeze_instructions) |
| freeze_instructions | 风控 | id, instruction_id, target_type, target_id, freeze_type, status | 被risk_events触发 |
| merchant_risk_profiles | 风控 | id, merchant_id, risk_tags, updated_at | TBD |
| user_identifiers | 用户中心 | id, userid, source_system, external_id, created_at | 被relationship_record和account关联 |
| payout_instruction | 代付系统 | id, instruction_id, account_no, amount, status, received_at | 生成出款记录(payout_record) |
| payout_record | 代付系统 | id, instruction_id, channel_order_no, channel, final_status, completed_at | 关联payout_instruction |