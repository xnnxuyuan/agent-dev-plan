# Week 0–1：跑通你自己的第一个 Agent（约 200 行，零框架）

这个目录里只有一个文件：\`agent_loop.py\`。它不依赖 LangChain / LangGraph / 任何 Agent 框架，
只用 \`openai\` 这个 SDK 调一个 OpenAI 兼容接口，就把「LLM + 工具 + 循环 + 上下文」这四件事全做完了。

**为什么先手写：** Agent 的全部秘密就是 \`run()\` 里那个 while 循环。框架把它藏起来，
你就失去了排查"它为什么不听我话"的能力。先手写一遍，之后用任何框架都是降维打击。

---

## 1. 装环境（10 分钟，只做一次）

\`\`\`powershell
# 1) 装依赖（你机器上已有 Python 3.12 + pip 25）
python -m pip install openai

# 2) 配 API Key（DeepSeek 的 Key 在 https://platform.deepseek.com 申请）
#    临时生效（只对当前窗口有效）：
$env:DEEPSEEK_API_KEY = "sk-你的key"

# 3) 想永久生效就写进用户环境变量：
[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-你的key", "User")
\`\`\`

> 你机器上 **还没有装 Git**（第 1 周必须装上：https://git-scm.com/download/win ），
> 因为从第 1 周开始你所有的产出都要提交到 GitHub，它是你的作品集。

## 2. 跑起来

\`\`\`powershell
cd D:\deepseekwork\agent-dev-plan\week0

# 第一个任务（务必先跑这个，看它怎么循环）
python agent_loop.py "列出当前目录有哪些文件，把结果写进 report.md"

# 观察这几件事：
#   - 它先调 list_dir，还是直接 write_file？
#   - 它写完有没有回过头验证？
#   - 一共用了几步？有没有多余调用？

# 放开 shell 审批（危险开关，只在本地玩）
python agent_loop.py --auto "统计当前目录下 .py 文件的数量和总行数，输出表格"
\`\`\`

每次运行都会往 \`trace.jsonl\` 追加每一步的工具名、参数、结果和 token 消耗——**这就是你未来的
可观测性系统的雏形**，第 2 周你要正式读它来复盘失败原因。

## 3. 第 1 周的三个必做练习（做完才算过关）

### 练习 A：加一个自己的工具（体会"工具即接口"）
加一个 \`grep_repo(keyword, path)\` 工具：在指定目录下递归搜索关键词，返回 \`文件:行号: 内容\`，最多 50 条。
要通过工具的 \`description\` 让模型知道**什么时候该用它**（而不是用 run_shell 去 grep）。

### 练习 B：故意把工具描述写坏（体会"描述决定行为"）
把 \`read_file\` 的 description 改成 \`"读取文件"\`（删掉所有使用说明），重跑同样的任务，
记录成功率/步数的变化。**这是你第一次亲手证明：工具描述比 prompt 咒语更重要。**

### 练习 C：把步数上限调到 3（体会"约束即设计"）
\`python agent_loop.py --max-steps 3 "..."\`，观察它在被截断时是否给出了有意义的中间结论。
然后想清楚：真实产品里步数上限、超时、token 预算分别该设多少？

## 4. 验收标准（第 1 周末自测）

- [ ] 能用自己的话解释：为什么工具报错要"回灌给模型"而不是抛异常？
- [ ] 能说出 3 个防止 agent 无限循环/烧钱的手段
- [ ] 练习 A/B/C 全部跑过，并有 trace.jsonl 作为证据
- [ ] 能把项目提交到 GitHub（第 1 周就得建仓库，别再拖）

## 5. 常见报错

| 现象 | 原因 | 解决 |
|---|---|---|
| \`未找到 API Key\` | 环境变量没设或换了窗口 | 重新 \`$env:DEEPSEEK_API_KEY=...\` |
| \`401 / Authentication Fails\` | Key 错、余额不足 | 到平台确认 Key 和余额 |
| 模型反复调同一个工具 | 工具返回的信息没用，或描述含糊 | 看 trace，改工具的返回内容（要含"下一步该怎么办"） |
| 任务跑一半就到步数上限 | 任务太大 | 把任务拆小，或先让它"只做调研、不要动手" |
| 中文显示乱码 | 控制台编码不是 UTF-8 | `chcp 65001` 后设置 `$env:PYTHONUTF8=1` 再运行 |
| \`参数不正确\` | 模型给的 JSON 不符合 schema | 简化参数、给参数加示例（\`description\` 里写例子） |
