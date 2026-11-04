
import subprocess

from sympy.utilities.iterables import capture


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_file (path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入{path}（{len(content)}）字符"

def run_shell(command: str) -> str:
    # 先用最简单的规则，每次都需要人工确认
    if input(f"\n[需要确认] 执行命令：{command}\n允许？(y/n) ").strip().lower() != "y":
           return "用户拒绝执行该命令"
    try:
         p = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return f"命令超时（60秒）"
    return (p.stdout + p.stderr)[-4000:] or "无输出" # 阶段避免撑爆上下文


TOOL_FUNCS = {"read_file": read_file, "write_file": write_file, "run_shell": run_shell}
