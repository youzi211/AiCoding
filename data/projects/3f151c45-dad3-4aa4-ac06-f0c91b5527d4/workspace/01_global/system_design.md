## 2.1 系统结构
本系统采用分层架构，以"三代系统"作为业务入口和管理中枢，通过"行业钱包系统"作为核心业务处理层，协调多个底层能力系统，共同完成天财分账业务。整体架构遵循职责分离原则，确保业务逻辑清晰、系统间解耦。

```mermaid
graph TB
    subgraph "用户交互层"
        APP[钱包APP/商服平台]
    end

    subgraph "业务管理层"
        GEN[三代系统]
    end

    subgraph "核心业务层"
        WALLET[行业钱包系统]
        CORE[业务核心]
    end

    subgraph "能力支撑层"
        ACCOUNT[账户系统]
        SETTLE[清结算]
        BILLING[计费中台]
        E_SIGN[电子签章系统]
        AUTH[认证系统]
    end

    subgraph "数据服务层"
        STATEMENT[对账单系统]
    end

    APP --> WALLET
    APP --> E_SIGN
    APP --> STATEMENT

    GEN --> WALLET

    WALLET --> E_SIGN
    WALLET --> ACCOUNT
    WALLET --> CORE
    WALLET --> BILLING
    WALLET --> SETTLE
    WALLET --> STATEMENT

    CORE --> ACCOUNT
    CORE --> SETTLE
    CORE --> STATEMENT

    E_SIGN --> AUTH

    SETTLE --> ACCOUNT
    SETTLE --> BILLING
    SETTLE --> STATEMENT

    STATEMENT --> ACCOUNT
    STATEMENT --> SETTLE
    STATEMENT --> WALLET
    STATEMENT --> CORE
```

## 2.2 功能结构
系统功能围绕天财分账业务的核心流程展开，主要包括账户管理、关系绑定、分账交易、结算对账四大功能域。

```mermaid
graph TD
    ROOT[天财分账系统] --> FM1[账户管理]
    ROOT --> FM2[关系绑定]
    ROOT --> FM3[分账交易]
    ROOT --> FM4[结算对账]

    FM1 --> FM1_1[账户开户]
    FM1 --> FM1_2[账户状态管理]
    FM1 --> FM1_3[账户能力控制]

    FM2 --> FM2_1[协议签署]
    FM2 --> FM2_2[身份认证]
    FM2 --> FM2_3[关系授权]

    FM3 --> FM3_1[资金归集]
    FM3 --> FM3_2[批量付款]
    FM3 --> FM3_3[会员结算]
    FM3 --> FM3_4[手续费计算]

    FM4 --> FM4_1[交易结算]
    FM4 --> FM4_2[退货处理]
    FM4 --> FM4_3[账单生成]
    FM4 --> FM4_4[数据核对]
```

## 2.3 网络拓扑图
TBD

## 2.4 数据流转
数据流转以"分账指令"和"资金动账"为核心，在三代系统、行业钱包系统、业务核心及账户系统之间传递，最终由对账单系统进行聚合。

```mermaid
flowchart LR
    subgraph S1 [指令发起]
        GEN[三代系统] -- 1. 发起分账指令 --> WALLET[行业钱包系统]
    end

    subgraph S2 [业务处理]
        WALLET -- 2. 请求资金划转 --> CORE[业务核心]
        CORE -- 3. 执行动账 --> ACCOUNT[账户系统]
        ACCOUNT -- 4. 返回动账结果 --> CORE
        CORE -- 5. 返回交易结果 --> WALLET
    end

    subgraph S3 [结算与计费]
        WALLET -- 6. 请求手续费计算 --> BILLING[计费中台]
        BILLING -- 7. 同步计费结果 --> SETTLE[清结算]
        SETTLE -- 8. 处理结算 --> ACCOUNT
    end

    subgraph S4 [数据聚合]
        ACCOUNT -- 9. 动账数据 --> STMT[对账单系统]
        SETTLE -- 10. 交易数据 --> STMT
        WALLET -- 11. 指令数据 --> STMT
        CORE -- 12. 交易数据 --> STMT
    end

    S1 --> S2 --> S3 --> S4
```

## 2.5 系统模块交互关系
模块间交互主要通过同步API调用和异步事件驱动两种方式，核心业务流由行业钱包系统串联。

```mermaid
flowchart TD
    GEN[三代系统] -- "开户/绑定/分账"指令 --> WALLET[行业钱包系统]

    WALLET -- 1. 生成并发送协议 --> E_SIGN[电子签章系统]
    E_SIGN -- 2. 调用认证 --> AUTH[认证系统]
    AUTH -- 3. 返回认证结果 --> E_SIGN
    E_SIGN -- 4. 回调签署结果 --> WALLET

    WALLET -- 5. 请求分账交易 --> CORE[业务核心]
    CORE -- 6. 调用动账 --> ACCOUNT[账户系统]
    ACCOUNT -- 7. 返回结果 --> CORE
    CORE -- 8. 返回结果 --> WALLET

    WALLET -- 9. 请求手续费计算 --> BILLING[计费中台]
    BILLING -- 10. 发布计费事件 --> SETTLE[清结算]

    SETTLE -- 11. 结算/退货扣款 --> ACCOUNT

    ACCOUNT -- 发布动账事件 --> STMT[对账单系统]
    SETTLE -- 发布交易事件 --> STMT
    WALLET -- 发布指令事件 --> STMT
    CORE -- 发布交易事件 --> STMT
```