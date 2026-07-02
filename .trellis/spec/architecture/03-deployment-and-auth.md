# 部署拓扑与身份接入（建议分阶段演进）

> 原则：内网现在没有 GitLab/Harbor 这类基础设施可以白嫖，但也不要为了"看起来完整"而一次性把 DB、审查流水线、Web 门户全部建出来。按需要演进，避免过度设计。

## Phase 1：最小可用（纯静态 + git 权限即发布权限）

- **git 仓库**：一个内部 git server（自建裸仓库 + SSH，或轻量部署一个 Gitea 实例——这是唯一值得考虑的"基础设施投入"，因为后面所有阶段都要靠它做 PR review/审计）。每个 skill 是仓库里的一个 `.agents/skills/<name>/` 目录（或独立仓库，视团队规模决定 mono-repo vs multi-repo）。
- **发布 = merge 到主分支**：CI（哪怕是最简单的 git hook / cron 脚本）在 merge 后重新生成一份内部索引（扫描目录 → 产出索引，模式对齐 Helm `index.yaml`），发布到内网 Nginx 静态托管；同一个 job 顺带产出 `.claude-plugin/marketplace.json` 给少数 Claude Code 用户用。
- **接入方式**（因为 OpenCode 没有原生 marketplace 命令，这里是 Phase 1 必须自己补的部分，具体按受众拆分见 [04-audience-distribution-channels.md](./04-audience-distribution-channels.md)）：给 OpenCode/研发用户提供一个一行命令的同步脚本（`curl https://skill-hub.internal/install.sh | bash -s <skill-name>`，效果是把对应目录 clone/rsync 进 `~/.config/opencode/skills/` 或项目级 `.agents/skills/`），Claude Code 用户走 `/plugin marketplace add https://skill-hub.internal/marketplace.json`。
- **权限模型**：发布权限 = git 仓库/目录的写权限（PR 审批人 = 对应 LDAP 组成员）。**不需要单独的用户系统**，天然对接 SSO/LDAP：谁能 push/approve，由 git server 的 LDAP 集成决定。
- **代价**：没有搜索/评分/安装统计，没有自动化安全扫描（初期靠 code review 人肉把关）。这是可以接受的起点，但**不能跳过安全方案里的静态/动态审查（见 [`../security/02-lifecycle-controls.md`](../security/02-lifecycle-controls.md)）**——哪怕是 Phase 1，CI 也应该在生成索引之前跑最基本的准入检查（密钥扫描、危险模式检测），这一步不依赖 DB，纯脚本就能做。**这一条比原计划更重要**：OpenClaw/ClawHub 生态已经证明了"没有发布前扫描的 skill registry"会被大规模投毒（见 [`../security/01-threat-model.md`](../security/01-threat-model.md)），Phase 1 不能把这一步留到 Phase 2 才做。

## Phase 2：加审查流水线

- CI 流水线拆分为：静态扫描 → 沙箱动态验证（quarantine）→ 签名 → 发布。对应 [`../security/`](../security/index.md) 的完整生命周期控制。
- 审查通过状态写入 skill 自己的 manifest（随 git 提交一起走版本控制），不需要额外 DB。

## Phase 3：视规模决定是否要 Web 门户 + DB

- 触发条件（任一满足再做，不要提前做）：skill 数量大到 git 目录浏览体验太差、需要跨团队检索/评分、需要给安全团队一个审计后台、需要按用户/项目做细粒度可见性控制（而不是"整个 marketplace 一起可见/不可见"）。
- 到这一步才需要一个真正的 API + DB 服务，Web UI 挂在 SSO 后面（内网 SSO 网关做认证，服务本身只需要信任网关传来的身份头，不用自己实现登录）。

## SSO/LDAP 接入点小结

| 环节 | 接入方式 |
|---|---|
| 发布（谁能提交/合并 skill） | git server 的 LDAP 认证 + 分支保护/PR 审批人规则 |
| 浏览/检索（Phase 3 才有 Web UI 时） | 内网 SSO 网关反代到 Web 服务，服务信任网关注入的身份头 |
| 安装（OpenCode 装同步脚本 / Claude Code 拉 marketplace.json） | 走内网 HTTPS 静态资源，不需要登录——**注意**：如果要做"分团队可见性"，静态托管这条路走不通，必须 Phase 3 的 API 层做鉴权后再返回内容 |
| 审计（谁装了什么） | OpenCode 和 Claude Code 原生机制都不上报安装事件到远端；如果需要"谁装了什么"的可见性，唯一可靠的办法是让 skill-hub 自己的安装脚本在拉取时上报（脚本里加一行调用内部 API），而不是指望任何一个 agent 工具自己给出安装遥测 |

## 开放问题（需要你决策，会影响上面的选型）

- 见 [`index.md`](./index.md) 里列的三个开放问题——尤其是"是否要分团队可见性"直接决定 Phase 1 能不能长期只用纯静态托管。
