import subprocess
import time
import urllib.request
from pathlib import Path
from permissions import WORKSPACE, resovle_in_workspace

from mpmath import chebyt

MAX_OUTPUT = 8000  # 工具返回给模型的最大字符数
TOOLS = {}


def tool(name, description, parameters):
    """装饰器： 把一个函数注册为工具"""

    def decorator(func):
        TOOLS[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
            "func": func,
        }
        return func

    return decorator


def get_schemas():
    """返回给模型看的工具说明书"""
    return [t["schema"] for t in TOOLS.values()]


def _params(**props):
    """简写：所有参数都是必填的字符串"""
    return {
        "type": "object",
        "properties": {
            k: {"type": "string", "description": v} for k, v in props.items()
        },
        "required": list(props),
    }


@tool(
    "list_dir", "列出某个目录下的文件和子目录。", _params(path="目录路径，当前目录写 .")
)
def list_dir(path="."):
    p = resovle_in_workspace(path)
    if p is None:
        return "[错误] 路径在工作区之外"
    return (
        "\n".join(sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir()))
        or "(空目录)"
    )


@tool("read_file", "读取一个文本文件的内容。", _params(path="文件路径"))
def read_file(path):
    p = resovle_in_workspace(path)
    if p is None:
        return "[错误] 路径在工作区之外"
    return p.read_text(encoding="utf-8")


@tool(
    "write_file",
    "把内容写入文件，已存在则覆盖，目录不存在会自动创建。",
    _params(path="文件路径", content="要写入的完整内容"),
)
def write_file(path, content):
    p = resovle_in_workspace(path)
    if p is None:
        return "[错误] 路径在工作区之外"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"已写入 {path}（{len(content)} 字符）"


@tool(
    "edit_file",
    "修改指定文件内容，必须同时传入 new, old",
    _params(path="修改文件的路径", new_text="新的内容", old_text="需要修改的内容"),
)
# def edit_file(path: str, new_text: str, old_text: str):
#
#     if not old_text:
#         raise ValueError("旧内容不能为空")
#
#     p = Path(path)
#
#     content = p.read_bytes()
#     old = old_text.encode("utf-8")
#     new = new_text.encode("utf-8")
#
#     position = content.find(old)
#     if position == -1:
#         return f"{path}路径的文件，不存在 {old} 内容"
#
#     if content.find(old, position + 1) != -1:
#         return f"{path}路径的文件，存在多个 {old} 内容， 请给出更长的原文"
#     content = content.replace(old, new, 1)
#     p.write_bytes(content)
#
#     return f"已写入 {path}（{len(new)} 字符）"


@tool(
    "run_shell",
    "在当前目录执行一条 shell 命令，返回退出码、标准输出和错误输出。",
    _params(command="要执行的命令"),
)
def run_shell(command, timeout=30):
    try:
        p = subprocess.run(command, shell=True, cwd=WORKSPACE, capture_output=True, text=True, timeout=timeout)

    except subprocess.TimeoutExpired:
        return f"[超时] 命令执行超过{timeout}秒，已终止。"

    return f"[exit {p.returncode}]\n{p.stdout}{p.stderr}"


@tool(
    "fetch_url",
    "抓取一个网页或接口的文本内容。url 必须以 http 或 https 开头。",
    _params(url="完整的 URL"),
)
def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "nami-agent"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


@tool(
    "get_time",
    "获取当前时间, 支持返回的格式",
    _params(fmt="时间格式，例如 %Y-%m-%d %H:%M:%S"),
)
def get_time(fmt: str):
    return time.strftime(fmt, time.localtime())


def execute(name, args):
    """执行工具，永远返回字符串，永远不抛异常"""
    if name not in TOOLS:
        return f"Error: 不存在工具 ‘{name}‘，可用工具：{','.join(TOOLS)}"

    try:
        result = str(TOOLS[name]["func"](**args))
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

    if len(result) > MAX_OUTPUT:
        result = result[:MAX_OUTPUT] + f"\n ...(已截断，共 {len(result)} 字符)"

    return result
