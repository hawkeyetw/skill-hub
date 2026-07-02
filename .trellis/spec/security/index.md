# skill-hub 安全与生命周期管理方案

> 回答核心问题："skill-hub 收集到的 skill，安全性问题要通过哪几个方面、哪些手段维护？" 结论：**skill 不是普通的代码包，它是会被加载进 agent 上下文、直接驱动 agent 行为的"可执行策略"（executable agent policy）**。这个定性决定了 skill-hub 的安全模型必须比普通制品仓库（npm/Docker/VS Code 扩展）多管一层——不仅要管"代码有没有恶意逻辑"，还要管"文字指令有没有在操纵 agent"。

> **运营模式（2026-07-02 确认）**：skill-hub 由你一个人维护，提供给内网的 IT/研发/非技术人员使用。skill 的主要来源是**你去市面上（GitHub/agentskills.io/ClawHub 一类公开渠道）采集的第三方内容**，偶尔有同事投稿。这意味着你的处境和 ClawHub 官方当初的处境几乎一样——区别是这次你要主动补上他们当时缺失的"引入前审查"这一环。下面的方案已经按"单人可操作"的标准做了简化，不是照搬大厂那套多团队分级审批流程。**如果只想看一份端到端的操作清单，直接看 [05-solo-operator-playbook.md](./05-solo-operator-playbook.md)。**

---

## 六个维度 + 对应手段（总览）

| 维度 | 要解决的问题 | 核心手段 |
|---|---|---|
| **1. 供应链 / 身份维度** | 这个 skill 到底是谁发的、有没有被冒名 | SSO/LDAP 身份认证发布者、命名空间归属校验、registry 侧签名（内部轻量 Sigstore/cosign 风格）、发布来源可追溯（CI 构建 vs 手动上传区分对待） |
| **2. 内容维度** | SKILL.md 正文本身是否在操纵 agent（不需要任何脚本就能作恶） | 人工+LLM 辅助审查 SKILL.md **渲染后的文本**（不只是元数据）、扫描隐藏指令模式（HTML 注释/Unicode 技巧/base64/"don't tell user"类话术）、prompt injection 检测 |
| **3. 权限维度** | skill 声称需要什么权限，是否与它实际的能力匹配 | 强制 skill manifest 声明（工具/路径/网络域名/密钥类型）、default-deny、manifest 由 agent 运行时强制执行而非只是文档 |
| **4. 运行时维度** | 装之前怎么验证它"真的"安全，而不是只看声明 | 隔离沙箱（容器/gVisor/Firecracker）+ 假凭证（canary secrets）跑一遍，观察是否有越权读取/外发 |
| **5. 生命周期维度** | 一个 skill 从提交到退役，每个阶段谁把关、状态怎么流转 | 三档信任状态（pending → approved → revoked，单人运营简化版）、版本不可变寻址、弃用/吊销机制 |
| **6. 可观测维度** | 出了问题之后能不能第一时间知道、能不能止损 | 全量审计日志（激活/工具调用/文件 diff/网络请求）、kill-switch、事件响应流程 |

## 文档索引

| 文档 | 内容 |
|---|---|
| [01-threat-model.md](./01-threat-model.md) | 威胁模型：为什么 skill 的风险模型和普通代码包不一样，对应的 OWASP LLM Top 10 类目和真实事故 |
| [02-lifecycle-controls.md](./02-lifecycle-controls.md) | **核心文档**：skill 生命周期 9 个阶段，每个阶段的具体安全手段 |
| [03-manifest-and-runtime-enforcement.md](./03-manifest-and-runtime-enforcement.md) | skill manifest 字段设计 + 为什么必须由运行时强制执行 |
| [04-quarantine-review-and-incident-response.md](./04-quarantine-review-and-incident-response.md) | 沙箱审查环境的具体设计 + 吊销/事件响应流程 |
| [05-solo-operator-playbook.md](./05-solo-operator-playbook.md) | **单人维护者操作手册**：从"发现一个 skill"到"内网用户能装"的端到端步骤，把架构和安全方案揉成一份可以照做的清单 |

## 与架构方案的关系

安全方案不是独立于架构存在的——[`../architecture/03-deployment-and-auth.md`](../architecture/03-deployment-and-auth.md) 里 Phase 1 的"纯静态 + git 权限即发布权限"必须配合本文档 [02-lifecycle-controls.md](./02-lifecycle-controls.md) 里"CI 阶段强制跑准入检查"一起看，两者是同一套流水线的不同切面。
