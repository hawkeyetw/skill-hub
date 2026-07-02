# 索引模型与产物格式

> **2026-07-02 修正**：本文档第一版假设"内网用户 = 用 Claude Code CLI 的研发"，据此把产物格式绑定在 Claude Code 专属的 marketplace 机制上。用户澄清后发现实际情况不同，见下方决策 1 的重写。**关键事实**：内网用户主力用 **OpenCode**（多 provider 的开源 agent CLI），接的是**自建的 DeepSeek V4 等开源模型**，不是 Anthropic 云端 API；未来可能转向 **OpenClaw**（自建网关型 agent 系统，带浏览器 Control UI + 移动端，面向更泛的用户群）。Claude Code CLI 目前只是少数重度用户（含你本人）在用。这个事实必须作为整个架构方案的第一约束。

## 决策 1（重写）：产物格式 = 对齐 `agentskills.io` 开放标准，而不是绑定 Claude Code

**不要把 skill-hub 的核心产物格式绑定在任何单一厂商的机制上。** 调研确认：

- `SKILL.md`（YAML frontmatter + Markdown 指令 + 可选 `scripts/`/`references/`/`assets/`）本身是一个**跨厂商的开放标准**，规范在 `agentskills.io`（`agentskills.io/specification`）。约定的共享落地目录是 `.agents/skills/<name>/SKILL.md`，多个工具都读这个目录。
- **OpenCode 原生支持这个标准**：会扫描 `.opencode/skills/`、`~/.config/opencode/skills/`，也会扫描共享的 `.agents/skills/` 和 Claude 兼容的 `.claude/skills/`（`opencode.ai/docs/skills/`）。OpenCode 的**插件**（不是 skill）是另一套东西——JS/TS 模块，放在 `.opencode/plugins/` 或通过 `opencode.json` 的 npm 包安装（`opencode.ai/docs/plugins`），和 skill 分发无关，不需要 skill-hub 管。
- **OpenCode 没有内置的 marketplace/registry 命令**（没有 `/plugin marketplace add` 这种东西）。官方文档给出的分发方式就是"本地文件复制、npm 包、git、社区目录页"（`opencode.ai/docs/ecosystem/`）——这意味着**skill-hub 必须自己提供一个轻量安装机制**，不能像最初设想的那样"白嫖 Claude Code 现成的市场协议"。
- **Claude Code 兼容仍然值得保留，但降级为次要能力**：`.agents/skills/` 本身 Claude Code 也能读，加上如果要用 Claude 的插件打包（`.claude-plugin/marketplace.json`）、原生 `/plugin marketplace add` 体验，可以作为对少数 Claude Code 用户的"加成"，但不能是 skill-hub 的主路径——尤其是调研还发现 Claude Code 通过网关/代理接非 Claude 模型这条路目前官方文档不承诺支持，这进一步说明公司主流的自建 DeepSeek 场景下 Claude Code 不是普适方案。
- **OpenClaw 生态已经有自己的 registry 概念（ClawHub）**："a skill and plugin registry for discovering and installing community extensions"（`openclaw.ai/ecosystem`）。等公司真的转向 OpenClaw，skill-hub 的角色很可能从"提供安装机制"收窄成"提供审查/信任层，产物走 ClawHub 兼容格式或者内部镜像"——**但 ClawHub 生态在 2026-02 出过一次真实的大规模恶意 skill 事件（详见 [`../security/01-threat-model.md`](../security/01-threat-model.md) 的 ClawHavoc 案例）**，这恰恰证明了"skill 分发中心必须有审查层"不是过度设计，是必要项。

**结论**：核心产物 = 标准 `SKILL.md` 目录，落地在共享 `.agents/skills/<name>/`；这一份内容对 OpenCode（现在）、Claude Code（部分用户）、以及未来任何遵循 agentskills.io 标准或读 `.agents/skills/` 的工具（含未来的 OpenClaw，如果它也兼容这个目录）都通用。**厂商专属的打包格式（Claude 的 marketplace.json、未来 ClawHub 的格式）作为可选的"导出适配层"生成，不作为存储的唯一形态。**

