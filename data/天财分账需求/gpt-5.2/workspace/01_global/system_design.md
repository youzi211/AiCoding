# 天财分账支付平台系统级设计文档

## 2.1 系统结构

本系统采用分层、模块化的微服务架构，旨在为“天财商龙”业务场景提供安全、合规、高效的账户管理与资金分账服务。整体架构遵循“高内聚、低耦合”原则，通过清晰的职责边界和标准化的API接口进行协作。

### 系统架构图 (C4 Container Diagram)

```mermaid
graph TB
    subgraph "外部系统/用户"
        ExtUser[商户/接收方<br/>钱包APP/商服平台]
        ExtSystem_TC[天财商龙业务系统]
        ExtSystem_3rd[第三方服务<br/>人脸核验/短信/文件存储]
    end

    subgraph "支付平台 - 业务接入与编排层"
        Wallet[行业钱包系统<br/>业务逻辑中枢与流程编排]
        Gen3[三代系统<br/>业务接入、配置与关系管理]
    end

    subgraph "支付平台 - 核心业务处理层"
        BizCore[业务核心<br/>交易处理中枢]
        Account[账户系统<br/>专用账户体系管理]
        Settlement[清结算系统<br/>资金清算与结算]
        Billing[计费中台<br/>实时手续费计算]
    end

    subgraph "支付平台 - 支撑与合规服务层"
        Auth[认证系统<br/>身份验证服务]
        ESign[电子签约平台<br/>合规授权与签约]
        Statement[对账单系统<br/>机构级账单服务]
    end

    subgraph "支付平台 - 基础设施"
        DB[(核心数据库集群)]
        MQ[(消息中间件)]
        Cache[(缓存)]
    end

    ExtUser --> Wallet
    ExtUser --> Account
    ExtSystem_TC --> Gen3
    Gen3 --> Wallet

    Wallet --> BizCore
    Wallet --> Account
    Wallet --> ESign
    Wallet --> Billing
    Wallet --> Statement

    BizCore --> Settlement
    BizCore --> Billing
    BizCore --> Account

    Settlement --> Account
    Settlement --> Billing

    Auth --> ESign
    Auth --> Account
    ESign --> Auth

    Statement --> Account
    Statement --> Settlement
    Statement --> BizCore
    Statement --> Wallet
    Statement --> Gen3

    Billing --> Gen3

    ExtSystem_3rd --> Auth
    ExtSystem_3rd --> ESign

    Wallet -.-> MQ
    BizCore -.-> MQ
    Settlement -.-> MQ
    Statement -.-> MQ

    Account -.-> DB
    Auth -.-> DB
    Billing -.-> DB
    BizCore -.-> DB
    Gen3 -.-> DB
    Settlement -.-> DB
    ESign -.-> DB
    Wallet -.-> DB
    Statement -.-> DB

    Wallet -.-> Cache
    Statement -.-> Cache
```

**架构说明**:
1.  **业务接入与编排层**: 作为对外业务入口，`三代系统`负责与外部“天财商龙”业务系统对接，进行业务路由和配置管理；`行业钱包系统`作为内部流程编排中枢，协调各下游服务完成业务闭环。
2.  **核心业务处理层**: 包含交易处理(`业务核心`)、账户管理(`账户系统`)、资金划转(`清结算系统`)和费用计算(`计费中台`)等核心支付能力，是系统的心脏。
3.  **支撑与合规服务层**: 提供身份认证(`认证系统`)、电子签约(`电子签约平台`)、账单服务(`对账单系统`)等支撑性、合规性功能，保障业务安全、合规、可审计。
4.  **基础设施**: 统一的数据库、消息队列和缓存服务，为各微服务提供数据持久化、异步解耦和性能加速能力。

## 2.2 功能结构

系统功能围绕“天财专用账户”的生命周期和“天财分账”交易流程进行组织，主要分为五大功能域。

### 功能结构图

```mermaid
graph TD
    A[天财分账支付平台] --> B[账户管理功能域]
    A --> C[交易处理功能域]
    A --> D[清结算功能域]
    A --> E[合规与风控功能域]
    A --> F[运营支撑功能域]

    B --> B1[账户开户/升级]
    B --> B2[账户信息查询]
    B --> B3[账户状态管理<br/>冻结/解冻]
    B --> B4[账户动账明细查询]

    C --> C1[分账交易指令接收]
    C --> C2[交易路由与处理]
    C --> C3[手续费实时计算]
    C --> C4[交易结果查询]

    D --> D1[账户间资金分账]
    D --> D2[主动结算触发]
    D --> D3[日终清算汇总]
    D --> D4[结算状态跟踪]

    E --> E1[身份认证<br/>打款/人脸]
    E --> E2[电子协议签署]
    E --> E3[资金关系绑定授权]
    E --> E4[操作审计与证据链]

    F --> F1[机构层级对账单]
    F --> F2[计费规则管理]
    F --> F3[商户关系映射管理]
    F --> F4[客户端功能管控]
```

