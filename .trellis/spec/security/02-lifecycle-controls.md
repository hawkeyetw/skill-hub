# skill 生命周期的九个阶段与对应安全手段

> 这是对"skill-hub 收集到的 skill，安全性问题可以通过哪几个方面、哪些手段维护"这个问题的直接回答。每个阶段列出**具体机制**，不是原则性的话。
>
> **运营模式前提（2026-07-02 确认，2026-07-02 第二轮补充调整审查强度分配）**：skill-hub 由你一个人维护，skill 的主要来源是**你去市面上（GitHub、agentskills.io 社区、ClawHub 一类公开渠道）采集回来的第三方内容**，偶尔有同事想投稿。这意味着——和 npm/VS Code 那种"防内部发布者账号被接管"的威胁模型不同，**你的头号风险是"引入了本来就有问题的外部内容"**，跟 ClawHub 用户当初的处境几乎一样（见 [01-threat-model.md](./01-threat-model.md) 的 ClawHavoc 案例）。区别是：这次由你充当那个原本缺失的"引入前审查"角色。为了不让你被淹没在人工审查里，下面按**来源**把审查强度拆成两条线——外部采集的一律走全套流程（含强制沙箱），内部来源（同事投稿/自己写）先靠自动扫描过一遍，人工读正文和沙箱这两步改成"视情况"，把你能省下来的精力都省下来。完整的单人操作清单见 [05-solo-operator-playbook.md](./05-solo-operator-playbook.md)。

## 1. 提交 / 接入（Intake）—— 按来源分两条线（2026-07-02 调整：以来源而不是风险等级决定审查强度）

**为什么按来源分线，不按 manifest 里的 risk_tier 分**：risk_tier 是 skill 自己声明的字段，外部来源的 skill 完全可能故意把风险等级填低来逃避审查——不能让被审查对象自己决定审查强度。来源（source 字段，见 [03-manifest-and-runtime-enforcement.md](./03-manifest-and-runtime-enforcement.md)）不是它自己能伪造的（外部采集就是外部采集，同事投稿有 SSO 身份背书），所以用来源做强制分支更可靠，同时也是减少你人工投入的关键——**内部来源的大部分工作可以交给自动扫描**。

| | Track E · 外部采集（`collected-external`） | Track I · 内部来源（`colleague-submitted` / `self-authored`） |
|---|---|---|
| 接入方式 | 你从 GitHub/agentskills.io/ClawHub 等公开渠道找到的 | 同事过 SSO 投稿，或你自己纯手写 |
| 落地 | **一律先放进"待审"目录，不直接放进对外可见目录**——哪怕作者看起来是知名项目/账号 | 同样先落"待审"目录，但可信度基线更高 |
| manifest | 大概率没有，需要你自己根据实际内容补一份 | 同事投稿时让他们附一句"干什么用的/需要什么权限"，方便你写 manifest 时对照 |
| 第 2 步静态扫描 | **强制** | **强制**（自动化，不额外增加你的负担） |
| 第 2 步人工读正文 | **强制**，不能跳 | **视情况**：静态扫描全过 + risk_tier 低 → 可以只是快速扫一眼而不是逐字读；risk_tier 中/高，或者扫描有可疑但不到"直接拒绝"的程度 → 还是要认真读一遍 |
| 第 3 步沙箱 | **强制，任何 risk_tier 都要过一遍**——不因为它自称"不需要网络/shell"就免检，manifest 声明本身在外部来源场景下不可信 | **视情况**：只有 risk_tier 中/高，或者声明了 shell/网络访问，或者是这个投稿人第一次投稿，才需要跑；纯文档类、无脚本、低风险的内部投稿可以跳过 |

审批权始终只在你一个人手上，不管走哪条线——分线只是为了把内部来源里"大概率没问题"的那部分工作自动化掉，不是放松内部来源的底线。

## 2. 静态审查（Static Review）—— 两条线都跑，全自动，不占用你的时间

- frontmatter schema 校验（必填字段、字段类型、`allowed-tools`/`disallowed-tools` 是否合法）。
- 路径穿越检测（`scripts/`、`references/` 里是否有指向仓库外的路径）。
- 密钥/secret scanning（参考 Hugging Face 用 TruffleHog 的方式：只对"能验证有效"的密钥告警，减少误报）。
- 危险 shell 模式检测（`rm -rf`、`curl | sh`、反引号/`$()` 里的可疑命令、对外网络请求的域名列表）。
- **prompt injection 模式检测**（这一条是 skill 特有的，其他生态不需要）：扫描 HTML 注释、Unicode 同形字/零宽字符、base64 编码块、"不要告诉用户"/"忽略之前的规则"这类话术、指向远程 URL 且会被自动 fetch 执行的内容、文件大小明显超出内容合理范围（对应 JFrog 发现的 22MB padded README 投毒手法）。
- 这一步的产出是"能不能进人工环节"的第一道闸——任何高危命中，两条线都直接拒绝，不管来源是外部还是内部。

