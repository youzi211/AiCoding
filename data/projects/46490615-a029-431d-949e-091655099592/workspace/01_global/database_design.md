# 5. 数据库设计

## 5.1 ER图

```mermaid
erDiagram
    /* 商户与账户核心 */
    merchant ||--o{ tiancai_account : "拥有"
    merchant ||--o{ binding_application : "发起"
    tiancai_account ||--o{ account_binding_card : "绑定"
    tiancai_account ||--o{ account_status_log : "记录状态变更"
    tiancai_account ||--o{ wallet_account_cache : "同步缓存"

    /* 关系绑定与认证 */
    binding_application ||--|| auth_request : "触发"
    auth_request ||--o{ auth_operation_log : "记录操作"
    auth_request ||--|| contract_task : "对应"
    contract_task ||--o{ contract_signer : "包含签署方"
    contract_task ||--o{ contract_evidence : "存证"
    wallet_binding ||--|| tiancai_relationship : "业务关系"
    tiancai_relationship ||--o{ tiancai_business_flow : "产生业务流水"

    /* 资金流转与清结算 */
    split_transfer_order ||--|| settlement_order : "生成"
    settlement_order ||--o{ settlement_detail : "包含明细"
    tiancai_batch_payment_detail }o--|| batch_payment_item : "对应"
    batch_payment_job ||--o{ batch_payment_item : "包含"
    settlement_order ||--o{ t_fee_transaction : "关联计费"
    t_fee_transaction ||--|| t_fee_rate_config : "使用费率"

    /* 账户账簿与流水 */
    tiancai_account ||--o{ account_ledger : "对应分户账"
    account_ledger ||--o{ ledger_journal : "记录流水"
    account_ledger ||--o{ account_transaction : "生成动账明细"

    /* 风控与退货 */
    risk_decision_record }|--|| risk_rule : "命中"
    risk_decision_record }|--|| risk_list : "检查名单"
    risk_decision_record }|--|| risk_feature : "使用特征"
    refund_preprocess_record ||--|| refund_account_config : "依据配置"

    /* 对账 */
    business_statement ||--o{ reconciliation_task : "触发核对"
    reconciliation_task ||--o{ reconciliation_discrepancy : "发现差异"

    /* 实体定义 */
    merchant {
        string merchant_no PK "商户号"
        string merchant_name "商户名称"
        string status "状态"
        datetime create_time "创建时间"
    }

    tiancai_account {
        string account_no PK "账户号"
        string merchant_no FK "所属商户号"
        string account_type "账户类型"
        string status "状态"
        datetime open_time "开户时间"
    }

    wallet_binding {
        string binding_id PK "绑定关系ID"
        string payer_account_no FK "付款方账户号"
        string payee_account_no FK "收款方账户号"
        string auth_status "认证状态"
        string payment_status "付款开通状态"
    }

    settlement_order {
        string order_no PK "清结算订单号"
        string biz_order_no "业务订单号"
        string order_type "订单类型"
        decimal total_amount "总金额"
        string status "状态"
    }

    account_ledger {
        bigint id PK
        string account_no FK "账户号"
        decimal balance "余额"
        decimal frozen_balance "冻结余额"
        datetime last_updated "最后更新时间"
    }
```

## 5.2 表结构

### 5.2.1 账户与商户模块

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **merchant** | 三代系统 | `merchant_no`(PK), `merchant_name`, `status`, `create_time`。存储收单商户基础信息。 | 1:N `tiancai_account`, 1:N `binding_application` |
| **tiancai_account** | 账户系统 / 天财分账模块 | `account_no`(PK), `merchant_no`(FK), `account_type`, `status`, `open_time`。天财专用账户核心信息。 | N:1 `merchant`, 1:N `account_binding_card`, 1:N `account_status_log`, 1:1 `account_ledger` |
| **account_binding_card** | 账户系统 | `id`(PK), `account_no`(FK), `card_no`, `bank_name`, `bind_status`。账户绑定的银行卡信息。 | N:1 `tiancai_account` |
| **account_status_log** | 账户系统 | `id`(PK), `account_no`(FK), `old_status`, `new_status`, `operator`, `change_time`。账户状态变更历史。 | N:1 `tiancai_account` |
| **wallet_account_cache** | 行业钱包系统 | `id`(PK), `account_no`(FK), `merchant_no`, `account_info`(JSON), `sync_time`。从账户系统同步的账户信息缓存。 | N:1 `tiancai_account` |

