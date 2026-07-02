# 开源生态架构参考

调研方式：分别检索各生态官方文档与实际事故报告确认（而非仅凭记忆），来源见各行链接。

| 生态 | 索引模型 | 最值得借鉴的信任机制 |
|---|---|---|
| **npm / Verdaccio** | API + DB（元数据+tarball），Verdaccio 是可自建的轻量私有代理（本地存储 + uplink 上游代理 + 访问规则） | scope 命名空间、发布强制 2FA/granular token、Sigstore provenance attestation（`docs.npmjs.com/generating-provenance-statements`） |
| **VS Code Marketplace / Open VSX** | 中心化 API 注册表，VSIX 包 + manifest | Verified Publisher（仅证明域名所有权，不代表内容安全）、发布时恶意软件/密钥扫描、namespace 相似度检测（`code.visualstudio.com/api/working-with-extensions/publishing-extension`） |
| **JetBrains Plugin Repository** | API 支撑的 marketplace，插件是 ZIP | **双重签名**：作者签名 + JetBrains 侧签名，未签名/被吊销的插件会在 IDE 里警告（`plugins.jetbrains.com/docs/intellij/plugin-signing.html`） |
| **Homebrew** | git-based "tap"：一个 tap = 一个装 Ruby formula 的 git 仓库 | 信任来自源码审查 + formula audit + 二进制包（bottle）校验和，没有中心化审核 |
| **Docker Registry / Harbor** | OCI API + 内容寻址 blob 存储（manifest/digest） | Harbor 在裸 OCI registry 上叠加：project 级 RBAC、robot account、Trivy 漏洞扫描、跨机房 replication（`goharbor.io/docs/.../vulnerability-scanning`） |
| **Helm / ChartMuseum** | **纯静态**：`index.yaml` + `.tgz`，任何 HTTP GET server 都能当 repo；ChartMuseum 是把这个模型做成可写服务的实现 | `.tgz.prov` 签名文件 + `helm install --verify` |
| **Hugging Face Hub** | git-native（模型/数据集/Space 都是 git 仓库，大文件走 Git-LFS/Xet） | 分层扫描：ClamAV 恶意软件扫描（每次 commit 触发）+ picklescan（检测 pickle 反序列化 RCE）+ TruffleHog 密钥扫描 + 第三方（Protect AI/JFrog）扫描；`safetensors` 格式作为 pickle 的安全替代方案 |
| **Backstage**（Spotify 内部开发者门户） | 不是制品仓库，是**目录/门户模式**：entity + 归属元数据 + 权限策略 | 集成方自定义 permission policy/RBAC，本质上是"编目 + 治理"而非"存储" |
| **GitHub Actions Marketplace** | git/release-based，`action.yml` + tag 发布即上架 | 发布强制 2FA、Verified Creator 标识、**消费侧建议 pin 到完整 commit SHA**（而不是可变 tag） |

## 直接相关的同类生态（不是"参考"，是我们实际要对接/竞争的对象）

| 生态 | 索引模型 | 现状 |
|---|---|---|
| **Claude Code plugin marketplace** | git/URL 托管的 `marketplace.json` + `/plugin` 命令 | 官方机制成熟，但只服务少数 Claude Code 用户，且不做任何内容审查/签名——skill-hub 存在的意义之一就是补上这一层 |
| **OpenCode**（内网现在主流工具） | **没有 registry**，纯本地文件/git/npm/社区目录页（`opencode.ai/docs/ecosystem/`） | 这是 skill-hub 必须自己填的空白：OpenCode 用户目前没有任何"发现/安装内部共享 skill"的现成通道 |
| **OpenClaw / ClawHub**（未来可能转向） | ClawHub 是官方定位的"skill and plugin registry"（`openclaw.ai/ecosystem`） | **2026-02 发生过真实的大规模恶意 skill 事件（ClawHavoc，341 个恶意 skill）**，OpenClaw 官方直到事件发生后才在 2026-02-07 上线 VirusTotal 扫描。详见 [`../security/01-threat-model.md`](../security/01-threat-model.md)。这是"内部审查层不能省"的最直接证据，也说明如果将来真的对接 ClawHub 生态，**skill-hub 的审查流水线不能依赖对方的把关**。 |

## 对 skill-hub 最有价值的 8 条模式

1. **产物用 `agentskills.io` 标准的 `SKILL.md` 目录格式**（落地在共享 `.agents/skills/`），Claude marketplace.json 只作为可选导出层；索引/检索/评分/审计这类"运营元数据"另起一套 API/DB 承载（详见 [01-registry-model.md](./01-registry-model.md)）。
2. **用 SSO/LDAP 组做命名空间归属**，发布前必须验证归属权，参考 npm scope / VS Code Verified Publisher 的思路。
3. **产物按 digest 不可变寻址**，支持 SemVer channel（stable/beta）+ 弃用/回滚，参考 OCI content-addressable 模型。
4. **准入检查跑在 CI 而不是靠人肉**：frontmatter schema 校验、路径穿越、密钥扫描、危险 shell 模式、异常体积/二进制文件、SBOM/provenance——参考 Hugging Face 的多层扫描器编排方式。
5. **安装前展示风险信息**：需要多少上下文、包含哪些脚本/hook/MCP server、请求了哪些预授权、维护者身份——这是 Claude Code 自己的安装 UI 已经在做的事，skill-hub 应该在此基础上叠加"是否通过审查"的标识。
6. **信任状态简化为三档**：pending → approved → revoked（单人运营不需要多级审批），但签名/验签的思路仍然保留，参考 JetBrains 双重签名 + Docker Content Trust 的"发布时签、拉取时验"模型——approved 状态本身要靠签名来标记，不是靠一个数据库字段"说了算"。
7. **客户端侧策略强制**：`strictKnownMarketplaces`、`blockedMarketplaces`、按团队的 skill allowlist、高风险 skill 默认禁用——这是 Claude Code 原生设置已经暴露的钩子，skill-hub 只需要下发正确的策略配置。
8. **安装全程可审计**：谁在什么时间从哪个来源装了哪个版本、拥有什么权限——为将来的事件响应（compromise 后需要知道"谁受影响"）打基础。
