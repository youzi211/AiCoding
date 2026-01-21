## 2.1 系统结构
天财分账系统是一个基于微服务架构的业务系统，旨在为天财商龙商户提供门店分账、会员结算、批量付款等资金处理能力。系统以**行业钱包系统**为核心业务逻辑处理单元，向上对接**三代系统**以获取商户与账户配置，向下依赖**账户系统**、**清结算系统**、**计费中台**等基础服务完成账户管理、资金结算和费用计算。**电子签章系统**与**认证系统**为业务流程中的关系绑定与授权提供支持。**业务核心**作为统一的资金交易入口，负责将分账指令路由至底层支付或清结算通道执行。**对账单系统**负责聚合各模块的业务数据，生成机构层级的各类账单。**钱包app/商服平台**作为前端应用，为商户提供业务操作界面。

```mermaid
graph TB
    subgraph "前端应用层"
        FE[钱包app/商服平台]
    end

    subgraph "业务服务层"
        WALLET[行业钱包系统]
        GEN3[三代系统]
        BIZ_CORE[业务核心]
        E_SIGN[电子签章系统]
    end

    subgraph "基础服务层"
        ACCOUNT[账户系统]
        SETTLE[清结算系统]
        FEE[计费中台]
        AUTH[认证系统]
    end

    subgraph "数据与报表层"
        STATEMENT[对账单系统]
    end

    subgraph "外部依赖"
        PAYMENT[支付系统]
    end

    FE --> WALLET
    FE --> GEN3
    FE --> E_SIGN
    FE --> STATEMENT

    GEN3 --> WALLET
    WALLET --> GEN3
    WALLET --> ACCOUNT
    WALLET --> E_SIGN
    WALLET --> FEE
    WALLET --> BIZ_CORE
    WALLET --> SETTLE

    E_SIGN --> AUTH

    BIZ_CORE --> PAYMENT
    BIZ_CORE --> SETTLE

    STATEMENT --> BIZ_CORE
    STATEMENT --> SETTLE
    STATEMENT --> WALLET
    STATEMENT --> ACCOUNT
    STATEMENT --> GEN3
```

## 2.2 功能结构
系统功能围绕天财分账的核心业务流程进行组织，主要包括账户与配置管理、关系绑定与认证、分账交易处理、以及账单与报表四大功能域。

```mermaid
graph TD
    A[天财分账系统] --> B[账户与配置管理]
    A --> C[关系绑定与认证]
    A --> D[分账交易处理]
    A --> E[账单与报表]

    B --> B1[天财专用账户开通]
    B --> B2[结算模式配置]
    B --> B3[账户状态与能力管理]

    C --> C1[分账关系绑定]
    C --> C2[开通付款签约]
    C --> C3[打款/人脸认证]

    D --> D1[归集]
    D --> D2[批量付款]
    D --> D3[会员结算]
    D --> D4[手续费计算]
    D --> D5[资金划转执行]

    E --> E1[分账账单]
    E --> E2[提款账单]
    E --> E3[收单账单]
    E --> E4[结算账单]
```

## 2.3 网络拓扑图
TBD

## 2.4 数据流转
数据流转描述了天财分账业务中关键流程的数据在系统各模块间的传递路径。核心流程包括：账户开通、关系绑定、分账交易执行。

```mermaid
flowchart TD
    subgraph "账户开通流程"
        A1[三代系统: 发起开户] --> A2[行业钱包系统: 校验并转发]
        A2 --> A3[账户系统: 创建并标记账户]
        A3 -- 账户ID --> A2
        A2 -- 开户结果 --> A1
    end

    subgraph "关系绑定流程"
        B1[三代系统/钱包app: 发起绑定] --> B2[行业钱包系统: 发起签约]
        B2 --> B3[电子签章系统: 生成协议并引导认证]
        B3 --> B4[认证系统: 执行打款/人脸验证]
        B4 -- 认证结果 --> B3
        B3 -- 签署完成通知 --> B2
        B2 -- 绑定状态更新 --> B1
    end

    subgraph "分账交易流程"
        C1[钱包app: 发起分账指令] --> C2[行业钱包系统: 处理请求]
        C2 --> C3[计费中台: 计算手续费]
        C3 -- 手续费金额 --> C2
        C2 --> C4[业务核心: 执行资金划转]
        C4 --> C5[支付/清结算系统: 完成资金处理]
        C5 -- 交易结果 --> C4
        C4 -- 执行结果 --> C2
        C2 -- 指令结果 --> C1
        C2 -- 交易事件 --> C6[对账单系统: 记录明细]
    end
```

## 2.5 系统模块交互关系
模块交互关系详细描述了各系统组件之间的接口调用与数据依赖，是系统集成与联调的基础。

```mermaid
flowchart LR
    GEN3[三代系统] -- "1. 开户/配置/绑定" --> WALLET[行业钱包系统]
    WALLET -- "2. 回调通知" --> GEN3

    WALLET -- "3. 创建/管理账户" --> ACCOUNT[账户系统]
    ACCOUNT -- "4. 账户信息" --> WALLET

    WALLET -- "5. 发起签约认证" --> E_SIGN[电子签章系统]
    E_SIGN -- "6. 认证结果/签署状态" --> WALLET

    E_SIGN -- "7. 发起验证" --> AUTH[认证系统]
    AUTH -- "8. 验证结果" --> E_SIGN

    WALLET -- "9. 计算手续费" --> FEE[计费中台]
    FEE -- "10. 费用结果" --> WALLET

    WALLET -- "11. 执行资金划转" --> BIZ_CORE[业务核心]
    BIZ_CORE -- "12. 划转结果" --> WALLET

    BIZ_CORE -- "13. 调用支付通道" --> PAYMENT[支付系统]
    BIZ_CORE -- "14. 调用结算通道" --> SETTLE[清结算系统]

    WALLET -- "15. 查询/冻结账户" --> SETTLE
    GEN3 -- "16. 配置结算账户" --> SETTLE

    STATEMENT[对账单系统] -- "17. 监听/拉取数据" --> BIZ_CORE
    STATEMENT -- "18. 监听/拉取数据" --> SETTLE
    STATEMENT -- "19. 监听/拉取数据" --> WALLET
    STATEMENT -- "20. 监听/拉取数据" --> ACCOUNT
    STATEMENT -- "21. 监听/拉取数据" --> GEN3

    FE[钱包app/商服平台] -- "22. 业务操作/查询" --> WALLET
    FE -- "23. 配置查询/操作" --> GEN3
    FE -- "24. 签约引导" --> E_SIGN
    FE -- "25. 账单查询" --> STATEMENT
```