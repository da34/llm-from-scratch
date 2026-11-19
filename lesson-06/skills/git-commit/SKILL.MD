---
name: git-commit
description: 按团队规范写 git 提交信息。用户要求提交代码或写 commit message 时使用。
---

# 提交信息规范

1. 第一行格式：<类型>: <简述>，类型只能是 feat / fix / docs / refactor / test
2. 简述不超过 50 字，不加句号
3. 空一行后写"为什么改"，不写"改了什么"（diff 里已经有了）
4. 提交前先运行 git diff --staged，确认暂存区内容和描述一致
