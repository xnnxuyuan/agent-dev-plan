#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
week0/agent_loop.py —— 从零手写的最小 Agent 循环（零框架，约 200 行）
它只做四件事：
  1. 把「系统提示 + 用户任务 + 历史」发给模型
  2. 模型说要用哪个工具，就执行哪个工具
  3. 把工具结果塞回历史，再问模型
  4. 模型不再调用工具时，输出最终答案

为什么先手写、不要一上来用框架：
  Agent 的全部秘密就在下面 run() 的 while 循环里。框架只是把这个循环
  包装得更花哨，但把它藏起来之后，你会失去排查问题的能力。

学习重点（第 1 周的任务）：
  - 工具的 description / 参数说明就是给模型看的"说明书"，改它往往比改 prompt 更有效
  - 每一步都要有上限：步数、超时、输出长度、token 预算
  - 工具报错不要把异常抛给用户，而要把「可读的错误 + 怎么改」回灌给模型
  - 危险操作（shell 命令）要有人工审批门

运行：
  pip install openai
  $env:DEEPSEEK_API_KEY = "sk-xxxx"          # PowerShell
  python agent_loop.py "统计当前目录下有多少个 .py 文件，把结果写进 report.md"
  python agent_loop.py --auto "把 README.md 里的 TODO 全部列出来"
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 中文 Windows 的控制台是 GBK，模型偶尔会返回 emoji / 生僻字，
# 这里把编码错误降级成替换字符，避免脚本因为一个字符直接崩溃。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

# ----------------------------------------------------------------------------
# 0. 配置：全部可被环境变量覆盖，方便做实验
# ----------------------------------------------------------------------------
WORKDIR = Path(os.environ.get("AGENT_WORKDIR", ".")).resolve()
MODEL = os.environ.get("AGENT_MODEL", "deepseek-chat")
BASE_URL = os.environ.get("AGENT_BASE_URL", "https://api.deepseek.com")
API_KEY_ENV = os.environ.get("AGENT_API_KEY_ENV", "DEEPSEEK_API_KEY")

MAX_STEPS = 15            # 步数上限：防止无限循环烧钱
MAX_TOOL_CHARS = 4000     # 单次工具结果回灌上限：防止上下文爆炸
MAX_READ_LINES = 400      # 单次读取行数上限
SHELL_TIMEOUT = 60        # shell 命令超时（秒）

AUTO_APPROVE = False      # --auto 时置 True：跳过 shell 审批（仅测试用）
TRACE_PATH = Path("trace.jsonl")

SYSTEM_PROMPT = f"""你是一个能操作本地文件和命令行的编程助手。

当前工作目录：{WORKDIR}
可用工具：list_dir / read_file / write_file / run_shell

工作规则：
1. 先看清现状再动手：不确定就先 list_dir 或 read_file。
2. 一次只做一小步；改完文件要用 read_file 或 run_shell 验证结果。
3. 工具返回错误时，读懂错误信息再换一种做法，不要重复提交同样的调用。
4. 不要臆造文件内容；没看过的文件不要假设它长什么样。
5. 任务完成后，用一段话总结：你做了什么、验证结果如何、还有什么遗留问题。
"""

# ----------------------------------------------------------------------------
# 1. 工具定义：这部分是给「模型」看的，不是给你看的
#    —— 模型只能看到 name / description / parameters，所以这三个字段就是全部
# ----------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "列出目录下的一层文件和子目录，带大小。用来了解项目结构。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作目录的目录路径，默认 '.'"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文本文件内容，返回带行号的文本。单次最多返回 400 行；大文件请分段读。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作目录的文件路径"},
                    "offset": {"type": "integer", "description": "从第几行开始读（1 起），默认 1"},
                    "limit": {"type": "integer", "description": "最多读多少行，默认 400"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "把内容写入文件（整文件覆盖）。父目录不存在会自动创建。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作目录的文件路径"},
                    "content": {"type": "string", "description": "要写入的完整内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "在工作目录下执行一条 PowerShell 命令并返回输出。用于运行测试、统计、查看 git 状态等。不要用它做破坏性操作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的 PowerShell 命令"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_repo",
            "description": "在目录下递归搜索文本关键词，返回 文件:行号: 内容 列表，最多 50 条。"
                           "适合按内容找函数定义、配置项、报错关键词等场景；"
                           "当需要按内容搜索而不是按文件名查找时用它，不要用 run_shell 去执行 grep。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "要搜索的关键词（不区分大小写）"},
                    "path": {"type": "string", "description": "相对工作目录的目录路径，默认 '.'"},
                },
                "required": ["keyword"],
            },
        },
    },
]


