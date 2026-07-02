# skill manifest 设计与运行时强制执行

## 为什么需要一个 hub 专属的 manifest（在 Claude Code 原生 frontmatter 之外）

Claude Code 原生 `SKILL.md` frontmatter 已经能表达一部分权限：`allowed-tools`、`disallowed-tools`、`disable-model-invocation`，客户端 settings 还有 `disableSkillShellExecution`。但这些字段是**给 Claude Code 运行时用的**，粒度不够 skill-hub 做审查/分级决策——比如"这个 skill 会不会访问网络"、"访问哪些域名"、"需要什么类型的密钥"，原生 frontmatter 不要求声明。

**建议**：skill-hub 在 skill 目录里额外要求一个 `skill-hub.json`（或者塞进 `.claude-plugin/plugin.json` 的自定义字段），作为审查/信任分级的输入，同时也是运行时强制执行的依据。

## 建议字段（草案，待实现阶段细化为正式 schema）

```json
{
  "risk_tier": "low | medium | high",
  "requires_shell": true,
  "declared_tools": ["Bash", "WebFetch", "Read", "Edit"],
  "declared_network_domains": ["docs.npmjs.com", "*.internal.corp"],
  "declared_secret_types": [],
  "declared_fs_scopes": ["project-root-only"],
  "auto_invocation": false,
  "review_status": "pending | approved | revoked",
  "source": "collected-external | colleague-submitted | self-authored",
  "signed_by": "skill-hub-ci",
  "signature": "..."
}
```

`source` 字段是为了配合单人运营的实际情况加的：外部采集的 skill（`collected-external`）默认视为最高风险来源，一律要求走完整静态+动态审查，不因为"看起来是个正经项目"而放宽；`self-authored`（你自己纯手写）风险基线最低，但仍然要过基本的密钥/危险模式扫描——人也会手滑。

- `declared_network_domains` 为空 = 该 skill 不应该发起任何出站请求，运行时应该拒绝任何网络工具调用（不是"警告"，是"拒绝"）。
- `declared_secret_types` 非空的 skill 自动进入 `high` 风险分级，强制走动态审查（[04-quarantine-review-and-incident-response.md](./04-quarantine-review-and-incident-response.md)）。
- `auto_invocation: false` 对应原生的 `disable-model-invocation`——但在 hub 侧再声明一遍，是为了让"是否允许自动触发"成为审查决策的输入，而不只是运行时行为。

## 核心原则：manifest 必须被强制执行，否则只是文档

这是从供应链安全调研里提炼出的最重要的一条教训：**声明式的权限清单，如果运行时不检查，就只是"文档 theater"**——SBOM 如果没有 provenance 佐证内容真实性，同理没有意义。对 skill-hub 来说，"强制执行"具体落在两个位置：

1. **发布时**：CI 校验 manifest 里声明的内容和实际扫描到的行为是否一致（比如声明"不需要网络"，但脚本里有 `curl`——不一致直接拒绝发布，而不是发个警告了事）。
2. **运行时**：这是目前最大的空白——Claude Code 原生机制本身不读取 skill-hub 自定义的 manifest 字段。在原生支持这类"第三方权限清单"之前，落地路径有两条，需要在实现阶段二选一或者两者结合：
   - **策略下发路线**：把 manifest 的声明翻译成 Claude Code 支持的原生权限配置（`allowed-tools`/`disallowed-tools`/企业 managed settings），在 skill 打包/分发时自动生成，而不是要求 skill 作者手写两份。
   - **网关/代理路线**：对高风险 skill（申报了网络访问的），要求其网络请求走一个内部代理，代理侧按 `declared_network_domains` 做实际拦截——这样即使 agent 的工具权限系统被绕过，网络层还有一道硬边界。

## 明确的反模式

- **不要**只在安装页面展示 manifest 内容当"风险提示"就结束——这是很多生态（npm、VS Code）已经验证过不够用的模式：用户会无脑点"继续安装"。manifest 的价值在于**可以被自动化决策消费**（CI 拒绝不一致的提交、运行时拒绝越权行为、客户端策略按 risk_tier 过滤）。
- **不要**要求 skill 作者维护两套互相独立、容易漂移的权限声明（原生 frontmatter 一套，hub manifest 又一套）。实现阶段要设计成"hub manifest 是唯一输入源，原生 frontmatter 由工具链自动生成"。