**已知限制（原生机制都不管的部分，需要 skill-hub 自己补，这条不受上面调整影响）**：
- 不管是 Claude Code 还是 OpenCode，肉眼可见的共同点是：加载 skill 的机制本身**不做内容审查、不做签名校验、不做权限最小化强制**。Anthropic 自己的定位是 "highly trusted"，OpenCode 更是干脆没有市场层面的把关。这部分始终是 skill-hub 的核心价值，见安全方案（[`../security/`](../security/index.md)）。
- 权限声明目前只能通过各家自己的 frontmatter 字段（Claude 的 `allowed-tools`/`disallowed-tools`/`disable-model-invocation`；OpenCode 认的 frontmatter 字段是 `name`/`description`/`license`/`compatibility`/`metadata`，不含权限字段）表达，没有一个跨工具通用的权限声明机制——这意味着 [`../security/03-manifest-and-runtime-enforcement.md`](../security/03-manifest-and-runtime-enforcement.md) 里 hub 自定义 manifest 的必要性又增加了一层：它必须是跨工具的统一层，因为不能指望每个 agent 工具自己的权限字段能对齐。

## 决策 2：索引模型 = git 作为唯一可信源 + 薄 API/DB 层

对比过的 9 个生态里，索引模型分两大类（详见 [02-reference-architectures.md](./02-reference-architectures.md)）：

- **纯静态**：Helm/ChartMuseum（`index.yaml` + `.tgz`，任何能发 GET 请求的 HTTP server 都能当 registry）、Homebrew（tap = 一个 git repo）。运维成本最低，天然有 git 的审计/blame/PR review。
- **API + DB**：npm、VS Code Marketplace、JetBrains、Docker/Harbor。支持检索、评分、安装统计、RBAC、审计，但要自己运营一套服务。

**建议**：不要在 Phase 1 就重新造一个"数据库支撑的制品仓库"。skill 体积小（Markdown + 少量脚本），发布频率低（内部团队级），最合适的模型是：

1. **git 仓库是唯一可信源**——每次发布 = 一次 PR/commit，天然获得 code review、blame、revert、diff 审计，不需要额外造版本历史系统。skill 本体就是 `.agents/skills/<name>/SKILL.md` 目录，直接进版本控制，不需要额外的打包步骤。
2. **CI 在 merge 后生成/更新一份内部索引**（JSON/YAML 列出所有已发布 skill 及其信任等级，模式对齐 Helm 的 `index.yaml` 生成方式），连同签名/扫描结果一起发布到静态托管；如果要顺带给 Claude Code 用户导出体验，同一份 CI job 可以再多产出一份 `.claude-plugin/marketplace.json`（内容从同一个源生成，不是维护两份独立数据）。
3. 当确实需要"搜索"、"安装量统计"、"评分"、"按团队精细授权可见性"时，再加一层薄 API/DB（不改变 git 是可信源这个事实，DB 只是缓存/索引），这一步可以推迟到 Phase 2/3。

这个模式直接对应 npm provenance 的思路："协议证明*谁构建的*，不证明*内容无害*"——git 的作用同理：它给出可追溯的来源，内容是否安全由审查流水线（见 security 文档）另外把关。

## 决策 3：命名空间 / 归属模型（2026-07-02 按实际运营模式调整）

第一版假设的是"多个内部团队各自往 skill-hub 发布"，npm scope 那种模型。**实际情况是你一个人运营，主要内容来自外部采集，偶尔有同事投稿**——命名空间的作用因此从"发布权限隔离"变成"标注来源，方便追溯"：

- 建议按**来源**分命名空间，而不是按团队：`@curated/<name>`（你从外部采集、审核通过后重新发布的）、`@contrib/<colleague-id>/<name>`（同事投稿，标注是谁提的，方便回头问问题/追责，但审批权仍然只在你手上）、`@internal/<name>`（你自己纯手写的）。
- 发布写权限：git 仓库的写权限就是你自己（+ 你信任的极少数人，如果需要别人帮忙做 CI 层面的活）。同事的"投稿"不等于"写权限"，走的是提 PR/丢文件夹给你，由你 merge，不需要给他们开通 git 写权限。
- SSO/LDAP 在这个模型里主要用在两个地方：① 同事投稿时确认"这是谁提的"（不是匿名文件）；② [04-audience-distribution-channels.md](./04-audience-distribution-channels.md) 里控制谁能浏览/安装（读权限），而不是控制谁能发布（写权限本来就只有你）。
- 命名唯一性检查依然要做——不是防"内部团队抢名字"，而是防**你从外部采集时把两个不同来源、名字相似的 skill 搞混**（比如收录了一个和之前已收录 skill 同名但内容不同的新版本，没意识到是不同作者），这条对单人运营反而更重要，因为没有第二个人帮你交叉检查。
