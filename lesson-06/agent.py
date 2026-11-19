import json
import os

import skills
from context import (
    clear_old_tool_results,
    compact,
    load_session,
    save_session,
    truncate_tool_result,
)
from dotenv import load_dotenv
from openai import OpenAI
from permissions import PermissionManager
from tools import execute, get_schemas

load_dotenv()


# SOFT_LIMIT = 3000 # 超过：清理旧工具结果
# HARD_LIMIT = 6000 # 超过： 简要压缩
SOFT_LIMIT = 16000  # 超过：清理旧工具结果
HARD_LIMIT = 24000  # 超过： 简要压缩


usage = {"prompt_tokens": 0}  # 上一次调用的真实 token 数


client = OpenAI(
    api_key=os.environ.get("API_KEY"),
    base_url=os.environ.get("BASE_URL"),
)

pems = PermissionManager()

MODEL = "workbuddy-ai/hy4flash-free"
MAX_STEPS = 20  # 放置模型陷入死循环

BASE_SYSTEM = (
    "你是一个能使用工具的助手，在用户当前目录下完成任务。"
    "必要时调用工具，完成后用简洁的语言汇报结果。"
)


class Session:
    """一个会话 = 一份 messages + 一个权限管理器 + 上一次 token 数"""

    def __init__(self, name, ask=None, persist=True) -> None:
        self.name = name
        self.persist = persist
        saved = load_session(name) if persist else None
        self.messages = saved or [{"role": "system", "content": ""}]
        self.messages[0] = {
            "role": "system",
            "content": build_system(),
        }  # 每次使用最新的技能
        self.perms = PermissionManager(ask=ask)
        self.prompt_tokens = 0

    def save(self):
        if self.persist:
            save_session(self.name, self.messages)


def build_system():
    return BASE_SYSTEM + skills.project_notes() + skills.skills_section()


def make_client():
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ.get("API_KEY"),
        base_url=os.environ.get("BASE_URL"),
    )


def handle_call(call, perms):
    """解析参数 -> 权限检查 -> 执行。永远返回字符串"""
    name = call.function.name
    try:
        args = json.loads(call.function.arguments or "{}")

    except json.JSONDecodeError:
        return "Error: 参数不是合法的 JSON"

    decision = perms.check(name, args)
    if not decision.allowed:
        return f"[权限拒绝]{decision.reason}"  # 拒绝原因也要回传，让模型换条路
    return execute(name, args)


def run(session, user_input, client, model=MODEL, log=print):
    messages = session.messages
    messages.append({"role": "user", "content": user_input})

    for _ in range(MAX_STEPS):
        # 用上一次调用的真实 token 数，决定这一轮是否需要处理
        if session.prompt_tokens > HARD_LIMIT:
            messages[:] = compact(client, model, messages)

        elif session.prompt_tokens > SOFT_LIMIT:
            clear_old_tool_results(messages)

        resp = client.chat.completions.create(
            model=model, messages=messages, tools=get_schemas()
        )
        session.prompt_tokens = resp.usage.prompt_tokens if resp.usage else 0
        print(f"   [prompt_tokens={usage['prompt_tokens']}]")

        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        # 没有工具调用，说明模型给出了最终回答
        if not msg.tool_calls:
            return msg.content or ""

        # 模型可能一轮请求多个工具，每个都必须回应
        for call in msg.tool_calls:
            name = call.function.name
            print(f"🔧 {name}({call.function.arguments[:80]})")
            result = handle_call(call, pems)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": truncate_tool_result(result),
                }
            )

    return "(达到最大步数，已停止)"


def main():
    clinet = make_client()
    session = Session("default")
    while True:
        q = input("你> ").strip()
        if q in ("exit", "quit"):
            break
        print("\n" + run(session, q, clinet) + "\n")
        session.save()

if __name__ == "__main__":
    main()
