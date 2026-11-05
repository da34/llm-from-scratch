"""Fibonacci 计算模块。"""


def fib(n: int) -> int:
    """返回第 n 个斐波那契数（fib(0)=0, fib(1)=1）。"""
    if n < 0:
        raise ValueError("n 必须是非负整数")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


if __name__ == "__main__":
    print(fib(10))