**人工读正文这一步**（渲染后的完整文本，不是 diff 摘要）按上面 Track E/Track I 的规则决定强制还是视情况；无论哪条线，一旦要读，读的都是 agent 实际会看到的完整文字，因为攻击者会把恶意指令藏在长文档中间或者不显眼的示例代码块里。

## 3. 动态审查 / 沙箱验证（Quarantine Review）—— Track E 强制、Track I 视情况

具体环境设计见 [04-quarantine-review-and-incident-response.md](./04-quarantine-review-and-incident-response.md)：

- 一次性容器/微虚拟机，注入假凭证（canary secrets）和假仓库。
- 全量记录工具调用、文件读写、网络请求。
- 检测是否有"读取凭证 + 尝试外发"这种组合行为——单独读取或单独请求外网都可能是正常功能，组合出现才是强信号。
- 你要看的只是**日志摘要**（有没有命中"组合行为"告警），不需要逐条看原始日志，这一步对你来说是"等脚本跑完看结论"，不是需要盯着的人工环节。

## 4. 签名与来源认证（Signing & Provenance）

- 通过审查的 skill，由 registry 侧签名（内部签名即可，不需要完整 PKI：可以用短期证书 + 内部 CA，或者对齐 cosign 的 keyless 签名思路，绑定 CI job 身份而不是长期私钥）。
- 记录一份 in-toto/DSSE 风格的 attestation：谁审查的、什么时间、静态扫描结果、沙箱验证结果、审批人。这份记录本身也要版本化保存，用于将来的事件回溯。
- **签名证明的是"经过了 skill-hub 的审查流程"，不是"内容一定无害"**——这一点要在文档和 UI 上明确说明，避免团队产生虚假的安全感（这也是 npm provenance 文档自己反复强调的：provenance proves origin, not benignness）。

## 5. 发布与版本化（Publish & Versioning）

- 按 digest（内容哈希）不可变寻址，版本号只是人类可读的别名，指向不可变内容。
- **信任状态只保留三档**（单人运营，不需要多团队分级审批那套重流程）：`pending`（已采集/投稿，自动扫描中或等你审）→ `approved`（你亲自看过内容 + 扫描/沙箱结果，签字通过——只有这一档对内网用户可见/可装）→ `revoked`（曾经 approved，后来因为问题下架）。风险等级（低/中/高，见 manifest 里的 `risk_tier`）是另一个独立维度，用来决定要不要走沙箱验证（第 3 步），不是发布状态。
- 支持 `stable`/`beta` 两个 channel，允许在不影响生产使用的前提下做灰度验证。

## 6. 分发与访问控制（Distribution & Access Control）

- 客户端侧（Claude Code 设置）下发团队级 allowlist：只允许安装 skill-hub 里达到某个信任等级的 skill。
- 高风险能力（申报了 shell 执行、broad 文件系统访问）的 skill 默认不出现在"推荐"列表里，需要用户显式搜索/确认。
- 利用 Claude Code 原生已有的策略钩子：`strictKnownMarketplaces`、`blockedMarketplaces`、`disableSideloadFlags`——skill-hub 只需要维护"哪些 marketplace 是被允许的"这份配置，不需要重新发明分发协议本身。

## 7. 运行时强制（Runtime Enforcement）

- agent 加载 skill 时，manifest 声明的权限范围是硬性上限，不是建议——manifest 之外的工具调用/网络请求/文件访问一律 deny，走正常的 Claude Code 权限确认流程。
- 详细设计见 [03-manifest-and-runtime-enforcement.md](./03-manifest-and-runtime-enforcement.md)——这是整套方案里最容易"设计了但没人执行"的一环，必须明确谁（agent 本身的 permission 系统，还是 skill-hub 分发的客户端策略配置）来强制。

## 8. 监控与审计（Monitoring & Audit）

- 记录：skill 何时被激活、渲染进上下文的完整 prompt 内容、期间的工具调用、文件 diff、网络请求尝试、用户的审批/拒绝决定。
- 这份日志是事件响应的基础——没有它，"skill X 是否影响了谁"这个问题在出事之后根本回答不了。

## 9. 弃用与吊销（Deprecation & Revocation）

- 详细流程见 [04-quarantine-review-and-incident-response.md](./04-quarantine-review-and-incident-response.md)。
- 核心能力：能够把一个已发布版本标记为"已吊销"，并且这个状态能传导到所有已经 `/plugin marketplace add` 过这个 hub 的客户端（不只是"从索引里删除"——删除只影响新安装，已装的还在）。
