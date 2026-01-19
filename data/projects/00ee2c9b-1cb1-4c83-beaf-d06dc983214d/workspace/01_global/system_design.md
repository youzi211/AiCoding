# 天财分账系统设计文档

## 2.1 系统结构

天财分账系统采用分层、模块化的微服务架构，旨在为机构及商户提供安全、合规、高效的资金分账、归集与结算服务。系统整体遵循“前后端分离、业务与资金分离、流程与执行分离”的设计原则，通过清晰的职责边界和标准化的接口交互，确保系统的可扩展性、可维护性和高可用性。

### 系统架构图 (C4 Container 视图)

```mermaid
graph TB
    subgraph "外部系统与用户"
        User[用户/商户<br/>钱包APP/商服平台]
        ExtWallet[行业钱包系统<br/>资金流转引擎]
        ExtSettle[清结算系统<br/>资金处理核心]
        ExtESign[电子签约平台<br/>身份核验与协议]
        ExtFee[计费中台<br/>手续费计算]
        ExtAcquiring[支付核心/收单系统]
    end

    subgraph "天财分账业务系统 (核心业务层)"
        APP[钱包APP/商服平台<br/>前端门户]
        AuthSvc[认证系统<br/>身份与关系授权]
        AccountSvc[账户系统<br/>资金账户管理]
        ThirdGenSvc[三代系统<br/>业务流程编排]
        LedgerSvc[账务核心系统<br/>资金记账引擎]
        BizCoreSvc[业务核心<br/>交易记录中枢]
        StatementSvc[对账单系统<br/>账单生成与交付]
    end

    subgraph "基础设施与中间件"
        DB[(数据库集群)]
        MQ[(消息中间件)]
        Cache[(缓存)]
        FileStore[文件存储服务]
    end

    User --> APP
    APP --> ThirdGenSvc
    APP --> AuthSvc
    APP --> AccountSvc

    ThirdGenSvc --> AuthSvc
    ThirdGenSvc --> AccountSvc
    ThirdGenSvc --> LedgerSvc
    ThirdGenSvc --> ExtESign
    ThirdGenSvc --> ExtFee

    AuthSvc --> AccountSvc
    AuthSvc --> ExtESign
    AuthSvc --> ExtSettle
    AuthSvc --> ExtWallet

    LedgerSvc --> AccountSvc
    LedgerSvc --> ExtSettle
    LedgerSvc --> ExtFee

    BizCoreSvc --> ThirdGenSvc
    BizCoreSvc --> ExtWallet

    StatementSvc --> BizCoreSvc
    StatementSvc --> ExtSettle
    StatementSvc --> AccountSvc
    StatementSvc --> ThirdGenSvc
    StatementSvc --> FileStore

    ExtWallet --> ExtSettle
    ExtWallet --> ThirdGenSvc
    ExtWallet --> AccountSvc
    ExtWallet --> ExtFee
    ExtWallet --> BizCoreSvc
    ExtWallet --> MQ

    ExtSettle --> ExtWallet
    ExtSettle --> ThirdGenSvc
    ExtSettle --> AccountSvc
    ExtSettle --> ExtAcquiring
    ExtSettle --> ExtFee
    ExtSettle --> StatementSvc

    ExtESign --> AuthSvc
    ExtFee --> ThirdGenSvc
    ExtFee --> ExtWallet
    ExtFee --> StatementSvc

    %% 内部服务与基础设施连接
    AuthSvc --> DB
    AccountSvc --> DB
    ThirdGenSvc --> DB
    LedgerSvc --> DB
    BizCoreSvc --> DB
    StatementSvc --> DB
    APP --> DB

    ThirdGenSvc --> MQ
    APP --> MQ
```

**架构说明**:
1.  **用户交互层**: 钱包APP/商服平台作为统一前端，封装后端复杂流程，提供用户操作界面。
2.  **核心业务层**: 由多个职责明确的微服务构成，是分账业务逻辑的核心承载层。
    *   **认证系统 (AuthSvc)**: 业务安全入口，负责身份验证、关系绑定与授权。
    *   **账户系统 (AccountSvc)**: 资金流转基石，管理所有业务参与方的专用资金账户。
    *   **三代系统 (ThirdGenSvc)**: 业务流程编排中枢，整合开户、签约、关系绑定、指令发起等流程。
    *   **账务核心系统 (LedgerSvc)**: 资金处理引擎，负责记账、余额管理与交易状态跟踪。
    *   **业务核心 (BizCoreSvc)**: 交易记录中枢，持久化成功交易，为对账提供权威数据源。
    *   **对账单系统 (StatementSvc)**: 数据聚合与交付，生成多维度对账单。
