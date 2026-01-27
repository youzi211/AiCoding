## 2.1 系统结构
本系统为面向“天财”合作方的分账业务平台，采用分布式微服务架构。系统以“三代”作为业务入口与核心协调方，通过“行业钱包”处理核心分账逻辑，并依赖“账户系统”、“清结算”、“电子签约平台”等专业系统完成资金、账户、认证等专项服务。各模块职责清晰，通过API进行松耦合交互，共同支撑归集、会员结算、批量付款三大业务场景。

```mermaid
graph TB
    subgraph "外部系统/合作方"
        TC[天财/开放平台]
        Bank[银行通道]
        Face[人脸识别服务]
    end

    subgraph "业务接入与协调层"
        GEN[三代系统]
        BC[业务核心]
        TX[交易系统]
    end

    subgraph "核心业务处理层"
        WALLET[行业钱包]
        AUTH[认证系统]
        PAYOUT[代付系统]
        RISK[风控]
    end

    subgraph "专业服务层"
        ACC[账户系统]
        SETTLE[清结算]
        SIGN[电子签约平台]
        FEE[计费中台]
        LEDGER[账务核心]
    end

    subgraph "数据与支撑层"
        STMT[对账单系统]
        USER[用户中心]
        MSG[消息中心]
    end

    TC --> GEN
    TC --> BC
    BC --> TX
    GEN --> WALLET
    TX --> WALLET
    WALLET --> ACC
    WALLET --> SETTLE
    WALLET --> SIGN
    AUTH --> SIGN
    AUTH --> WALLET
    PAYOUT --> ACC
    PAYOUT --> SIGN
    RISK --> BC
    RISK --> WALLET
    SETTLE --> FEE
    SIGN --> Bank
    SIGN --> Face
    SIGN --> FEE
    LEDGER --> ACC
    LEDGER --> STMT
    USER --> GEN
    USER --> SIGN
    STMT --> ACC
    STMT --> SETTLE
```

## 2.2 功能结构
系统功能围绕天财分账业务的核心流程展开，划分为商户与账户管理、分账交易处理、资金结算、签约认证、风控对账五大功能域。

```mermaid
graph TD
    Root[天财分账系统]

    subgraph F1[商户与账户管理]
        F1A[商户入网审核]
        F1B[机构号管理]
        F1C[天财账户开户]
        F1D[账户状态管理]
    end

    subgraph F2[分账交易处理]
        F2A[资金归集]
        F2B[会员结算]
        F2C[批量付款]
        F2D[分账指令执行]
        F2E[交易冲正]
    end

    subgraph F3[资金结算]
        F3A[主动/被动结算触发]
        F3B[资金清算]
        F3C[手续费清分]
        F3D[资金划转执行]
    end

    subgraph F4[签约认证]
        F4A[关系绑定]
        F4B[开通付款]
        F4C[打款验证]
        F4D[人脸验证]
        F4E[协议签署]
    end

    subgraph F5[风控与对账]
        F5A[交易风险检查]
        F5B[签约风险检查]
        F5C[人工审核]
        F5D[账单生成]
        F5E[勾稽校验]
    end

    Root --> F1
    Root --> F2
    Root --> F3
    Root --> F4
    Root --> F5

    F1C --> F2D
    F4A --> F2A
    F4A --> F2B
    F4B --> F2C
    F3D --> F2D
    F5A --> F2D
    F5B --> F4A
    F5B --> F4B
```

## 2.3 网络拓扑图
TBD

## 2.4 数据流转
数据流转以一笔“会员结算”场景的分账交易为例，描述从交易发起到资金划转完成的关键数据流。

```mermaid
flowchart LR
    subgraph S1[请求发起]
        A1[天财] -- 分账请求<br>（含场景、付方、收方、金额） --> A2[业务核心]
    end

    subgraph S2[校验与预处理]
        A2 -- 校验账户、关系、幂等 --> A3[行业钱包]
        A3 -- 查询账户状态与关系 --> A4[账户系统]
        A3 -- 查询关系绑定状态 --> A5[用户中心]
        A2 -- 交易风险检查 --> A6[风控]
    end

    subgraph S3[资金处理]
        A3 -- 分账指令 --> A7[交易系统]
        A7 -- 调用资金划转 --> A4
        A7 -- 计算手续费 --> A8[计费中台]
        A8 -- 同步计费结果 --> A9[清结算]
        A9 -- 执行清算与划转 --> A4
    end

    subgraph S4[结果同步与对账]
        A4 -- 动账通知 --> A10[对账单系统]
        A9 -- 结算结果通知 --> A2
        A10 -- 数据聚合 --> A11[账单文件]
    end

    S1 --> S2 --> S3 --> S4
```

## 2.5 系统模块交互关系
模块间主要通过同步API调用进行交互，部分场景辅以异步消息通知。核心交互围绕“行业钱包”、“账户系统”、“清结算”和“电子签约平台”展开。

```mermaid
flowchart TD
    GEN[三代] -->|1. 触发开户| WALLET[行业钱包]
    WALLET -->|2. 开立账户| ACC[账户系统]
    BC[业务核心] -->|3. 提交分账| WALLET
    WALLET -->|4. 校验关系| USER[用户中心]
    WALLET -->|5. 发起签约/认证| SIGN[电子签约平台]
    SIGN -->|6. 执行打款验证| ACC
    SIGN -->|7. 调用人脸服务| FACE[外部人脸识别]
    WALLET -->|8. 处理分账指令| TX[交易系统]
    TX -->|9. 调用资金划转| ACC
    TX -->|10. 请求计费| FEE[计费中台]
    SETTLE[清结算] -->|11. 请求结算划转| ACC
    SETTLE -->|12. 同步手续费| FEE
    ACC -->|13. 动账通知| STMT[对账单系统]
    SETTLE -->|14. 结算明细| STMT
    RISK[风控] -->|15. 风险检查| BC
    RISK -->|16. 风险检查| WALLET
    PAYOUT[代付系统] -->|17. 批量付款指令| ACC
    PAYOUT -->|18. 校验付款授权| SIGN
    LEDGER[账务核心] -->|19. 核对交易| STMT
    LEDGER -->|20. 账户操作| ACC
```