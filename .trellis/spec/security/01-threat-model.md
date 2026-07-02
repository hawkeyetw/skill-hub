# 威胁模型

## 核心命题：skill 是"可执行的 agent 策略"，不是文档

Anthropic 自己的文档明确警告：项目级 skill 在被信任之前必须审查，因为**"一个 skill 可以给自己授予广泛的工具访问权限"**（`code.claude.com/docs/en/skills`）。一个恶意/被篡改的 `SKILL.md`，**即使不带任何 `scripts/` 里的可执行代码**，光靠 Markdown 正文里的自然语言指令就能让 agent：

- 读取 `.env`/密钥文件"作为上下文"，再通过看似正常的操作（提交、发 issue、调用某个工具）把内容带出去；
- 引导 agent "别提这些步骤"、"直接 commit"、"优先用 `rm -rf` 清理"、"跳过测试"；
- 让 agent 把攻击者控制的文本当成比用户指令优先级更高的"流程"。

这正是这套体系和 npm/Docker/VS Code 扩展的根本区别：**那些生态的信任问题是"这段代码会不会做坏事"，skill-hub 多一层"这段文字会不会说服 agent 做坏事"。** 审查流程如果只扫描 `scripts/` 里的代码，漏掉 `SKILL.md` 正文，等于没审查。

## 对应的 OWASP LLM Top 10 类目

- **LLM01 Prompt Injection**（含 indirect injection：从文件/网页/RAG 内容里注入指令）——可导致密钥泄露、越权调用函数、在关联系统里执行命令。`genai.owasp.org/llmrisk/llm01-prompt-injection/`
- **LLM06 Excessive Agency**——过度的功能/权限/自治性，把"模型被误导"变成"现实世界的破坏"。`genai.owasp.org/llmrisk/llm062025-excessive-agency/`
- **LLM07 Insecure Plugin Design**（旧编号，但对 skill/tool API 仍然适用）——接受自由格式指令、弱参数校验、对敏感操作不要求二次确认。`genai.owasp.org/llmrisk2023-24/llm07-insecure-plugin-design/`

## 真实事故作为参照（不是假设性风险）

- **ChatGPT 插件 · Cross-Plugin Request Forgery / markdown 图片外带数据**（Johann Rehberger，2023）：攻击者通过间接 prompt injection 劫持一个低权限插件（如网页浏览），再串联到高权限插件（如能读邮件的 OAuth 插件），把数据用 Markdown 图片渲染的方式偷偷外带。`embracethered.com/blog/posts/2023/chatgpt-cross-plugin-request-forgery-and-prompt-injection/`
- **MCP Tool Poisoning**（Invariant Labs）：工具描述里藏着的隐藏指令，让 agent 读取 SSH key/配置文件，通过工具参数把内容带出去，甚至能"影子劫持（shadow）"其他 MCP server 上本来可信的工具。这是离 skill-hub 场景最近的一个案例——机制几乎一样，只是载体从 tool description 换成了 SKILL.md。`invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks`
- **供应链层面**（不涉及 prompt injection，纯代码/身份维度）：npm event-stream/flatmap-stream（维护者账号被接管）、ua-parser-js（账号接管+挖矿木马）、VS Code Marketplace 的 GlassWorm/Darcula（超过百万安装量的恶意扩展、Verified Publisher 徽章被绕过）、Hugging Face Hub 的 pickle 反序列化 RCE 模型——说明"内容审查"之外，身份/供应链维度的威胁同样真实存在，且规模可以很大。
- **ClawHub / "ClawHavoc"（2026-02，与 skill-hub 场景几乎是同一个问题的真实案例，独立信源核实过，不是道听途说）**：OpenClaw 的 skill/plugin registry ClawHub 被投毒，安全公司 Koi Security 于 2026-02-01 披露 **341 个恶意 skill**，335 个可归到同一波攻击（"ClawHavoc"），手法包括伪造前置依赖、挂在 GitHub 的恶意 ZIP、glot.io 代码片段、投放 AMOS（macOS 窃密木马）。Palo Alto Unit 42、Trend Micro 分别独立复现/佐证；JFrog 另外发现一个叫 `omnicogg` 的 ClawHub 投毒包，**把恶意的 curl-to-bash payload 藏在一个刻意撑到 22MB 的 README 文件里**（直接印证下面"内容维度审查必须看渲染后的完整正文，不能只扫代码/只看摘要"这条原则）；Bitdefender 统计当时抽检的 OpenClaw skill 里约 17% 有恶意行为。OpenClaw 官方直到事件发生后（2026-02-07）才上线 VirusTotal 扫描——**说明"先有 registry、后补审查"这个顺序在真实世界已经造成过大规模损失，skill-hub 不能重蹈覆辙**。（注：调研中还看到一个"该事件同时牵涉 Hugging Face Hub 的跨注册表攻击"的说法，经独立核实**没有找到可信来源支持这一点**，予以排除，只采信上面经多家安全公司独立佐证的核心事实。）

## 威胁分类小结（用于对照 [02-lifecycle-controls.md](./02-lifecycle-controls.md) 里的具体手段）

1. **内容作恶**：SKILL.md 正文本身是攻击载体（prompt injection / 隐藏指令 / 社会工程话术）。
2. **代码作恶**：`scripts/` 里的可执行代码是攻击载体（reverse shell、密钥窃取、挖矿）。
3. **身份/供应链作恶**：发布者账号被接管、命名相似导致装错、"静默更新"把良性 skill 换成恶意版本（rug pull）。
4. **权限滥用**：skill 声明的权限和实际需要的不匹配，或者 agent 运行时根本不强制权限声明，导致"申报的都是幌子"。