**功能域说明**:
- **账户管理功能域**: 由`账户系统`和`三代系统`共同实现，负责天财专用账户的创建、维护、查询和资金明细展示。
- **交易处理功能域**: 以`业务核心`和`行业钱包系统`为核心，完成从天财发起的资金分账交易的全流程处理。
- **清结算功能域**: 由`清结算系统`主导，处理账户间的实时分账、商户资金的主动结算以及日终清算。
- **合规与风控功能域**: 由`认证系统`和`电子签约平台`支撑，确保业务参与方身份真实、授权有效，并留存完整合规证据。
- **运营支撑功能域**: 包括`对账单系统`的账单服务、`计费中台`的规则管理、`三代系统`的关系管理以及`钱包APP`的商户端功能管控。

## 2.3 网络拓扑图

系统部署在私有云或金融云环境，采用分区隔离、多层防护的网络架构，确保安全与合规。

```mermaid
graph TB
    subgraph "互联网区 (DMZ)"
        direction LR
        ELB_Internet[互联网接入负载均衡]
        WAF[Web应用防火墙]
    end

    subgraph "业务服务区 (Trust Zone)"
        direction TB
        ELB_Internal[内部负载均衡]
        subgraph "微服务集群"
            Wallet_Instances[行业钱包系统实例]
            Gen3_Instances[三代系统实例]
            BizCore_Instances[业务核心实例]
            Account_Instances[账户系统实例]
            Other_Instances[...其他微服务实例]
        end
        MQ_Cluster[消息中间件集群]
        Cache_Cluster[缓存集群]
    end

    subgraph "数据区 (Secure Zone)"
        DB_Master[(主数据库)]
        DB_ReadReplica[(只读副本)]
        DB_Backup[(备份存储)]
    end

    subgraph "外部服务区"
        Ext_TC[天财商龙系统]
        Ext_3rd_SMS[短信网关]
        Ext_3rd_Face[人脸核验服务]
        Ext_FileStore[文件存储服务]
    end

    Internet[商户/用户] --> WAF
    WAF --> ELB_Internet
    ELB_Internet --> Wallet_Instances
    ELB_Internet --> Gen3_Instances

    Ext_TC --> ELB_Internal
    ELB_Internal --> Gen3_Instances

    Wallet_Instances --> ELB_Internal
    Gen3_Instances --> ELB_Internal
    ELB_Internal --> BizCore_Instances
    ELB_Internal --> Account_Instances
    ELB_Internal --> Other_Instances

    BizCore_Instances --> MQ_Cluster
    Account_Instances --> MQ_Cluster

    Wallet_Instances --> Cache_Cluster
    Statement_Instances[对账单系统实例] --> Cache_Cluster

    BizCore_Instances --> DB_Master
    Account_Instances --> DB_Master
    Other_Instances --> DB_Master
    BizCore_Instances --> DB_ReadReplica
    Account_Instances --> DB_ReadReplica

    DB_Master --> DB_Backup

    Wallet_Instances --> Ext_3rd_SMS
    Auth_Instances[认证系统实例] --> Ext_3rd_Face
    ESign_Instances[电子签约平台实例] --> Ext_FileStore
```

**网络拓扑说明**:
1.  **分区隔离**: 严格划分互联网区(DMZ)、业务服务区、数据区和外部服务区，通过防火墙策略控制访问。
2.  **入口防护**: 互联网流量通过WAF和负载均衡进入，仅暴露`行业钱包系统`(面向商户APP)和`三代系统`(面向天财商龙)的接口。
3.  **内部通信**: 微服务间通过内部负载均衡和私有域名进行RPC调用，关键异步通信通过消息中间件解耦。
4.  **数据访问**: 业务服务区通过专线或安全网关访问数据区的主备数据库。写操作指向主库，部分读操作可分流至只读副本。
5.  **外部集成**: 与第三方服务（短信、人脸、文件存储）的通信通过指定的出口网关进行，并配置相应的IP白名单和流量监控。

## 2.4 数据流转

系统数据流转主要围绕“账户开户”、“关系绑定”、“分账交易”和“账单生成”四个核心业务流程。

### 核心业务流程数据流图

```mermaid
flowchart TD
    subgraph A[业务流程：天财账户开户与关系绑定]
        direction LR
        A1[天财商龙发起请求] --> A2[三代系统接收并路由]
        A2 --> A3[行业钱包系统校验并编排]
        A3 --> A4[账户系统创建专用账户]
        A3 --> A5[电子签约平台发起认证签约]
        A5 --> A6[认证系统执行打款/人脸验证]
        A6 --> A7[电子签约平台完成协议签署]
        A7 --> A8[行业钱包系统确认关系绑定]
        A8 --> A9[三代系统更新绑定状态]
    end

    subgraph B[业务流程：天财分账交易]
        direction LR
        B1[天财商龙发起分账指令] --> B2[行业钱包系统接收并校验]
        B2 --> B3[业务核心处理交易逻辑]
        B3 --> B4[计费中台计算手续费]
        B4 --> B5[清结算系统执行资金划拨]
        B5 --> B6[账户系统更新余额并记录明细]
        B6 --> B7[业务核心更新交易状态]
        B7 --> B8[行业钱包系统返回最终结果]
    end

    subgraph C[数据流程：日终对账单生成]
        direction TB
        C1[对账单系统触发日终任务] --> C2[拉取账户动账明细]
        C2 --> Account
        C1 --> C3[拉取分账交易明细]
        C3 --> BizCore
        C1 --> C4[拉取结算汇总数据]
        C4 --> Settlement
        C1 --> C5[拉取商户与关系映射]
        C5 --> Wallet
        C5 --> Gen3
        C6[对账单系统加工与聚合数据] --> C7[生成机构层级账单文件]
        C7 --> C8[推送或供下载]
    end

    A --> B
    B --> C
```

