import json
import os
from pathlib import Path

MAX_TOOL_CHARS = 4000           # 单个工具结果最多保留的字符数
KEEP_PECENT_TOOL_RESULT = 3     # 清理时，保留最近几条工具的结果
KEEP_LAST_TURNS = 2             # 压缩时，原样保留最近几轮用户对话


# 程序自己的状态

STATE_DIR = Path(os.environ.get("MAIN_STATE_DIR", Path.home() / ".yj-agent"))
SESSION_DIR = STATE_DIR / "session"


PLACEHOLDER = "[旧工具结果已清理，如需要请重新调用工具]"

SUMMARY_PROMPT = """你是对话摘要器。把下面这段 Agent 的历史对话压缩成摘要，要求：
1. 保留：用户的目标、已完成的步骤、关键结论、重要的文件路径和参数、尚未解决的问题
2. 丢弃：寒暄、重复内容、工具返回的大段原文
3. 用简洁的条目写，不要超过 500 字
只输出摘要本身。"""


def truncate_tool_result(text, limit=MAX_TOOL_CHARS):
    if len(text) <= limit:
        return text

    half = limit // 2
    return f"{text[:half]}\n...[中间省略 {len(text) - limit} 字符]...\n{text[-half:]}"


def clear_old_tool_results(messages, keep=KEEP_PECENT_TOOL_RESULT):
    tool_idx = [i for i,m in enumerate(messages) if m["role"] == "tool"]
    old = tool_idx[:-keep] if keep > 0 else tool_idx

    for i in old:
        messages[i]["content"] = PLACEHOLDER