# ----------------------------------------------------------------------------
# 2. 工具实现：注意每个工具都必须「有上限、有可读错误」
# ----------------------------------------------------------------------------
def safe_path(raw: str) -> Path:
    """把模型给的路径锁在工作目录内。这是最小版的沙箱。"""
    p = Path(raw)
    target = (WORKDIR / p).resolve() if not p.is_absolute() else p.resolve()
    if target != WORKDIR and WORKDIR not in target.parents:
        raise ValueError(f"拒绝访问工作目录之外的路径：{target}")
    return target


def tool_list_dir(path: str = ".") -> str:
    target = safe_path(path)
    if not target.exists():
        return f"错误：目录不存在：{path}。可以先用 list_dir('.') 看看有哪些目录。"
    if not target.is_dir():
        return f"错误：{path} 不是目录，是文件。请用 read_file 读取它。"
    entries = sorted(target.iterdir(), key=lambda x: (x.is_file(), x.name))[:200]
    lines = []
    for e in entries:
        if e.is_dir():
            lines.append(f"[DIR ] {e.name}/")
        else:
            lines.append(f"[FILE] {e.name}  ({e.stat().st_size} bytes)")
    return "\n".join(lines) or "（空目录）"


def tool_read_file(path: str, offset: int = 1, limit: int = MAX_READ_LINES) -> str:
    target = safe_path(path)
    if not target.exists():
        return f"错误：文件不存在：{path}。可以用 list_dir 确认文件名。"
    if target.is_dir():
        return f"错误：{path} 是目录。请用 list_dir。"
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # 读不动就告诉模型换策略，而不是崩掉
        return f"错误：读取失败（{exc}）。文件可能是二进制，请换其他方式。"
    lines = text.splitlines()
    limit = max(1, min(int(limit), MAX_READ_LINES))
    start = max(1, int(offset))
    chunk = lines[start - 1: start - 1 + limit]
    head = f"（共 {len(lines)} 行，本次显示第 {start}-{start + len(chunk) - 1} 行）\n"
    body = "\n".join(f"{i:>5}| {t}" for i, t in enumerate(chunk, start=start))
    return head + body


def tool_write_file(path: str, content: str) -> str:
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"已写入 {target.relative_to(WORKDIR)}（{len(content)} 字符）。建议用 read_file 复核一遍。"


def tool_run_shell(command: str) -> str:
    if not AUTO_APPROVE:
        print(f"\n  [需要你批准] 即将执行：{command}")
        answer = input("  执行吗？(y/N) ").strip().lower()
        if answer != "y":
            return "用户拒绝了这条命令。请不要重试同一条命令，改为向用户说明你想做什么、为什么需要它。"
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            cwd=WORKDIR, capture_output=True, text=True,
            timeout=SHELL_TIMEOUT, encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return f"错误：命令超过 {SHELL_TIMEOUT} 秒未结束，已终止。请换一条更快或更精确的命令。"
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    text = f"exit_code={proc.returncode}\nSTDOUT:\n{out}"
    if err:
        text += f"\nSTDERR:\n{err}"
    return text or f"exit_code={proc.returncode}（无输出）"


def tool_grep_repo(keyword: str, path: str = ".") -> str:
    """递归搜索目录下的文本文件，返回 文件:行号: 内容，最多 50 条。"""
    target = safe_path(path)
    if not target.exists():
        return f"错误：目录不存在：{path}。可以先用 list_dir('.') 看看有哪些目录。"
    if not target.is_dir():
        return f"错误：{path} 不是目录，是文件。grep_repo 只搜索目录。"

    keyword_l = keyword.lower()
    hits: list[str] = []
    scanned = 0
    for p in target.rglob("*"):
        if not p.is_file():
            continue
        if p.stat().st_size > 1024 * 1024:  # 跳过超大文件，避免读爆内存
            continue
        scanned += 1
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            if keyword_l in line.lower():
                hits.append(f"{p.relative_to(WORKDIR)}:{i}: {line.strip()[:200]}")
                if len(hits) >= 50:
                    break
        if len(hits) >= 50:
            break

    if not hits:
        return f"在 {path} 下共扫描 {scanned} 个文本文件，未找到包含「{keyword}」的行。"
    return f"共找到 {len(hits)} 条（上限 50），扫描 {scanned} 个文本文件：\n" + "\n".join(hits)


