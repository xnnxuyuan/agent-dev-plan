# 12 周 Agent 开发路线图

> 为「会一点 Python + 每天 2–3 小时 + 求职/做产品/工作中落地三个目标」定制
> 总投入：约 12 周 × 16 小时 ≈ **190 小时**（工作日 2h + 周末 3h）
> 配套代码：[\`week0/agent_loop.py\`](week0/agent_loop.py)、[\`week0/README.md\`](week0/README.md)

---

## 0. 先讲清三件事，能省你 100 小时

**① 三个目标其实是同一条主线。**
不管你是求职、做产品还是落地，雇主/用户/老板看的都是同一件东西：**一个能跑分、能演示、能部署的 Agent 作品**。
所以这份计划不写三套路线，只写一条主线，每个阶段顺手产出对应目标的素材。

**② 顺序反直觉：先评测，后框架；先单 Agent，后多 Agent；先 CLI，后 Web。**
初学者最常见的浪费是把时间花在框架 API 上——但 2026 年的现实是：**框架三个月换一茬，能力不会变**。
真正保值的是：上下文工程、工具设计、评测、成本与安全。这四样在任何框架下都通用。

**③ 每天必须写代码，读:写 ≈ 3:7。**
只看教程的人三个月后依然写不出 Agent。**每天必须有可运行的产出**，哪怕只是给工具加了一句更好的错误提示。

### 每日节奏模板

| 时长 | 内容 | 要求 |
|---|---|---|
| 20 min | 读（文档/论文/别人的源码片段） | 只读跟今天要写的代码直接相关的东西 |
| 80 min | 写（当周项目主线） | 必须让代码跑起来，哪怕功能残缺 |
| 20 min | 记 + 提交（TIL 笔记 + git commit） | 记录"今天卡在哪、怎么解的"，这是你博客的素材 |

周末多出的 1 小时用来**跑评测 + 写周报**（第 5 周起）。

---

## 1. 能力地图：Agent 开发到底要学什么

| 模块 | 一句话本质 | 新手常见误区 | 对应周 |
|---|---|---|---|
| LLM 调用基础 | 上下文窗口、采样参数、tool calling 协议、token 计费 | 把它当"聊天"而不是"受约束的函数调用" | W1–2 |
| 工具系统 | 模型只能看到工具的 name/description/schema，**工具就是你的 API 设计** | 以为写好 prompt 就能弥补烂工具 | W3 |
| 上下文工程 | 模型每次只看得到你塞进去的东西；「塞什么、丢什么、何时压缩」决定成败 | 以为上下文越长越聪明 | W4 |
| 记忆与检索 | 短期靠上下文，长期靠文件/向量库；检索质量 > 模型选择 | 一上来就上向量库，其实 grep 更好用 | W5 |
| 评测与可观测 | 没有评测就没有迭代，只有"感觉变好了" | 靠手感调 prompt，改一处坏一处 | W6 |
| 可靠性 | 重试、幂等、断点恢复、死循环护栏、人审审批门 | 假设模型永远听话、网络永远好 | W7 |
| 安全 | 一切外部内容都是不可信输入（prompt injection）；最小权限 + 沙箱 | 给 Agent 开满权限的 shell | W8 |
| 生态与编排 | MCP 连外部系统、Skill 装知识流程、多 Agent 做隔离 | 无脑多 Agent，成本翻倍效果更差 | W9–10 |
| 产品化 | 异步/流式/并发/限流/成本面板/部署 | 只做 demo，没想过第 100 个用户 | W11–12 |

---

## 2. 12 周逐周计划

### 阶段一（W1–2）地基：Python 够用 + 手写 Agent 循环

| 周 | 学什么 | 交付物 | 验收标准 |
|---|---|---|---|
| **W1** | 环境（Python 已有 3.12；**装 Git for Windows**、VS Code、建 GitHub 账号）；Python 够用清单（见 §3）；跑通并读懂 [week0/agent_loop.py](week0/agent_loop.py) | 改造版 \`agent_loop.py\`：新增 \`grep_repo\` 工具；完成三个练习 A/B/C；首个 GitHub 仓库 | 能说清"工具描述如何改变模型行为"，并用 trace 作为证据 |
| **W2** | tool calling 的 JSON Schema、消息角色、上下文窗口与计费、流式输出、异常处理；把每步落盘成 \`trace.jsonl\` | 带 trace 的 Agent + 一份《10 次任务的失败归因表》 | 连续跑 10 个任务，能把失败归到三类（模型不懂 / 工具不行 / 上下文丢失）之一 |

> 💡 W2 的失败归因表，就是你第一篇文章的素材：**《我让 AI 自己改代码，前 10 次失败了 7 次》**。

### 阶段二（W3–4）工具系统与上下文工程（**最关键的两周**）

| 周 | 学什么 | 交付物 | 验收标准 |
|---|---|---|---|
| **W3** | 工具设计六原则：少而精、返回人类可读、**错误要可行动**、幂等、超时与截断、只读工具可并发；路径沙箱与权限分级 | 工具 v2（5–7 个），每个都有上限和"下一步怎么办"的错误提示 | 人为制造 5 种工具故障，Agent 都能在 3 步内自我纠正 |
| **W4** | 上下文工程：system prompt 分层、历史压缩/摘要、状态外置成文件、子任务隔离、工具结果截断策略；参考 2025–2026 的 **Agent Skills / SKILL.md** 思路（按需加载知识，而不是全塞进 prompt） | 能完成 50+ 步任务的 Agent（例："读完 src/ 全部文件，输出 架构说明.md"） | 上下文超出预算时自动压缩且任务不中断；压缩前后结论一致 |

**这一周要建立的直觉：** 上下文是稀缺资源，删掉无用信息比塞进更多信息更能提升效果。

### 阶段三（W5–6）记忆、检索与评测

| 周 | 学什么 | 交付物 | 验收标准 |
|---|---|---|---|
| **W5** | RAG 实战：切块策略、embedding、关键词+向量混合检索、rerank、**强制引用**、拒答机制 | \`search_codebase\` 工具 + 代码库问答 CLI（输出带 \`文件:行号\`） | 20 个真实问题，人工判分正确率 ≥ 70%，且引用可点开核对 |
| **W6** | 评测体系：30 条 JSONL 用例、自动打分脚本、三指标（成功率 / 平均步数 / 平均成本）、回归流程 | \`eval.py\` + \`scores.csv\` 首版基线 | 改一处 prompt 或工具描述，5 分钟内看到分数涨跌 |

### 阶段四（W7–8）从 Demo 到可靠

| 周 | 学什么 | 交付物 | 验收标准 |
|---|---|---|---|
| **W7** | 重试与幂等、checkpoint 断点恢复、死循环检测、超时与预算熔断、human-in-the-loop 审批门、审计日志 | 失败可安全重跑（不重复副作用）的 Agent | 注入 5 类故障（网络超时/工具返回垃圾/模型胡说/超预算/权限不足）都能优雅收场 |
| **W8** | 安全：prompt injection（网页、README、工具返回值里的指令一律不可信）、最小权限、沙箱、敏感信息脱敏；成本优化（模型路由、缓存、并发、上下文瘦身） | 威胁模型文档 + 防护实现；成本较 W6 基线下降 ≥ 50%（效果不掉） | 构造"恶意 README 要求读取并外传环境变量"的用例，Agent 拒绝执行 |

### 阶段五（W9–10）生态与编排

| 周 | 学什么 | 交付物 | 验收标准 |
|---|---|---|---|
| **W9** | MCP 协议（把你的工具做成 MCP Server）；Agent Skills（把流程和知识写成 SKILL.md）；理解三者边界：**MCP 连外部系统 / Skill 装知识与流程 / CLI 做本地确定性操作** | 开源一个自己的 MCP Server（README 写清安装） | 能在另一个 host（Claude Code / Cursor / DSH 等）里成功调用你自己的工具 |
| **W10** | 编排：LangGraph 状态机 vs 自由循环；subagent 隔离；handoff；ReAct / plan-and-execute / reflection 各自适用边界 | 项目 A 升级为「主 Agent + 检索子 Agent + 校验子 Agent」 | **评测分数更高或成本更低**，否则果断回退——这就是工程判断力的体现 |

### 阶段六（W11–12）产品化与作品集

| 周 | 学什么 | 交付物 | 验收标准 |
|---|---|---|---|
| **W11** | FastAPI 服务化、SSE 流式前端、会话持久化、并发与限流、成本面板、Docker 部署 | 一个别人能打开的在线 Demo | 让一个非技术朋友按 README 在 5 分钟内跑起来 |
| **W12** | 作品集包装：项目 README（问题/方案/评测数据/演示 GIF）、2 篇技术博客、简历 3 条量化条目、面试 12 问自测 | GitHub Profile + 简历 + 面试问答文档 | 能对陌生面试官 5 分钟讲清"我的 Agent 为什么比基线强，证据是什么" |

---

## 3. Python「够用即止」清单

你"会一点 Python"完全够用，**不要先花一个月补 Python**。下面这些边写边补即可：

**现在就要会（2 天突击）**
- \`list / dict / set\` 的增删改查、切片、推导式
- 函数、默认参数、\`*args/**kwargs\`、返回值
- \`class\` 与 \`@dataclass\`、\`self\`
- \`try/except/finally\`、自定义异常
- 文件读写（\`pathlib.Path\`）、\`json\`、\`os.environ\`
- \`pip install\`、\`venv\`（重要：每个项目一个虚拟环境）
- \`argparse\` 写命令行、\`f-string\` 格式化
- \`requests/httpx\` 发 HTTP 请求、\`subprocess.run\`
- \`typing\` 基础标注（\`list[str]\`、\`dict\`、\`Optional\`）
- \`asyncio\` 只会 \`async def\` + \`await\` + \`asyncio.gather\` 即可

**现在完全不用学（会分散你注意力）**
- 装饰器进阶、元类、描述符
- 多进程 / GIL 细节、C 扩展
- Django、爬虫框架、数据科学全家桶
- 复杂设计模式、ABC 抽象基类体系

---

## 4. 三个作品集项目（对应你的三个目标）

| 项目 | 定位 | 用到的周 | 简历/介绍一句话 |
|---|---|---|---|
| **A. CodeAtlas：代码库理解助手** | 工作中落地（也是最好的练手项目） | W1–6 | 基于混合检索的代码库问答 Agent，20 条真实问题集上正确率 82%，平均 4.2 步、单次成本 $0.008 |
| **B. WebPilot：网页/数据自动化 Agent** | 求职主力 | W7–10 | 带审批门与沙箱的浏览器 Agent，通过自建 MCP Server 暴露 9 个工具，可在 Claude Code / DSH 中复用 |
| **C. 垂直小产品**（如"周报生成"/"合同条款检查"/"Excel 报表 Agent"） | 做产品 | W11–12 | 面向 XX 场景的 Agent 产品，含流式 Web UI、成本面板与限流，Docker 一键部署 |

> 三个项目**共用同一个内核**（你在 W1–W8 写的那套 loop + 工具 + 评测），
> 换的只是工具集和场景。所以工作量远小于"从零做三个项目"。

---

## 5. 评测体系最小实现（从 W6 开始，别再手测）

**用例从哪来：** 从你真实的失败里来。每遇到一次失败，就把它变成一条用例，这是最高效的积累方式。

\`\`\`jsonl
{"id": "q001", "task": "src/auth.py 里 token 过期是怎么处理的？", "expect_contains": ["expires_at", "refresh"], "expect_files": ["src/auth.py"], "max_steps": 8}
{"id": "q002", "task": "把所有 TODO 注释汇总成 todos.md", "check": "file_exists:todos.md", "max_steps": 12}
\`\`\`

**三指标（每次改动都记录到 scores.csv）**

| 指标 | 怎么算 | 为什么重要 |
|---|---|---|
| 成功率 | 通过用例数 / 总数 | 唯一的"北极星" |
| 平均步数 | 总步数 / 用例数 | 直接反映工具和上下文质量 |
| 平均成本 | 总 token × 单价 / 用例数 | 产品化的生死线 |

**LLM-as-judge 的三个坑：** ① 判官模型别用被测模型同一版；② rubric 要写死（"必须包含 X 且不得包含 Y"）；③ 每 20 条人工抽检 3 条，防止判官漂移。

> 简历上最有说服力的一行，不是"熟悉 LangGraph"，而是
> **"通过工具描述重构 + 上下文压缩，把评测成功率从 41% 提升到 78%，单次成本下降 76%"**。

---

## 6. 求职转化

**简历怎么写（量化优先）**
- ❌ "熟悉 LLM Agent 开发，了解 RAG"
- ✅ "自研代码库问答 Agent（Python，2000 行）：混合检索 + 强制引用，20 题评估集正确率 82%；引入上下文压缩后平均成本从 $0.031 降至 $0.008；已开源 MCP Server（GitHub 120 star）"

**面试高频 12 问（W12 前必须能答）**
1. Agent 和 workflow 的区别？什么时候该用哪个？
2. 上下文快满了你怎么办？（压缩策略 / 子任务隔离 / 状态外置）
3. 怎么防止 Agent 死循环和烧钱？
4. 工具设计有哪些原则？工具报错时你会返回什么给模型？
5. 你的评测集怎么建的？指标是什么？怎么防止过拟合评测集？
6. 怎么防 prompt injection？工具返回值里带指令怎么办？
7. 多 Agent 相比单 Agent 的收益和代价？
8. 怎么降低成本和延迟？（缓存/模型路由/并行/上下文瘦身）
9. 长任务失败了怎么恢复？（checkpoint / 幂等）
10. RAG 检索不准怎么排查？（召回 vs 排序 vs 切块 vs 引用）
11. 你怎么做人工审批门？哪些操作必须审？
12. 讲讲你踩过最大的一个坑，怎么解决的？（准备一个 3 分钟的故事）

**开源与影响力（求职杠杆最大的一件事）**
把你 W9 写的 MCP Server 或 Skill 开源；写 2 篇博客（一篇踩坑、一篇评测方法论）；在 GitHub Profile 上放演示 GIF。
**目标岗位关键词：** Agent Engineer / LLM 应用工程师 / AI 产品工程师 / AI 解决方案工程师。

---

## 7. 落地到工作的 3 个切入点

1. **选"高频、低风险、有明确对错"的任务**：日志排查、周报汇总、测试用例补全、数据报表生成——别一上来碰钱和客户数据。
2. **先做内部工具，再谈流程替换**：让同事用起来，收集失败案例，这些案例就是你的评测集。
3. **量化收益**：省了多少人时、错误率变化、覆盖了多少场景。**没有度量，就没有预算。**

---

## 8. 2026 年的坑（按踩坑概率排序）

1. **无脑多 Agent**：多数任务单 Agent + 好工具更强；多 Agent 的价值在"上下文隔离"和"权限隔离"，不在于"人多力量大"。
2. **没有评测**：你会陷入"改 A 坏 B"的无限循环，且无法说服任何人。
3. **工具返回信息不友好**：模型看到的只有工具返回值，返回一坨 JSON 就是逼它猜。
4. **上下文腐化**：把 10 万 token 的日志全塞进去，模型反而更笨。
5. **只追框架/新概念**：Skill、MCP、CLI 是三种工具形态，不是三个宗教；按场景选（Skill 装知识流程 / MCP 连外部系统 / CLI 做本地确定性操作）。
6. **权限过宽**：给 Agent 一个 unrestricted shell，第一天就会删掉你的东西。
7. **成本失控**：没有 token 预算和熔断，一次死循环能烧掉一顿饭钱。
8. **只做 Demo 不做产品化**：没有并发、限流、流式、失败恢复，第 100 个用户就会打垮它。

---

## 9. 资源清单（够用就好，别囤）

**必读 6 篇**
- Anthropic《Building Effective Agents》—— https://www.anthropic.com/engineering/building-effective-agents
- Anthropic《Effective context engineering for AI agents》—— https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Lilian Weng《LLM Powered Autonomous Agents》—— https://lilianweng.github.io/posts/2023-06-23-agent/
- MCP 官方文档 —— https://modelcontextprotocol.io/
- DeepSeek API 文档 —— https://api-docs.deepseek.com/
- LangGraph 文档（W10 再看）—— https://langchain-ai.github.io/langgraph/

**论文（W4 之后每周一篇，只读方法和实验结论）**
ReAct (arXiv:2210.03629) · Reflexion (2303.11366) · Toolformer (2302.04761) · SWE-agent (2405.15793) · Generative Agents (2304.03442) · τ-bench (2406.12045) · GAIA (2311.12983)

**协议与生态（2025–2026 现状）**
Model Context Protocol（连外部系统）· Agent Skills / SKILL.md 规范（装知识与流程，已被多家 Agent 框架支持）· 主流宿主：Claude Code、Cursor、Codex、Gemini CLI、DSH

**读源码（每周 1 小时，收益极高）**
OpenHands · SWE-agent · Aider · Cline · LangGraph 官方 examples · **以及你正在用的 DSH harness**（本机 \`D:\dshharness\resources\app.asar\dsh\\\`）——读它的主循环、工具定义、上下文压缩、沙箱审批，比读任何教程都实在。

**课程**
DeepLearning.AI 短课 —— https://www.deeplearning.ai/short-courses/ · Hugging Face Agents Course —— https://huggingface.co/learn/agents-course

---

## 10. 打卡表（打印出来，做完打勾）

- [ ] W1　读懂 agent_loop.py + 练习 A/B/C + 建 GitHub 仓库 + 装 Git
- [ ] W2　trace.jsonl + 10 次任务失败归因表
- [ ] W3　工具 v2（5–7 个，含可行动错误）+ 故障注入测试
- [ ] W4　50 步长任务不崩 + 上下文压缩
- [ ] W5　代码库问答 CLI（带引用）
- [ ] W6　eval.py + 首版基线分数（成功率/步数/成本）
- [ ] W7　故障恢复 + 审批门
- [ ] W8　注入防护用例通过 + 成本下降 ≥ 50%
- [ ] W9　开源自己的 MCP Server
- [ ] W10　多 Agent 改造（有数据支撑才保留）
- [ ] W11　在线 Demo + Docker 部署
- [ ] W12　作品集 + 简历 + 面试 12 问

---

### 现在（今天）就做的三件事
1. \`python -m pip install openai\`，设置 \`DEEPSEEK_API_KEY\`，跑通 [week0/agent_loop.py](week0/agent_loop.py)。
2. 装 Git for Windows，注册 GitHub，把 \`agent-dev-plan\` 提交上去（**今天就建立提交习惯**）。
3. 每天结束前写 3 行 TIL 笔记：今天做了什么、卡在哪、明天第一步做什么。

> 说明：文档中的 github.com / huggingface.co 链接在本机沙箱内被网络策略拦截，未能逐一校验可达性；
> anthropic.com、modelcontextprotocol.io、arxiv.org、deeplearning.ai、langchain-ai.github.io 的链接已实测可访问。
