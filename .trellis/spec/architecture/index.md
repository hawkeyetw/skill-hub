# skill-hub 架构方案

> 内网 skill 分发中心：让公司内网其他用户可以发现、安装、复用 Claude Code Skills（以及未来可能的 plugins/commands/agents）。当前处于**方案评审阶段**，尚未选定实现技术栈，未开工写代码。

---

## 背景与约束（2026-07-02 确认，含当天补充修正）

- **身份**：内网已有统一 SSO/LDAP/AD，skill-hub 应该接入而不是自建用户体系。
- **基础设施**：没有可复用的 GitLab/Gitea、没有 Harbor/Nexus/Artifactory 之类的制品库——skill-hub 是纯新建。
- **实际使用的 agent 工具（重要，第一版方案曾经假设错误）**：内网用户主力用 **OpenCode**（开源多 provider agent CLI），接的是**自建 DeepSeek V4 等开源模型**，不是 Anthropic 云端 API；未来可能转向 **OpenClaw**（自建网关型 agent 系统，带浏览器 Control UI + 移动端，面向更广的用户群体）。Claude Code CLI 目前只是少数重度用户在用。详见 [01-registry-model.md](./01-registry-model.md) 开头的修正说明。
- **产物形态**：Skill = 一个 `SKILL.md`（YAML frontmatter + Markdown 指令）+ 可选的 `scripts/`、`references/`、`assets/`，遵循跨厂商开放标准 `agentskills.io`。这些内容会被加载进 agent 的上下文，agent 可以按照其中的指令调用工具（含 shell）——即 skill 是"可执行的 agent 策略"，不是纯文本文档。这个特性同时决定了架构设计和安全设计（见 [`../security/`](../security/index.md)）。

## 文档索引

| 文档 | 内容 |
|---|---|
| [01-registry-model.md](./01-registry-model.md) | 核心决策：索引模型（git-backed vs API+DB）、产物格式（对齐 `agentskills.io` 标准，Claude marketplace 只是可选导出层）、命名空间/归属模型 |
| [02-reference-architectures.md](./02-reference-architectures.md) | 9 个开源生态的架构参考对照表 + OpenCode/OpenClaw 现状 + 可复用的模式 |
| [03-deployment-and-auth.md](./03-deployment-and-auth.md) | 部署拓扑建议（分阶段演进）、SSO/LDAP 接入点 |
| [04-audience-distribution-channels.md](./04-audience-distribution-channels.md) | **按受众拆分的分发方式**：研发（OpenCode/Claude Code）、IT 部门（治理视图）、非技术人员（现阶段只读浏览，不做自助安装） |

## 关键决策速览（待评审）

1. **产物格式对齐 `agentskills.io` 开放标准**，落地在共享 `.agents/skills/<name>/` 目录，OpenCode/Claude Code 都能直接读；Claude 专属的 `.claude-plugin/marketplace.json` 从 CI 的同一份源里顺带多导出一份，作为对少数 Claude Code 用户的加成，不是主路径。
2. **索引模型：git 作为唯一可信源 + 薄 API/DB 层做检索、评分、安装审计**，不是重新发明一个制品仓库。理由见 [01-registry-model.md](./01-registry-model.md)。
3. **分阶段演进而非一步到位**：Phase 1 纯静态（git + CI 生成索引 + Nginx 托管 + 一行安装脚本），Phase 2 加审查/扫描流水线，Phase 3 视规模决定是否要 DB 化的检索/评分/审计服务。避免过度设计。
4. **分发方式按受众拆分，不是一套 UX 打天下**：研发走 Web 门户 + 命令行安装；IT 部门是治理视图 + 批量下发标准 skill 集；非技术人员现阶段只做只读浏览，不设计自助安装流程，未来接入 OpenClaw 后由该层代为消费 skill-hub 的审查产物。详见 [04-audience-distribution-channels.md](./04-audience-distribution-channels.md)。

## 开放问题（需要你决策）

- 内网用户获取 skill-hub URL 的方式：直接 HTTPS 域名，还是需要过内网代理/VPN？
- 是否需要多租户/多团队隔离（不同部门的 skill 互相不可见），还是全公司统一可见？
- Phase 1 是否接受"仅 git push 权限控制 = 发布权限控制"这种最简模型，还是从第一天就要审查流水线？（**倾向后者**——见 [03-deployment-and-auth.md](./03-deployment-and-auth.md) 里 ClawHavoc 事件的教训）
- "openclaw" 这个未来方向目前只是初步确认它是真实产品（`openclaw.ai`，自建网关型 agent 系统），具体什么时候评估/落地、接入方式如何，还需要你进一步明确。
