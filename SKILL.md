---
name: zsxq-publish
description: |
  知识星球内容发布工具。将本地 Markdown 文件或文本内容快速发布到知识星球（韭菜喵厂长）。
  支持发布话题（短内容）和长文章两种模式。自动处理 Markdown 到知识星球富文本格式的转换。
  Cookie 过期时自动提示浏览器登录授权，登录后持久化保存。
  当用户需要：(1) 发布内容到知识星球，(2) 发布 Markdown 文件，(3) 查看发布历史，(4) 登录授权时使用。
  触发词：发布到知识星球、zsxq-publish、知识星球发布、发布话题、发布文章
allowed-tools: Bash, Read, Write, Glob, Grep
mode-command: false
---

# 知识星球内容发布工具

## 概览

将内容发布到**韭菜喵厂长**知识星球（ID: 15554418212152）。

支持两种发布模式：
- **话题模式**（topic）：短内容，直接以富文本发布，<500字自动选择
- **文章模式**（article）：长内容，两步流程（创建文章 → 创建话题引用），>=500字自动选择

## 运行器路径

所有命令通过 `run.py` 运行器执行，它会自动管理虚拟环境和依赖安装：

```
RUN = "C:/Users/Administrator/.claude/skills/zsxq-publish/scripts/run.py"
```

## 命令参考

### 1. 浏览器登录授权（Cookie 过期时使用）

```bash
python "${RUN}" main.py login --timeout 120
```

- 自动打开 Chrome 浏览器到知识星球登录页
- 用户扫码登录后，自动提取 Cookie 并保存到 auth.json
- 登录一次后 Cookie 长期有效，无需频繁登录
- `--timeout` 可选，登录等待超时秒数，默认 120

### 2. 检查认证状态

```bash
python "${RUN}" main.py check-auth
```

- 如果认证过期，会提示运行 login 命令

### 3. 发布本地文件（自动判断模式）

```bash
python "${RUN}" main.py publish --file "<文件路径>" --tags "标签1,标签2"
```

### 4. 发布话题（短内容）

从文本发布：
```bash
python "${RUN}" main.py topic --text "话题内容文本" --title "可选标题" --tags "标签1,标签2"
```

从文件发布：
```bash
python "${RUN}" main.py topic --file "<文件路径>" --title "可选标题" --tags "标签1"
```

### 5. 发布文章（长内容）

```bash
python "${RUN}" main.py article --file "<Markdown文件路径>" --title "可选标题" --tags "标签1,标签2"
```

### 6. 查看发布历史

```bash
python "${RUN}" main.py history --count 10
```

## 工作流场景

### 场景 A：认证过期 → 自动登录 → 发布

1. 先运行 `check-auth` 检查认证状态
2. 如果过期，运行 `login` 命令打开浏览器
3. 用户在浏览器中扫码登录
4. Cookie 自动保存到 auth.json
5. 继续执行发布操作

**重要**: 当 check-auth 或发布命令报告认证过期时，必须先运行 login 命令。

### 场景 B：用户提供文本内容发布

1. 用户说 "发布到知识星球：xxx内容"
2. 先 check-auth，如过期则 login
3. 判断内容长度选择话题/文章模式
4. 执行发布命令
5. 报告发布结果

### 场景 C：用户指定本地文件发布

1. 用户说 "把 xxx.md 发布到知识星球"
2. 先 check-auth，如过期则 login
3. Read 文件确认内容
4. 使用 `publish --file` 命令
5. 报告发布结果

### 场景 D：从飞书文档发布

1. 用户提供飞书文档链接或 document_id
2. 使用 lark-mcp 工具读取飞书文档内容
3. 将内容保存为临时 .md 文件
4. 使用 `publish --file` 发布

## 注意事项

- 发布后内容需审核，状态 `in_review` 是正常的
- 话题最大文本长度 10000 字符
- 建议批量发布时每篇间隔 3-5 秒
- 登录一次后 Cookie 长期有效（通常数周到数月）
- 如浏览器登录失败，检查 Chrome 是否正常安装