3.  **外部依赖系统**: 与支付体系内其他核心平台紧密协作。
    *   **行业钱包系统**: 最终的资金划转执行者。
    *   **清结算系统**: 处理资金清算、结算及内部账户管理。
    *   **电子签约平台**: 提供合规的身份核验与电子协议服务。
    *   **计费中台**: 提供统一的手续费计算服务。
4.  **基础设施**: 数据库、消息队列、缓存、文件存储等支撑所有服务稳定运行。

## 2.2 功能结构

系统功能围绕“账户-认证-关系-指令-资金-对账”的核心链路进行模块化划分，各模块功能既相对独立又协同运作。

### 功能结构图

```mermaid
graph TD
    Root[天财分账系统] --> F1[用户与门户]
    Root --> F2[账户与认证管理]
    Root --> F3[业务关系与流程]
    Root --> F4[资金处理与记账]
    Root --> F5[计费与对账]
    Root --> F6[系统支撑]

    F1 --> F1.1[用户登录与权限]
    F1 --> F1.2[账户信息概览]
    F1 --> F1.3[业务关系引导与发起]
    F1 --> F1.4[分账指令操作]
    F1 --> F1.5[通知与消息]

    F2 --> F2.1[账户生命周期管理<br/>创建/查询/状态维护]
    F2 --> F2.2[身份认证与核验<br/>打款/人脸/协议]
    F2 --> F2.3[关系绑定与授权<br/>创建/查询/解除]

    F3 --> F3.1[商户信息管理<br/>总部/门店]
    F3 --> F3.2[业务关系管理<br/>归集/批量付款/会员结算]
    F3 --> F3.3[分账指令编排<br/>归集指令发起]
    F3 --> F3.4[业务流程状态跟踪]

    F4 --> F4.1[分账交易执行<br/>创建/冲正]
    F4 --> F4.2[账户余额管理<br/>查询/冻结]
    F4 --> F4.3[资金记账与流水<br/>记账/流水记录]
    F4 --> F4.4[资金划转驱动<br/>调用钱包/清结算]

    F5 --> F5.1[手续费计算<br/>规则管理/试算/实算]
    F5 --> F5.2[业务记录聚合<br/>交易流水持久化]
    F5 --> F5.3[对账单服务<br/>生成/查询/下载/推送]

    F6 --> F6.1[电子签约集成<br/>人脸核验/协议签署]
    F6 --> F6.2[清结算集成<br/>内部账户/结算执行/资金划转]
    F6 --> F6.3[消息与事件驱动]
    F6 --> F6.4[数据存储与缓存]
```

**功能模块说明**:
*   **用户与门户 (F1)**: 面向用户的前端功能集合，提供直观的业务操作界面和引导。
*   **账户与认证管理 (F2)**: 系统安全与合规的基础，确保参与方身份真实、关系有效。
*   **业务关系与流程 (F3)**: 定义和执行业务规则的核心，管理商户、关系及指令的生命周期。
*   **资金处理与记账 (F4)**: 系统最核心的资金操作层，确保每笔资金变动准确、可追溯。
*   **计费与对账 (F5)**: 业务运营支撑，准确计算成本并提供清晰的账务数据。
*   **系统支撑 (F6)**: 集成外部能力和提供基础设施，保障系统间稳定协作。

## 2.3 网络拓扑图

系统部署在私有云或金融级云平台内，网络拓扑遵循金融系统安全规范，划分不同安全区域。