DISPATCH = {
    "list_dir": tool_list_dir,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "run_shell": tool_run_shell,
    "grep_repo": tool_grep_repo,
}


def execute_tool(name: str, args: dict) -> str:
    """统一入口：任何工具异常都变成「模型能读懂的文本」，而不是崩溃。"""
    fn = DISPATCH.get(name)
    if fn is None:
        return f"错误：没有名为 {name} 的工具。可用工具：{', '.join(DISPATCH)}"
    try:
        result = fn(**args)
    except TypeError as exc:
        return f"错误：参数不正确（{exc}）。请对照工具的参数说明重新调用。"
    except Exception as exc:
        return f"错误：工具 {name} 执行失败（{type(exc).__name__}: {exc}）"
    if len(result) > MAX_TOOL_CHARS:
        result = result[:MAX_TOOL_CHARS] + f"\n…（输出过长已截断，共 {len(result)} 字符）"
    return result


# ----------------------------------------------------------------------------
# 3. 主循环：Agent 的全部秘密都在这 30 行里
# ----------------------------------------------------------------------------
def run(task: str, max_steps: int) -> None:
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("缺少依赖：请先运行  pip install openai")

    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        sys.exit(f"未找到 API Key：请先设置环境变量 {API_KEY_ENV}（PowerShell: $env:{API_KEY_ENV}='sk-xxx'）")

    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    call_counts: dict[str, int] = {}
    trace_file = TRACE_PATH.open("a", encoding="utf-8")
    started = time.time()
    tokens_in = tokens_out = 0

    print(f"\n任务：{task}\n工作目录：{WORKDIR}\n模型：{MODEL}\n" + "-" * 60)

    for step in range(1, max_steps + 1):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, temperature=0.2,
        )
        usage = getattr(resp, "usage", None)
        if usage:
            tokens_in += usage.prompt_tokens or 0
            tokens_out += usage.completion_tokens or 0
        msg = resp.choices[0].message
        tool_calls = list(msg.tool_calls or [])

        if msg.content:
            print(f"\n[{step}] 模型：{msg.content.strip()}")

        # 没有工具调用 => 模型认为任务结束
        if not tool_calls:
            print("-" * 60)
            print(f"完成，共 {step} 步，用时 {time.time() - started:.1f}s，"
                  f"tokens: 输入 {tokens_in} / 输出 {tokens_out}")
            trace_file.close()
            return

        assistant_msg: dict = {"role": "assistant", "content": msg.content or ""}
        if tool_calls:
            assistant_msg["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls
            ]
        messages.append(assistant_msg)

        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                result = "错误：你的参数不是合法 JSON，请重新调用并确保参数是合法 JSON。"
                args = {}
            else:
                signature = json.dumps({"n": name, "a": args}, ensure_ascii=False, sort_keys=True)
                call_counts[signature] = call_counts.get(signature, 0) + 1
                if call_counts[signature] >= 3:
                    # 死循环护栏：同样的一次调用出现 3 次，就不再执行
                    result = ("【系统提醒】你已经连续 3 次提交完全相同的调用。"
                              "这条路走不通，请换一种做法，或者直接告诉用户你卡在哪里。")
                else:
                    print(f"\n[{step}] 调用 {name}({json.dumps(args, ensure_ascii=False)[:200]})")
                    result = execute_tool(name, args)
                    print("     -> " + result.replace("\n", "\n     ")[:600])

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            trace_file.write(json.dumps(
                {"step": step, "tool": name, "args": args, "result": result,
                 "tokens_in": tokens_in, "tokens_out": tokens_out}, ensure_ascii=False) + "\n")
            trace_file.flush()

    print("-" * 60)
    print(f"达到步数上限 {max_steps} 步仍未完成。tokens: 输入 {tokens_in} / 输出 {tokens_out}")
    print("排查建议：看 trace.jsonl，判断是「工具不好用」「任务太大」还是「模型绕圈」。")
    trace_file.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="最小可用的手写 Agent 循环")
    parser.add_argument("task", help="交给 agent 的自然语言任务")
    parser.add_argument("--auto", action="store_true", help="自动批准所有 shell 命令（危险，仅本地测试用）")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS, help=f"步数上限，默认 {MAX_STEPS}")
    args = parser.parse_args()

    global AUTO_APPROVE
    AUTO_APPROVE = args.auto
    run(args.task, args.max_steps)


if __name__ == "__main__":
    main()
