import subprocess
import json
from openai import OpenAI
from sympy.utilities.iterables import capture
import sys
import os


client = OpenAI(
    api_key=os.environ.get("API_KEY", "test"),
    base_url=os.environ.get("BASE_URL", "http://127.0.0.1:3425"),
)

MODEL = os.environ.get("MODEL", "commandcode-plan/deepseek/deepseek-v4.1-flash-fast")
MAX_STEPS = 20  # 防止死循环：Agent 最多转 20 圈


SYSTEM = (
    "你是一个能操作本地文件和命令行的编程助手。"
    "需要时调用工具，完成任务后直接用文字总结，不要再调用工具。"
)

def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入{path}（{len(content)}）字符"


def run_shell(command: str) -> str:
    # 先用最简单的规则，每次都需要人工确认
    if input(f"\n[需要确认] 执行命令：{command}\n允许？(y/n) ").strip().lower() != "y":
        return "用户拒绝执行该命令"
    try:
        p = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        return f"命令超时（60秒）"
    return (p.stdout + p.stderr)[-4000:] or "无输出"  # 阶段避免撑爆上下文


TOOL_FUNCS = {"read_file": read_file, "write_file": write_file, "run_shell": run_shell}


def _tool(name, desc, props):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": {
                    k: {"type": "string", "description": v} for k, v in props.items()
                },
                "required": list(props),
            },
        },
    }

TOOLS = [
    _tool("read_file", "读取文件内容", {"path": "文件路径"}),
    _tool("write_file", "写入文件（覆盖）", {"path": "文件路径", "content": "完整文件内容"}),
    _tool("run_shell", "执行 shell 命令并返回输出", {"command": "要执行的命令"}),
]


def run(task: str) -> None:
    messages = [
        { "role": "system", "content": SYSTEM },
        { "role": "user", "content": task }
    ]

    for step in range(1, MAX_STEPS + 1):
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        # 模型没有调用工具 = 认为任务结束了，循环退出
        if not msg.tool_calls:
            print(f"\n完成，共{step}步，\n{msg.content}")
            return

        # 模型要调用工具, 执行， 并把结果 作为 tool 添加到 message
        for call in msg.tool_calls:
            name = call.function.name
            print(f"第【{step}步】 {name}（{call.function.arguments[:80]}）")

            try:
                args = json.loads(call.function.arguments)
                result = TOOL_FUNCS[name](**args)

            except Exception as e: # 工具出错，也要告诉模型，让它去修正
                result = f"工具执行出错{type(e).__name__}:{e}"
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    print(f"\n 达到{MAX_STEPS}步上限，已停止")




if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('用法：python agent.py "你的任务"')
    run(sys.argv[1])
