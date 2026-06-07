# AI Chat for Android

此目录包含 Android 版 AI Chat 的 Kivy 源码和构建配置。

## 目录结构

```
android/
├── main.py                # Kivy 应用主入口
├── buildozer.spec         # Buildozer 构建配置
├── .gitignore
├── core/                  # 核心模块（从上级复制）
│   ├── api_manager.py     # API 密钥管理（含本地模型支持）
│   ├── session_manager.py # 会话管理
│   ├── settings.py        # 应用设置
│   ├── helpers.py         # 工具类
│   ├── markdown.py        # Markdown 渲染
│   ├── export_manager.py  # 导出管理
│   ├── shortcutter.py     # 快捷键
│   ├── system_prompts.py  # 系统提示词
│   └── __init__.py        # 全局常量
└── .github/workflows/     # 工作流文件（实际位于项目根目录 .github/workflows/）
```

## 构建 APK

### 方式一：GitHub Actions（推荐）

1. 将 `android/` 目录推送到 GitHub 仓库
2. 在 GitHub 仓库页面点击 **Actions** → **Build Android APK** → **Run workflow**
3. 等待约 30-60 分钟，构建完成后下载 APK

### 方式二：本地 Buildozer

需要 Linux 环境（或 WSL/Docker）：

```bash
cd android
pip install buildozer cython
buildozer -v android debug
```

APK 生成在 `android/bin/` 目录下。

## 功能特性

- 💬 多会话对话
- 🔑 多 API 提供商（OpenAI、SiliconFlow、DeepSeek 等）
- 🏠 本地模型支持（Ollama / LM Studio）
- 🌓 浅色/深色主题切换
- ⚙️ 模型参数调节（Temperature 等）
