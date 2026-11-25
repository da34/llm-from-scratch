import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from context import STATE_DIR   # 第 4 课定义的状态目录，在工作区之外，Agent 不能直接改
from tools import tool


TASKS_FILE = STATE_DIR / "tasks.json"
MIN_INTERVAL = timedelta(minutes=5)
MAX_TASKS = 20
PREAUTHORIZABLE = {"fetch_url", "write_file"}  # run_shell 不能预授权
HEARTBEAT_OK = "HEARTBEAT_OK"

CURRENT = {"chat_id": None}   # 当前正在对话的聊天，由 bot.py 设置

def next_run(spec, after):
    """支持两种写法: every 30m / every 2h / daily 9:00"""
    spec = spec.strip().lower()
    m = re.fullmatch(r"every\s+(\d+)\s*([mh])", spec)
    if m:
        n = int(m[1])
        delta = timedelta(minutes=n) if m[2] == "m" else timedelta(hours=n)
        if delta < MIN_INTERVAL:
            raise ValueError(f"间隔不能小于{MIN_INTERVAL}")

        return after + delta

    m = re.fullmatch(r"daily\s+(\d{1,2}):(\d{2})", spec)
    if m:
        h, mi = int(m[1]), int(m[2])

        if h > 23 or mi > 59:
            raise ValueError("时间不合法")

        t = after.replace(hour=h, minute=mi, second=0, microsecond=0)
        return t if t > after else t + timedelta(days=1)
    raise ValueError(f"看不懂的时间规则：{spec!r}，支持 every 30m / every 2h / daily 09:00")
