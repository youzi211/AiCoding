## 2.1 系统结构
天财分账系统采用分层与模块化架构，以行业钱包系统为核心业务处理引擎，整合了账户、签约、认证、结算、计费等多个专业系统。系统整体遵循职责分离原则，通过清晰的接口定义和事件驱动机制进行协作，确保资金处理业务的合规性、安全性与可扩展性。

```mermaid
graph TB
    subgraph "商户端 (Client Layer)"
        APP[钱包APP/商服平台]
    end

    subgraph "业务应用层 (Application Layer)"
        GEN[三代系统]
        WALLET[行业钱包系统]
        SIGN[电子签约平台]
    end

    subgraph "核心服务层 (Core Service Layer)"
        ACCT[账户系统]
        AUTH[认证系统]
        SETTLE[清结算系统]
        FEE[计费中台]
        CORE[业务核心系统]
    end

    subgraph "数据与报表层 (Data & Reporting Layer)"
        STMT[对账单系统]
    end

    subgraph "外部依赖 (External Dependencies)"
        BANK[银行通道]
        FACE[第三方人脸识别]
        SMS[短信服务]
    end

    APP --> WALLET
    APP --> SIGN
    APP --> GEN
    APP --> STMT

    GEN --> ACCT
    WALLET --> ACCT
    WALLET --> GEN
    WALLET --> SIGN
    WALLET --> FEE
    WALLET --> SETTLE
    WALLET --> CORE

    SIGN --> AUTH
    SIGN --> SMS

    AUTH --> BANK
    AUTH --> FACE

    SETTLE --> FEE
    CORE --> SETTLE
    CORE --> FEE

    STMT --> CORE
    STMT --> SETTLE
    STMT --> WALLET
    STMT --> GEN
```

## 2.2 功能结构
系统功能围绕天财分账的核心业务流程（关系绑定、资金处理、账单管理）进行组织。主要功能模块包括商户与账户管理、签约认证、分账处理、结算计费以及账单服务。

```mermaid
graph TD
    Root[天财分账系统] --> FM1[商户与账户管理]
    Root --> FM2[签约与认证]
    Root --> FM3[分账处理]
    Root --> FM4[结算与计费]
    Root --> FM5[账单服务]

    FM1 --> SFM1_1[商户入驻与标识]
    FM1 --> SFM1_2[专用账户开户]
    FM1 --> SFM1_3[结算/手续费配置]

    FM2 --> SFM2_1[签约流程编排]
    FM2 --> SFM2_2[打款验证]
    FM2 --> SFM2_3[人脸验证]
    FM2 --> SFM2_4[关系绑定管理]

    FM3 --> SFM3_1[归集]
    FM3 --> SFM3_2[会员结算]
    FM3 --> SFM3_3[批量付款]
    FM3 --> SFM3_4[分账记录处理]

    FM4 --> SFM4_1[结算配置]
    FM4 --> SFM4_2[手续费计算]
    FM4 --> SFM4_3[账户冻结]
    FM4 --> SFM4_4[计费同步]

    FM5 --> SFM5_1[数据聚合]
    FM5 --> SFM5_2[账单生成]
    FM5 --> SFM5_3[账单查询下载]
```

## 2.3 网络拓扑图
TBD

## 2.4 数据流转
数据流转描述了关键业务数据在系统各模块间的传递路径，主要包括配置数据、验证数据、交易数据和结算数据。流转通过同步API调用和异步事件驱动两种方式完成。

```mermaid
flowchart LR
    subgraph S1[配置与开户]
        direction LR
        GEN_1[三代系统] -- 1. 请求开户 --> ACCT_1[账户系统]
        ACCT_1 -- 2. 返回账户ID --> GEN_1
        GEN_1 -- 3. 推送配置事件 --> WALLET_1[行业钱包系统]
    end

    subgraph S2[关系绑定]
        direction LR
        WALLET_2[行业钱包系统] -- 4. 发起签约 --> SIGN_1[电子签约平台]
        SIGN_1 -- 5. 发起验证 --> AUTH_1[认证系统]
        AUTH_1 -- 6. 验证结果回调 --> SIGN_1
        SIGN_1 -- 7. 签约结果通知 --> WALLET_2
    end

    subgraph S3[分账处理]
        direction LR
        WALLET_3[行业钱包系统] -- 8. 发起分账 --> CORE_1[业务核心系统]
        CORE_1 -- 9. 请求计费 --> FEE_1[计费中台]
        CORE_1 -- 10. 触发结算 --> SETTLE_1[清结算系统]
        CORE_1 -- 11. 发布交易事件 --> STMT_1[对账单系统]
    end

    S1 --> S2
    S2 --> S3
```

## 2.5 系统模块交互关系
模块间交互关系基于依赖方向（调用/被调用）和核心业务流程进行定义。行业钱包系统作为业务枢纽，与最多模块交互；账户系统和认证系统作为底层能力提供者，被上层模块依赖。

```mermaid
graph TD
    APP[钱包APP/商服平台]
    GEN[三代系统]
    WALLET[行业钱包系统]
    SIGN[电子签约平台]
    ACCT[账户系统]
    AUTH[认证系统]
    SETTLE[清结算系统]
    FEE[计费中台]
    CORE[业务核心系统]
    STMT[对账单系统]

    %% 核心业务调用流
    GEN -- 开户/配置 --> ACCT
    WALLET -- 关系绑定 --> SIGN
    SIGN -- 身份验证 --> AUTH
    WALLET -- 发起分账 --> CORE
    CORE -- 手续费计算 --> FEE
    CORE -- 触发结算 --> SETTLE

    %% 数据同步与查询
    WALLET -- 校验配置/状态 --> GEN
    WALLET -- 校验账户 --> ACCT
    SETTLE -- 同步计费 --> FEE
    STMT -- 消费交易事件 --> CORE
    STMT -- 消费结算事件 --> SETTLE
    STMT -- 消费业务数据 --> WALLET
    STMT -- 消费配置数据 --> GEN

    %% 前端交互
    APP -- 发起业务/查询 --> WALLET
    APP -- 签约跳转 --> SIGN
    APP -- 配置管理 --> GEN
    APP -- 账单查询 --> STMT
```