**数据流转关键点**:
1.  **开户与绑定**: 数据从外部业务系统流入，经过多系统校验、账户创建、合规认证，最终形成账户和绑定关系数据，存储于`账户系统`、`行业钱包系统`和`三代系统`的相关表中。
2.  **分账交易**: 交易指令触发资金和状态的连环变更。`业务核心`记录交易主流程，`清结算系统`记录资金划拨订单，`账户系统`记录最底层的余额和明细变动，`计费中台`记录费用流水。各模块通过事务消息确保最终一致性。
3.  **账单生成**: `对账单系统`作为数据消费者，在日终或定时从多个上游系统（`账户系统`、`业务核心`、`清结算系统`等）拉取加工后的明细数据，进行聚合后生成面向天财机构的统一视图账单。上游系统需保证数据的准确性和及时推送。

## 2.5 系统模块交互关系

以下模块交互图详细描述了各微服务在关键场景下的调用依赖关系。

### 模块交互依赖图

```mermaid
flowchart LR
    subgraph External[外部依赖]
        三代系统
        账务核心系统
        短信网关
        人脸核验服务
        文件存储服务
    end

    行业钱包系统 --> 三代系统
    行业钱包系统 --> 账户系统
    行业钱包系统 --> 电子签约平台
    行业钱包系统 --> 业务核心
    行业钱包系统 --> 计费中台
    行业钱包系统 --> 对账单系统

    三代系统 --> 行业钱包系统
    三代系统 --> 计费中台
    三代系统 --> 清结算系统
    三代系统 --> 对账单系统
    三代系统 --> 账户系统

    业务核心 --> 账务核心系统
    业务核心 --> 计费中台
    业务核心 --> 对账单系统

    账户系统 --> 账务核心系统
    账户系统 --> 对账单系统
    账户系统 --> 清结算系统
    账户系统 --> 三代系统

    清结算系统 --> 行业钱包系统
    清结算系统 --> 账户系统
    清结算系统 --> 计费中台
    清结算系统 --> 业务核心

    计费中台 --> 三代系统
    计费中台 --> 行业钱包系统
    计费中台 --> 清结算系统
    计费中台 --> 对账单系统
    计费中台 --> 账户系统

    认证系统 --> 电子签约平台
    认证系统 --> 账务核心系统
    认证系统 --> 人脸核验服务
    认证系统 --> 行业钱包系统

    电子签约平台 --> 行业钱包系统
    电子签约平台 --> 认证系统
    电子签约平台 --> 短信网关
    电子签约平台 --> 文件存储服务

    对账单系统 --> 账户系统
    对账单系统 --> 清结算系统
    对账单系统 --> 业务核心
    对账单系统 --> 行业钱包系统
    对账单系统 --> 三代系统

    钱包APP/商服平台 --> 账户系统
    钱包APP/商服平台 --> 清结算系统
    钱包APP/商服平台 --> 行业钱包系统
    钱包APP/商服平台 --> 三代系统
    钱包APP/商服平台 --> 认证系统
```

**核心交互关系分析**:

1.  **中枢协调者 - 行业钱包系统**: 是业务流程的主要驱动者，依赖最多下游系统（账户、签约、业务核心、计费），是连接业务入口（三代）与内部核心服务的枢纽。
2.  **核心服务三角 - 业务核心、清结算、账户系统**: 构成资金处理的核心闭环。`业务核心`驱动交易，`清结算`执行资金操作，`账户系统`记录资金变动，三者联系紧密。
3.  **配置与数据源 - 三代系统**: 作为业务规则的源头（如计费规则、商户关系），被`计费中台`、`行业钱包`、`对账单系统`等多个模块依赖。
4.  **合规双支柱 - 认证系统 & 电子签约平台**: 两者相互调用，共同完成用户身份核实与法律授权，为`行业钱包系统`发起的绑定、付款等关键操作提供安全保障。
5.  **数据消费端 - 对账单系统**: 是主要的数据集成和输出端，依赖几乎所有产生资金和交易数据的核心模块，以提供统一的账单视图。
6.  **客户端 - 钱包APP/商服平台**: 面向最终用户，其功能实现依赖于后端的账户、交易、关系管理等核心服务。

此设计确保了职责清晰，同时通过`行业钱包系统`的有效编排和标准化API，降低了模块间的网状耦合度。