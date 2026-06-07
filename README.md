# 🤖 AI Chat - 专业级 AI 对话助手

**版本：** 2.0.0 ｜ **语言：** Python 3.12+

一个基于 **Python tkinter** 构建的桌面端 AI 对话客户端，支持多会话管理、多 API 密钥、Markdown 渲染、主题切换、会话导出、系统托盘等丰富功能。

---

## ✨ 功能特性

| 分类 | 功能 |
|------|------|
| 💬 **对话** | 多会话独立管理，自动保存，对话历史搜索 |
| 🔑 **多 API** | 管理多个 API Key 并自由切换，支持自定义 API 地址 |
| 🎨 **Markdown** | 实时渲染 Markdown 消息，代码语法高亮，表格渲染 |
| 🌓 **主题** | 浅色/深色主题一键切换 |
| 📤 **导出** | 会话导出为 纯文本 / Markdown / JSON |
| 🧠 **系统提示** | 自定义和管理系统提示词模板 |
| ⚙️ **参数** | 可调模型参数（temperature、top_p、max_tokens 等） |
| ⌨️ **快捷键** | 丰富的键盘快捷键操作 |
| 🔍 **搜索** | 全会话历史全文搜索 |
| 🗂️ **文件** | 拖拽文件到输入框自动上传 |
| 🔊 **TTS** | 文字转语音朗读（需安装 `pyttsx3`） |
| 🔒 **加密** | 支持设置密码对本地数据进行加密存储 |
| 🌐 **代理** | 支持 HTTP 代理配置 |
| 📟 **系统托盘** | 最小化到系统托盘后台运行 |
| 🖥️ **CLI 模式** | 支持 `--cli` 命令行对话模式 |
| 🛠️ **打包** | 支持 PyInstaller 打包为单文件 exe |

---

## 📦 安装

### 方式一：Python 源码运行

#### 前置要求
- Python 3.10+
- pip

#### 安装依赖

```bash
pip install openai requests pyttsx3
```

> `pyttsx3` 为可选依赖（TTS 朗读功能），如不需要可跳过。

#### 启动

```bash
cd C:\Users\Administrator\Desktop\python\ai
python main.py
```

#### CLI 模式

```bash
python main.py --cli
```

#### 添加到 PATH

```bash
python main.py --install-path
```

### 方式二：使用打包后的 exe

`dist/AI-Chat.exe` 已由 PyInstaller 打包，可直接运行，无需安装 Python 环境。

---

## 🚀 快速开始

1. **启动程序** — 运行 `python main.py` 或双击 `dist/AI-Chat.exe`
2. **添加 API 密钥** — 点击界面上的 API 密钥管理按钮，添加你的 OpenAI API Key
3. **开始对话** — 输入框键入问题，按 Enter 发送（或 Ctrl+Enter 换行）
4. **管理会话** — 左侧会话面板新建、切换、删除会话
5. **调整主题** — 右上角一键切换浅色/深色模式

---

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Enter` | 发送消息 |
| `Ctrl+Enter` / `Shift+Enter` | 换行 |
| `Ctrl+N` | 新建会话 |
| `Ctrl+W` | 关闭当前会话 |
| `Ctrl+Shift+N` | 删除当前会话 |
| `Ctrl+F` | 搜索消息 |
| `Ctrl+D` | 清空当前会话 |
| `Ctrl+E` | 导出当前会话 |
| `Ctrl+S` | 展开/收起侧边栏 |
| `Ctrl+B` | 切换主题 |
| `Ctrl+Up` | 切换到上一个会话 |
| `Ctrl+Down` | 切换到下一个会话 |
| `Ctrl+Shift+C` | 复制代码块 |
| `Ctrl+Shift+S` | 保存代码块到文件 |
| `Ctrl+=` | 放大字体 |
| `Ctrl+-` | 缩小字体 |
| `Ctrl+0` | 重置字体大小 |
| `Escape` | 取消请求 / 关闭对话框 |
| `F11` | 切换全屏 |
| `F5` | 刷新模型列表 |

---

## 📁 项目结构

```
ai/
├── main.py                 # 主入口（GUI + CLI 双模式）
├── AI-Chat.spec            # PyInstaller 打包配置
├── core/
│   ├── __init__.py          # 全局常量、信号、管理器初始化
│   ├── api_manager.py       # API 密钥管理器
│   ├── session_manager.py   # 会话管理器
│   ├── export_manager.py    # 导出管理器
│   ├── helpers.py           # 工具类（日期、文本、文件、加密等）
│   ├── markdown.py          # Markdown 渲染引擎
│   ├── settings.py          # 设置管理器
│   ├── shortcutter.py       # 快捷键管理器
│   └── system_prompts.py    # 系统提示词管理器
├── static/                  # 静态资源（预留）
├── templates/               # 模板文件（预留）
├── build/                   # PyInstaller 构建中间产物
├── dist/                    # PyInstaller 打包输出（AI-Chat.exe）
├── cache/                   # 运行时缓存目录
└── exports/                 # 会话导出目录
```

### 数据目录

用户数据默认存储在：
- **Windows：** `%USERPROFILE%\Documents\AI-Chat\`
- **macOS / Linux：** `~/.aichat/`

包括：
- `sessions.json` — 会话数据
- `api_keys.json` — API 密钥（支持加密）
- `settings.json` — 应用设置
- `system_prompts.json` — 系统提示词模板
- `password.hash` — 加密密码哈希
- `cache/` — 缓存目录
- `exports/` — 导出文件目录

---

## 🔧 打包为 exe

项目已配置 PyInstaller，如需重新打包：

```bash
pip install pyinstaller
pyinstaller AI-Chat.spec
```

输出在 `dist/AI-Chat.exe`。也可以直接使用项目中已有的打包结果。

---

## ⚙️ 命令行参数

```bash
python main.py --help
```

| 参数 | 说明 |
|------|------|
| `--cli` | 以命令行模式运行（无图形界面） |
| `--install-path` | 将程序所在目录添加到系统 PATH |
| `--uninstall-path` | 从系统 PATH 中移除程序所在目录 |

---

## 💡 技术栈

- **UI 框架：** Tkinter（Python 标准库）
- **AI API：** OpenAI Python SDK
- **依赖请求：** `requests`
- **可选依赖：** `pyttsx3`（TTS 朗读）
- **打包工具：** PyInstaller

---

## 📝 开源说明

本项目为个人开发维护的 AI 聊天客户端，基于 OpenAI API 实现。欢迎使用与改进。

> ⚠️ 使用前请自行准备有效的 OpenAI API Key 或兼容接口的 API Key。