```mermaid
graph TB
    subgraph "互联网区 (DMZ)"
        Client[用户浏览器/移动APP]
        F5[F5/负载均衡器]
        WAF[Web应用防火墙]
    end

    subgraph "应用服务区"
        subgraph "前端服务集群"
            APP1[钱包APP服务实例1]
            APP2[钱包APP服务实例2]
        end
        subgraph "业务微服务集群"
            Svc1[认证系统]
            Svc2[账户系统]
            Svc3[三代系统]
            Svc4[账务核心]
            Svc5[业务核心]
            Svc6[对账单系统]
        end
        LB[内部负载均衡/API Gateway]
    end

    subgraph "数据区"
        subgraph "数据库集群"
            PrimaryDB[主数据库]
            ReadReplica[只读副本]
        end
        subgraph "缓存与消息集群"
            Redis[Redis集群]
            Kafka[Kafka集群]
        end
        NAS[网络文件存储]
    end

    subgraph "支付平台区 (内部网络)"
        Wallet[行业钱包系统]
        Settle[清结算系统]
        ESign[电子签约平台]
        Fee[计费中台]
    end

    Client --> WAF
    WAF --> F5
    F5 --> APP1
    F5 --> APP2

    APP1 --> LB
    APP2 --> LB
    LB --> Svc1
    LB --> Svc2
    LB --> Svc3
    LB --> Svc4
    LB --> Svc5
    LB --> Svc6

    Svc1 --> PrimaryDB
    Svc2 --> PrimaryDB
    Svc3 --> PrimaryDB
    Svc4 --> PrimaryDB
    Svc5 --> PrimaryDB
    Svc6 --> PrimaryDB
    Svc5 --> ReadReplica
    Svc6 --> ReadReplica

    Svc1 --> Redis
    Svc2 --> Redis
    Svc3 --> Redis
    Svc4 --> Redis

    Svc1 --> Kafka
    Svc3 --> Kafka
    Svc5 --> Kafka
    Svc6 --> Kafka
    APP1 --> Kafka

    Svc6 --> NAS
    ESign --> NAS

    Svc1 -.->|HTTPS/内部API| ESign
    Svc3 -.->|HTTPS/内部API| ESign
    Svc3 -.->|HTTPS/内部API| Fee
    Svc4 -.->|HTTPS/内部API| Fee

    Svc2 -.->|HTTPS/内部API| Settle
    Svc3 -.->|HTTPS/内部API| Settle
    Svc4 -.->|HTTPS/内部API| Settle
    Svc6 -.->|HTTPS/内部API| Settle

    Svc3 -.->|HTTPS/内部API| Wallet
    Svc4 -.->|HTTPS/内部API| Wallet
    Svc5 -.->|HTTPS/内部API| Wallet

    Wallet -.->|HTTPS/内部API| Settle
    Settle -.->|HTTPS/内部API| Wallet
```

**拓扑说明**:
1.  **安全隔离**: 通过防火墙划分互联网区、应用服务区、数据区和支付平台区，实施层层防护。
2.  **高可用**: 关键服务（前端、微服务、数据库、缓存、消息队列）均采用集群化部署，消除单点故障。
3.  **负载均衡**: 入口层使用F5硬件负载均衡，内部服务间通过软件负载均衡或API网关进行路由。
4.  **访问控制**: 应用服务区微服务通过内部网络以HTTPS协议调用支付平台区的系统，确保通信安全。
5.  **数据存储**: 核心业务数据使用主从数据库，读写分离提升性能。文件、缓存、消息队列使用专用集群。

## 2.4 数据流转

数据在系统中的流转主要围绕“业务指令驱动资金变动，变动结果形成业务记录，记录聚合生成对账单”这一主线进行。

### 核心业务数据流图 (以资金归集为例)

```mermaid
sequenceDiagram
    participant U as 用户(APP)
    participant T as 三代系统
    participant A as 认证系统
    participant E as 电子签约平台
    participant L as 账务核心系统
    participant W as 行业钱包系统
    participant S as 清结算系统
    participant B as 业务核心
    participant St as 对账单系统

    Note over U,St: 阶段一：关系建立与认证
    U->>T: 1. 发起创建归集关系请求
    T->>A: 2. 调用创建关系绑定
    A->>E: 3. 发起电子协议签署
    E-->>U: 4. 引导用户完成签约(人脸/协议)
    E->>A: 5. 回调通知签约结果
    A->>T: 6. 通知关系绑定结果
    T->>U: 7. 返回关系建立成功

    Note over U,St: 阶段二：指令发起与资金处理
    U->>T: 8. 发起归集指令
    T->>L: 9. 调用创建分账交易
    L->>L: 10. 记账（冻结付款方余额等）
    L->>W: 11. 调用执行天财分账
    W->>S: 12. 调用内部账户划转
    S->>S: 13. 清算记账
    S-->>W: 14. 返回划转结果
    W-->>L: 15. 返回分账结果
    L->>L: 16. 更新交易状态并解冻/扣账
    L-->>T: 17. 返回交易执行结果
    T-->>U: 18. 通知指令执行完成

    Note over U,St: 阶段三：记录持久化与对账
    W->>B: 19. 异步通知交易成功
    B->>B: 20. 持久化业务记录
    St->>B: 21. 定时/触发拉取业务记录
    St->>S: 22. 拉取清结算流水
    St->>St: 23. 聚合数据，生成对账单
    St->>U/外部: 24. 推送/提供对账单下载
```

