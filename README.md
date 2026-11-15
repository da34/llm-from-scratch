# LLM from Scratch

## 项目简介

根据 纳米ai 的课程进行学习

## 目录结构

## 课程内容

### [lesson-01](lesson-01/)

实现 `agent` 的最小化代码

### [lesson-02](lesson-02/)

在 `lesson-01` 的基础添加 `tool` 的实现

### [lesson-03](lesson-03/)

添加 `tool` 的封装，新加工具不需要动主循环，并且加入工具的权限管控，危险命令需经过人的介入，并且限制工作区在启动目录

### [lesson-04](lesson-04/)

## 环境准备

python 3.x

## 运行方式

创建虚拟环境：

```shell
python -m venv .venv
```

安装项目依赖：

```shell
python -m pip install -r requirements.txt
```

然后进入对应的课程目录，单文件启动：

```shell
python agent.py
```

## 测试
