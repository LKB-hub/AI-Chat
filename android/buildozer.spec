[app]

# 应用信息
title = AI Chat
package.name = aichat
package.domain = org.aichat
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json
version = 2.0.0
version.regex = __version__\s*=\s*['"](.*)['"]
version.filename = main.py

# 构建需求
requirements = python3,kivy==2.3.1,openai,requests,pyjnius,android

# 权限
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Android 特定
android.api = 34
android.minapi = 21
android.sdk = 34
android.ndk = 27
android.ndk_api = 21
android.sdk_path = 
android.ndk_path = 
android.ant_path = 
android.accept_sdk_license = True
android.archs = arm64-v8a
android.gradle_dependencies = 
android.enable_androidx = True
android.gradle_version = 8.0
android.gradle_plugin_version = 8.0.0
android.use_play_services = False
android.google_services = False
android.wakelock = False
android.window_size = 720x1280
android.fullscreen = 1
android.store_languages_standard = True

# 图标（可选）
# android.icon = icon.png

# 应用启动
osx.python_version = 3
osx.kivy_version = 2.3.1

# 安全
android.private_storage = True
android.allow_backup = True

# 网络
android.connected = True
android.install_location = auto

# 编译
presplash.color = #1e1e2e
# android.presplash = presplash.png

[buildozer]

log_level = 2
warn_on_root = 1
# 用 Docker 构建
docker = True