**数据流关键路径说明**:
1.  **业务配置流**: 用户通过APP发起，经由三代系统、认证系统、电子签约平台，完成商户、账户、关系的创建与认证。数据最终落地到各系统的数据库。
2.  **资金指令流**: 指令从APP发起，经三代系统路由至账务核心。账务核心完成本地记账后，驱动行业钱包和清结算系统完成实际的资金跨账户划转。资金状态在账务核心、钱包、清结算等多个系统中同步更新。
3.  **数据记录流**: 成功的资金交易由行业钱包系统异步通知业务核心进行持久化，形成权威业务流水。对账单系统定时从业务核心和清结算系统拉取数据，进行聚合、加工，生成最终的对账单。

## 2.5 系统模块交互关系

各模块通过定义良好的API进行同步或异步（消息）交互，共同完成复杂的业务流程。下图概括了核心模块间的主要调用与依赖关系。

### 模块交互依赖图

```mermaid
graph LR
    subgraph "外部依赖系统"
        direction LR
        ExtESign[电子签约平台]
        ExtWallet[行业钱包系统]
        ExtSettle[清结算系统]
        ExtFee[计费中台]
    end

    subgraph "天财分账核心模块"
        APP[钱包APP/商服平台]
        Auth[认证系统]
        Account[账户系统]
        ThirdGen[三代系统]
        Ledger[账务核心系统]
        BizCore[业务核心]
        Statement[对账单系统]
    end

    %% APP 交互
    APP -- “创建关系/指令” --> ThirdGen
    APP -- “查询账户/发起认证” --> Account
    APP -- “查询关系状态” --> Auth

    %% 三代系统 核心编排者
    ThirdGen -- “创建/查询关系” --> Auth
    ThirdGen -- “创建/查询账户” --> Account
    ThirdGen -- “发起分账交易” --> Ledger
    ThirdGen -- “发起签约流程” --> ExtESign
    ThirdGen -- “试算/计算手续费” --> ExtFee

    %% 认证系统 安全前置
    Auth -- “验证账户信息” --> Account
    Auth -- “发起/查询签约” --> ExtESign
    Auth -- “触发打款认证” --> ExtSettle
    Auth -- “验证账户权限” --> ExtWallet

    %% 账务核心 资金引擎
    Ledger -- “管理账户余额” --> Account
    Ledger -- “驱动资金划转” --> ExtWallet
    Ledger -- “涉及结算记账” --> ExtSettle
    Ledger -- “计算实收手续费” --> ExtFee

    %% 业务核心 记录中枢
    BizCore -- “监听交易成功事件” --> ExtWallet
    BizCore -- “提供业务流水” --> Statement

    %% 对账单系统 数据聚合
    Statement -- “拉取核心流水” --> BizCore
    Statement -- “拉取结算流水” --> ExtSettle
    Statement -- “获取账户信息” --> Account
    Statement -- “获取商户关系” --> ThirdGen

    %% 行业钱包与清结算 资金执行双核
    ExtWallet -- “校验关系/账户” --> Auth
    ExtWallet -- “执行划转指令” --> ExtSettle
    ExtWallet -- “计算手续费” --> ExtFee
    ExtWallet -- “通知交易结果” --> BizCore

    ExtSettle -- “管理内部账户” --> Account
    ExtSettle -- “处理结算指令” --> ThirdGen
    ExtSettle -- “提供结算数据” --> Statement
```

**交互关系总结**:
*   **三代系统** 是业务流程的**总指挥**，串联了认证、账户、账务、外部签约和计费，是交互最广泛的模块。
*   **认证系统** 和 **账户系统** 是业务的**基石**，几乎所有涉及资金和关系的操作都需要与之交互。
*   **账务核心系统** 是**资金操作**的发起点，连接内部记账与外部资金执行系统（钱包、清结算）。
*   **行业钱包系统** 与 **清结算系统** 是**资金执行**的双核心，负责最终的资金流转和清算，并与其他模块有广泛交互。
*   **业务核心** 与 **对账单系统** 处于业务流程的**下游**，负责记录聚合与输出，强依赖上游的业务和资金模块。
*   **钱包APP/商服平台** 是业务的**起点**和**界面**，主要与三代系统交互，间接驱动整个系统。