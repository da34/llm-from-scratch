import json
import os

from openai import OpenAI
from tools import execute, get_schemas
from permissions import PermissionManager
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("API_KEY"),
    base_url=os.environ.get("BASE_URL"),
)

pems = PermissionManager()

MODEL = "deepseek/deepseek-flash"
MAX_STEPS = 20  # 放置模型陷入死循环

SYSTEM = (
    "你是一个能使用工具的助手，在用户当前目录下完成任务。"
    "必要时调用工具，完成后用简洁的语言汇报结果。"
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
        return f"[权限拒绝]{decision.reason}" # 拒绝原因也要回传，让模型换条路
    return execute(name, args)

def run(user_input, messages):
    messages.append({"role": "user", "content": user_input})


    for _ in range(MAX_STEPS):
        with client.chat.completions.stream(
            model=MODEL, messages=messages, tools=get_schemas()
        ) as stream:
            for event in stream:
                if event.type == "content.delta":
                    print(event.delta, end="", flush=True)
            msg = stream.get_final_completion().choices[0].message

        if msg.content:
            print()

        messages.append(msg.model_dump(exclude_none=True))

        # 没有工具调用，说明模型给出了最终回答
        if not msg.tool_calls:
            return msg.content or ""


        # 模型可能一轮请求多个工具，每个都必须回应
        for call in msg.tool_calls:
            name = call.function.name
            print(f"🔧 {name}({call.function.arguments[:80]})")
            result = handle_call(call, pems)

            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    print("(达到最大步数，已停止)")
    return "(达到最大步数，已停止)"

if __name__ == "__main__":
    messages = [{"role": "system", "content": SYSTEM}]
    while True:
        q = input("你> ").strip()
        if q in ("exit", "quit"):
            break
        print()
        run(q, messages)
        print()