### 5.2.2 关系绑定与认证模块

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **binding_application** | 三代系统 | `binding_id`(PK), `merchant_no`(FK), `payer_info`, `payee_info`, `apply_status`。分账关系绑定申请记录。 | N:1 `merchant`, 1:1 `auth_request` |
| **auth_request** | 认证系统 | `auth_request_id`(PK), `binding_id`(FK), `auth_type`, `auth_status`, `result`, `finish_time`。认证请求核心信息与结果。 | 1:1 `binding_application`, 1:N `auth_operation_log`, 1:1 `contract_task` |
| **auth_operation_log** | 认证系统 | `id`(PK), `auth_request_id`(FK), `operation`, `operator`, `operate_time`。认证流程关键操作日志。 | N:1 `auth_request` |
| **wallet_binding** | 行业钱包系统 | `binding_id`(PK), `payer_account_no`(FK), `payee_account_no`(FK), `auth_status`, `payment_status`。分账授权关系的权威存储。 | 关联 `tiancai_account` (付款方与收款方) |
| **tiancai_relationship** | 业务核心系统 / 天财分账模块 | `relationship_id`(PK), `payer_account_no`, `payee_account_no`, `binding_id`, `status`。天财分账业务视角的关系绑定记录。 | 1:1 `wallet_binding`, 1:N `tiancai_business_flow` |
| **tiancai_business_flow** | 业务核心系统 | `flow_no`(PK), `relationship_id`(FK), `biz_type`, `request_data`, `status`, `create_time`。天财分账业务流水，记录所有请求。 | N:1 `tiancai_relationship` |

### 5.2.3 电子签约模块

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **contract_task** | 电子签章系统 | `contract_task_id`(PK), `auth_request_id`(FK), `template_id`, `contract_status`, `signed_file_url`。签约任务主表。 | 1:1 `auth_request`, 1:N `contract_signer`, 1:N `contract_evidence` |
| **contract_signer** | 电子签章系统 | `id`(PK), `contract_task_id`(FK), `signer_id`, `signer_role`, `sign_status`。签约任务中的签署方信息。 | N:1 `contract_task` |
| **contract_template** | 电子签章系统 | `template_id`(PK), `template_name`, `template_file_hash`, `status`。协议模板库。 | 1:N `contract_task` |
| **contract_evidence** | 电子签章系统 | `id`(PK), `contract_task_id`(FK), `evidence_type`, `evidence_data`, `timestamp`。签约过程存证链。 | N:1 `contract_task` |

### 5.2.4 资金流转与清结算模块

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **split_transfer_order** | 三代系统 | `order_no`(PK), `biz_type`, `payer_account_no`, `total_amount`, `status`。分账/归集/付款指令订单。 | 1:1 `settlement_order` |
| **settlement_order** | 清结算系统 | `order_no`(PK), `biz_order_no`(FK), `order_type`, `total_amount`, `status`, `settle_time`。清结算主订单。 | 1:1 `split_transfer_order`, 1:N `settlement_detail`, 1:1 `t_fee_transaction` |
| **settlement_detail** | 清结算系统 | `id`(PK), `order_no`(FK), `payee_account_no`, `amount`, `settle_status`。清结算分账明细。 | N:1 `settlement_order` |
| **tiancai_batch_payment_detail** | 业务核心系统 | `id`(PK), `batch_no`, `payee_account_no`, `amount`, `status`。天财批量付款业务明细。 | 1:1 `batch_payment_item` |
| **batch_payment_job** | 天财分账模块 | `job_id`(PK), `total_count`, `success_count`, `job_status`。批量付款任务。 | 1:N `batch_payment_item` |
| **batch_payment_item** | 天财分账模块 | `item_id`(PK), `job_id`(FK), `payee_account_no`, `amount`, `item_status`。批量付款任务明细。 | N:1 `batch_payment_job` |
| **split_transfer_record** | 行业钱包系统 | `record_id`(PK), `order_no`, `process_status`, `result_code`, `process_time`。分账指令处理记录。 | 关联 `settlement_order` |

