# 对外展示与分发方式（按受众拆分）

> 回答的问题："IT 部门 / 研发 / 非技术人员，分别应该用什么方式从 skill-hub 获取 skill？" 三类人对"安装"这件事的技术门槛完全不同，不能用一套 UX 打发所有人。

## 前提：三类受众对应的实际工具（2026-07-02 确认）

| 受众 | 实际使用的 agent 工具 | 技术门槛 |
|---|---|---|
| 研发（少数，含你本人） | Claude Code CLI | 熟悉命令行 |
| 研发/内网主流用户 | **OpenCode**（接自建 DeepSeek V4） | 熟悉命令行，但工具本身没有 marketplace |
| 未来可能的全员场景 | **OpenClaw**（网关型，带浏览器 Control UI + 移动端） | 不要求会用命令行 |
| IT 部门 | 不是 skill 的"使用者"，是治理者 | 需要管理视图，不是安装视图 |
| 非技术人员 | 目前没有对应的 agent 工具在用 | 见下方"非技术人员"专节——这是最需要想清楚的部分 |

## 研发（OpenCode / Claude Code）：Web 门户 + 一行命令

不管 Phase 几，都应该有一个**只读的 Web 目录页**（哪怕 Phase 1 就是纯静态 HTML，从同一份 CI 生成的索引渲染出来）：可搜索、可看每个 skill 的说明/风险等级/维护者/更新时间，页面上直接给出对应工具的安装命令，复制粘贴即可：

- OpenCode / 其他读 `.agents/skills/` 的工具：`curl -fsSL https://skill-hub.internal/install.sh | bash -s <skill-name>`（脚本把对应目录同步到 `~/.config/opencode/skills/` 或当前项目的 `.agents/skills/`，用户自己选全局装还是项目级装）。
- Claude Code：`/plugin marketplace add https://skill-hub.internal/marketplace.json` 然后 `/plugin install <name>@skill-hub`（一次性加好 marketplace 之后，后续都是原生体验）。

这条路径不需要非常复杂的工程——本质是"Helm/ChartMuseum 那种静态目录页 + 一个安装脚本"，不需要账号系统，因为发布权限已经在 git 层面管住了，安装本身是只读操作。

## IT 部门：治理视图，不是安装视图

IT 部门的诉求不是"装 skill"，是"知道有哪些 skill、谁发布的、有没有过审、出问题能不能马上处理"。对应到架构上：

- 复用同一个 Web 门户，但接入 SSO 后按角色多开放一层：审查状态、审计日志（见 [`../security/02-lifecycle-controls.md`](../security/02-lifecycle-controls.md) 第 8 步）、吊销操作入口（见 [`../security/04-quarantine-review-and-incident-response.md`](../security/04-quarantine-review-and-incident-response.md)）。
- 另一个真正属于 IT 的分发动作：**批量下发"公司标准 skill 集"**——通过现有的终端管理工具（无论是软件分发工具还是登录脚本），在员工机器初始化时把一批已经 `approved`（你亲自审核通过）的 skill 预置进 `~/.config/opencode/skills/`，用户不需要自己动手装，这也是 IT 部门"统一管控基线"的常规做法，不是 skill-hub 需要重新发明的东西，只是 skill-hub 要把"当前 approved 清单"这个数据以脚本能读的形式（比如一个 JSON 列表）暴露出来给 IT 的下发工具消费。

## 非技术人员：不做"下载"这件事，做"可见 + 治理前置"

这是三类人里最容易想岔的一类——**不要假设非技术人员会经历"打开网页 → 找到 skill → 下载/安装"这个流程**，原因：

1. 目前没有一个非技术人员在用的 agent 客户端支持"装 skill"这个概念（Claude.ai 网页版虽然支持上传自定义 skill，但那是个人账号级、不支持组织统一分发，且要求 Pro/Team/Enterprise 套餐 + 代码执行权限，跟这次"内网自建模型"的场景对不上）。
2. 未来最可能的答案其实是 **OpenClaw**：它的定位就是"自建网关，连接聊天类前端和移动端，让非工程背景的人通过聊天界面用上 agent 能力"。也就是说，**非技术人员不会、也不应该自己去挑一个 SKILL.md 装上——他们应该是通过聊天/移动端界面，使用某个已经被人（IT/研发）挑好、审核过、配置好的能力**，skill 本身对他们是不可见的实现细节。

**结论（现阶段）**：
- 非技术人员现在唯一需要的是**只读浏览权限**——同一个 Web 门户，看得到 skill-hub 里有什么能力、大概能干什么、谁负责，但没有"安装"按钮，因为对他们来说没有可以安装的目标。如果他们想用某个能力，走的是"找研发/IT 帮忙接入"，不是自助流程。
- 一旦 OpenClaw 真的落地，skill-hub 的角色变成给 OpenClaw/ClawHub（或者内部对应的东西）供货：**skill-hub 输出的是"已经审查过的能力清单"，由 IT/研发把这些能力接进 OpenClaw 的聊天/移动端界面，终端的非技术用户全程不接触 SKILL.md 文件本身**。这一条要等 OpenClaw 的实际接入方式明确后再细化，现在只需要保证 skill-hub 的审查产物（签名+分级+manifest）足够结构化，将来能被这一层消费，不需要现在就为它设计专门的下载 UX。

**一个强化这个结论的理由**：ClawHub 生态在 2026-02 出过大规模恶意 skill 事件（见 [`../security/01-threat-model.md`](../security/01-threat-model.md)），受害的正是"用户自己在 registry 里挑一个 skill 装上"这种自助模式——对非技术人员来说，他们最没有能力识别一个 SKILL.md 内容是否可疑（这需要读懂技术细节），所以更不应该让他们走"自助挑选安装"这条路。这进一步支持"非技术人员只应该消费别人已经审查通过、包装好的能力，不应该有自己的安装动作"这个设计方向。