### 5.2.5 计费模块

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **t_fee_transaction** | 计费中台 | `transaction_id`(PK), `order_no`(FK), `fee_amount`, `payer_account_no`, `calc_status`, `settle_status`。计费交易记录。 | 1:1 `settlement_order`, N:1 `t_fee_rate_config` |
| **t_fee_rate_config** | 计费中台 | `config_id`(PK), `merchant_no`, `product_code`, `fee_rate`, `effective_time`。从三代系统同步的费率规则缓存。 | 1:N `t_fee_transaction` |
| **t_fee_daily_summary** | 计费中台 | `id`(PK), `summary_date`, `merchant_no`, `total_fee`, `transaction_count`。计费日汇总表。 | - |
| **fee_config** | 三代系统 | `config_id`(PK), `merchant_no`, `scene`, `rule`(JSON), `status`。分账业务手续费规则配置（权威源）。 | - |

### 5.2.6 账户账簿与流水模块

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **account_ledger** | 清结算系统 | `id`(PK), `account_no`(FK), `balance`, `frozen_balance`, `last_updated`。账户分户账簿，余额权威数据源。 | 1:1 `tiancai_account`, 1:N `ledger_journal`, 1:N `account_transaction` |
| **ledger_journal** | 清结算系统 | `journal_id`(PK), `account_no`(FK), `order_no`, `change_amount`, `balance_after`, `journal_time`。账户资金变动流水日记账。 | N:1 `account_ledger` |
| **account_transaction** | 对账单系统 | `transaction_id`(PK), `account_no`(FK), `order_no`, `amount`, `balance_after`, `trade_time`, `summary`。面向查询的账户动账明细。 | N:1 `account_ledger` |

### 5.2.7 风控模块

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **risk_decision_record** | 风控系统 | `record_id`(PK), `request_id`, `entity_type`, `entity_id`, `risk_level`, `action`, `hit_rule_ids`。风险决策记录。 | N:N `risk_rule`, N:N `risk_list`, N:N `risk_feature` |
| **risk_rule** | 风控系统 | `rule_id`(PK), `rule_name`, `condition`(JSON), `risk_level`, `action`, `status`。可配置的风险规则。 | N:N `risk_decision_record` |
| **risk_list** | 风控系统 | `list_id`(PK), `entity_type`, `entity_value`, `list_type`, `expire_time`。风险名单（黑/灰/白名单）。 | N:N `risk_decision_record` |
| **risk_feature** | 风控系统 | `feature_id`(PK), `entity_type`, `entity_id`, `feature_name`, `feature_value`, `calc_time`。风险特征快照。 | N:N `risk_decision_record` |
| **risk_case** | 风控系统 | `case_id`(PK), `related_record_ids`, `case_status`, `assignee`, `close_time`。人工处理的风险案件。 | - |

### 5.2.8 退货前置模块

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **refund_preprocess_record** | 退货前置模块 / 清结算系统 | `record_id`(PK), `original_order_no`, `request_amount`, `deducted_amount`, `status`, `account_config_id`。退货前置处理全流程记录。 | N:1 `refund_account_config` |
| **refund_account_config** | 退货前置模块 | `config_id`(PK), `merchant_no`, `deduct_account_no`, `priority`, `status`。定义商户退货扣款账户规则。 | 1:N `refund_preprocess_record` |

### 5.2.9 对账模块

| 表名 | 所属模块 | 主要字段说明 | 与其他表的关系 |
| :--- | :--- | :--- | :--- |
| **business_statement** | 对账单系统 | `statement_no`(PK), `merchant_no`, `statement_date`, `total_income`, `total_payout`, `status`。业务对账单主表。 | 1:N `reconciliation_task` |
| **reconciliation_task** | 对账单系统 | `task_id`(PK), `statement_no`(FK), `task_type`, `data_source_a`, `data_source_b`, `task_status`。数据核对任务。 | N:1 `business_statement`, 1:N `reconciliation_discrepancy` |
| **reconciliation_discrepancy** | 对账单系统 | `id`(PK), `task_id`(FK), `diff_type`, `diff_amount`, `data_a_snapshot`, `data_b_snapshot`。核对发现的差异明细。 | N:1 `reconciliation_task` |