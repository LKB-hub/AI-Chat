#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chat for Android - Kivy 版
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any

# 添加项目根目录到路径
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import (
    StringProperty, BooleanProperty, NumericProperty,
    ObjectProperty, ListProperty, DictProperty, ColorProperty
)
from kivy.utils import get_color_from_hex, rgba
from kivy.clock import mainthread

# 导入核心模块
sys.path.insert(0, os.path.join(APP_DIR, "core") if os.path.isdir(os.path.join(APP_DIR, "core")) else APP_DIR)
from core import (
    api_key_manager, session_manager, system_prompt_manager,
    app_settings, init_globals, signal_theme_changed,
    signal_session_changed, encryption_password, encryption_enabled,
    EXPORT_DIR, CACHE_DIR
)
from core.helpers import DateTimeHelper, TextHelper, FileHelper, EncryptionManager, Validator
from core.markdown import MarkdownRenderer

# ============================================================================
# 主题系统
# ============================================================================

THEMES = {
    "light": {
        "bg": "#f5f6fa", "card": "#ffffff", "sidebar": "#ffffff",
        "text": "#1a1a1a", "text_secondary": "#888888",
        "accent": "#0084ff", "accent_ai": "#00a67e",
        "input_bg": "#ffffff", "border": "#e8e8e8",
        "primary": "#0084ff", "secondary": "#00a67e",
        "user_bubble": "#0084ff", "ai_bubble": "#e8f0fe",
    },
    "dark": {
        "bg": "#1e1e2e", "card": "#2d2d3f", "sidebar": "#252536",
        "text": "#ffffff", "text_secondary": "#aaaaaa",
        "accent": "#6c5ce7", "accent_ai": "#00a67e",
        "input_bg": "#2d2d3f", "border": "#3a3a4f",
        "primary": "#6c5ce7", "secondary": "#00a67e",
        "user_bubble": "#6c5ce7", "ai_bubble": "#3a3a5f",
    },
}


def get_theme():
    theme_name = app_settings.get("theme", "light") if app_settings else "light"
    return THEMES.get(theme_name, THEMES["light"])


def get_color(key):
    return get_color_from_hex(get_theme()[key])


# ============================================================================
# 消息气泡组件
# ============================================================================

class MessageBubble(BoxLayout):
    """消息气泡"""
    message = StringProperty("")
    is_user = BooleanProperty(False)
    timestamp = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.bind(minimum_height=self._set_height)

    def _set_height(self, *args):
        self.height = max(dp(50), self.minimum_height)


class ChatMessage(RecycleDataViewBehavior, BoxLayout):
    """RecycleView 消息项"""
    index = NumericProperty(0)
    text = StringProperty("")
    is_user = BooleanProperty(False)
    time_str = StringProperty("")

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        return False


# ============================================================================
# 主聊天界面
# ============================================================================

class ChatScreen(Screen):
    """聊天主界面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sending = False
        self._current_messages = []
        self._init_ui()

    def _init_ui(self):
        theme = get_theme()
        layout = BoxLayout(orientation="vertical")

        # 顶部栏
        top_bar = BoxLayout(
            size_hint_y=None, height=dp(56),
            padding=[dp(8), dp(8)],
        )
        # 菜单按钮
        menu_btn = Button(
            text="☰", size_hint=(None, None), size=(dp(48), dp(48)),
            background_normal="", background_color=get_color("accent"),
        )
        menu_btn.bind(on_release=lambda x: self._toggle_drawer())
        top_bar.add_widget(menu_btn)

        # 会话标题
        title = Label(
            text=self._get_session_title(),
            color=get_color("text"), size_hint_x=1,
            font_size=sp(18),
        )
        top_bar.add_widget(title)

        # 设置按钮
        settings_btn = Button(
            text="⚙", size_hint=(None, None), size=(dp(48), dp(48)),
            background_normal="", background_color=get_color("accent"),
        )
        settings_btn.bind(on_release=lambda x: self._open_settings())
        top_bar.add_widget(settings_btn)

        layout.add_widget(top_bar)

        # 消息列表
        self.message_rv = RecycleView()
        self.message_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None, padding=[dp(12), dp(8)],
        )
        self.message_layout.bind(minimum_height=self.message_layout.setter("height"))
        self.message_scroll = ScrollView()
        self.message_scroll.add_widget(self.message_layout)

        layout.add_widget(self.message_scroll)

        # 底部输入区
        input_area = BoxLayout(
            size_hint_y=None, height=dp(56),
            padding=[dp(8), dp(4)], spacing=dp(4),
        )
        self.input_field = TextInput(
            size_hint_x=1,
            multiline=False,
            hint_text="输入消息...",
            font_size=sp(16),
            padding=[dp(8), dp(12)],
        )
        self.input_field.bind(on_text_validate=lambda x: self._send_message())
        input_area.add_widget(self.input_field)

        send_btn = Button(
            text="发送", size_hint=(None, None), size=(dp(64), dp(48)),
            background_normal="", background_color=get_color("primary"),
        )
        send_btn.bind(on_release=lambda x: self._send_message())
        input_area.add_widget(send_btn)

        layout.add_widget(input_area)
        self.add_widget(layout)

    def _get_session_title(self):
        if session_manager:
            return session_manager.current_session or "AI Chat"
        return "AI Chat"

    def _toggle_drawer(self):
        sm = self.manager
        if sm:
            sm.current = "sessions" if sm.current != "sessions" else "chat"

    def _open_settings(self):
        sm = self.manager
        if sm and sm.has_screen("settings"):
            sm.current = "settings"

    def _send_message(self):
        text = self.input_field.text.strip()
        if not text or self._sending:
            return

        if not api_key_manager or not api_key_manager.get_client():
            self._show_error("未配置 API 密钥，请先在设置中添加")
            return

        self._sending = True
        self.input_field.text = ""

        # 显示用户消息
        self._add_message(text, is_user=True)

        # 显示"思考中..."
        thinking_id = self._add_message("思考中...", is_user=False)

        # 后台线程发送
        thread = threading.Thread(
            target=self._do_request,
            args=(text, thinking_id),
            daemon=True,
        )
        thread.start()

    def _add_message(self, text, is_user=False):
        msg_frame = BoxLayout(
            orientation="horizontal",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(40),
            padding=[dp(4), dp(2)],
        )

        # 空白填充
        if is_user:
            msg_frame.add_widget(BoxLayout(size_hint_x=0.3))

        msg_label = Label(
            text=text,
            size_hint_x=0.7,
            text_size=(None, None),
            color=get_color("text"),
            padding=[dp(12), dp(8)],
            halign="right" if is_user else "left",
        )
        msg_label.bind(
            texture_size=lambda lb, sz: setattr(
                msg_frame, "height", max(dp(40), sz[1] + dp(16))
            )
        )
        msg_frame.add_widget(msg_label)

        if not is_user:
            msg_frame.add_widget(BoxLayout(size_hint_x=0.3))

        self.message_layout.add_widget(msg_frame)

        # 滚动到底部
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)

        return len(self.message_layout.children) - 1

    def _update_message(self, index, text):
        """更新消息内容（用于流式更新）"""
        if index < len(self.message_layout.children):
            child = self.message_layout.children[index]
            if isinstance(child, BoxLayout) and len(child.children) >= 2:
                label = child.children[1] if len(child.children) > 1 else child.children[0]
                if hasattr(label, "text") and not label.text.startswith("思考"):
                    label.text += text
                else:
                    label.text = text

    def _scroll_to_bottom(self):
        self.message_scroll.scroll_y = 0

    def _do_request(self, text, thinking_index):
        """后台发送 API 请求"""
        try:
            client = api_key_manager.get_client()
            cfg = api_key_manager.get_current_config()

            system_prompt = system_prompt_manager.get_prompt(
                session_manager.current_session
            ) if system_prompt_manager else ""

            messages_list = [{"role": "system", "content": system_prompt}]
            if session_manager and hasattr(session_manager, "conversation_history"):
                messages_list.extend(session_manager.conversation_history)
            messages_list.append({"role": "user", "content": text})

            model = cfg.get("model", "gpt-3.5-turbo")
            max_tokens = cfg.get("max_tokens", 4096)
            temperature = cfg.get("temperature", 0.7)
            top_p = cfg.get("top_p", 0.9)

            kwargs = dict(
                model=model,
                messages=messages_list,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            full_response = ""
            response = client.chat.completions.create(**kwargs)
            full_response = response.choices[0].message.content or ""

            # 更新消息
            Clock.schedule_once(lambda dt: self._on_response(text, full_response, thinking_index, None))

        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._on_response(text, None, thinking_index, str(e))
            )

    @mainthread
    def _on_response(self, question, answer, msg_index, error):
        if error:
            # 更新错误消息
            self._replace_thinking(msg_index, "请求失败: %s" % error)
            self._show_error(error)
        else:
            self._replace_thinking(msg_index, answer)
            # 保存到历史
            if session_manager:
                session_manager.add_message("user", question)
                session_manager.add_message("assistant", answer)

        self._sending = False

    def _replace_thinking(self, index, text):
        """替换"思考中..."为实际内容"""
        if index < len(self.message_layout.children):
            child = self.message_layout.children[index]
            for c in child.children:
                if isinstance(c, Label):
                    c.text = text
                    c.bind(
                        texture_size=lambda lb, sz: setattr(
                            child, "height", max(dp(40), sz[1] + dp(16))
                        )
                    )

    def _show_error(self, msg):
        popup = Popup(
            title="错误",
            content=Label(text=msg),
            size_hint=(0.8, 0.4),
        )
        popup.open()

    def on_enter(self):
        """进入屏幕时刷新"""
        theme = get_theme()
        self._apply_theme()

    def _apply_theme(self):
        theme = get_theme()
        # 主题色已全局通过 kv 绑定


# ============================================================================
# 会话列表界面
# ============================================================================

class SessionListScreen(Screen):
    """会话管理侧边栏"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_ui()

    def _init_ui(self):
        layout = BoxLayout(orientation="vertical", padding=[dp(8)])

        # 标题
        title = Label(
            text="会话列表",
            size_hint_y=None, height=dp(48),
            font_size=sp(20),
        )
        layout.add_widget(title)

        # 会话列表面板
        self.session_scroll = ScrollView()
        self.session_list = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(4),
        )
        self.session_list.bind(minimum_height=self.session_list.setter("height"))
        self.session_scroll.add_widget(self.session_list)
        layout.add_widget(self.session_scroll)

        # 底部按钮
        btn_layout = BoxLayout(
            size_hint_y=None, height=dp(50),
            spacing=dp(8), padding=[dp(8), dp(4)],
        )
        new_btn = Button(
            text="+ 新建会话",
            background_normal="",
            background_color=get_color("primary"),
        )
        new_btn.bind(on_release=lambda x: self._new_session())
        btn_layout.add_widget(new_btn)

        back_btn = Button(
            text="← 返回",
            background_normal="",
            background_color=get_color("secondary"),
        )
        back_btn.bind(on_release=lambda x: self._go_back())
        btn_layout.add_widget(back_btn)

        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def on_enter(self):
        self._refresh_list()

    def _refresh_list(self):
        self.session_list.clear_widgets()
        if not session_manager:
            return

        sessions = session_manager.list_sessions() if hasattr(session_manager, "list_sessions") else []
        current = session_manager.current_session if hasattr(session_manager, "current_session") else ""

        for ses in sessions:
            name = ses.get("name", ses) if isinstance(ses, dict) else ses
            is_current = (name == current)

            btn = Button(
                text="● %s" % name if is_current else "○ %s" % name,
                size_hint_y=None, height=dp(44),
                background_normal="",
                background_color=get_color("primary") if is_current else get_color("card"),
                color=get_color("text"),
                halign="left",
                padding=[dp(12), 0],
            )
            btn.bind(on_release=lambda b, n=name: self._switch_session(n))
            # 删除按钮
            del_btn = Button(
                text="✕", size_hint=(None, None), size=(dp(36), dp(44)),
                background_normal="", background_color=(1, 0.3, 0.3, 0.8),
            )
            del_btn.bind(on_release=lambda b, n=name: self._delete_session(n))

            row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(2))
            row.add_widget(btn)
            row.add_widget(del_btn)
            self.session_list.add_widget(row)

    def _new_session(self):
        if session_manager and hasattr(session_manager, "create_session"):
            name = "会话 %s" % datetime.now().strftime("%m%d_%H%M")
            session_manager.create_session(name)
        self._refresh_list()
        self._go_back()

    def _switch_session(self, name):
        if session_manager and hasattr(session_manager, "switch_to"):
            session_manager.switch_to(name)
        self._refresh_list()
        self._go_back()

    def _delete_session(self, name):
        if session_manager and hasattr(session_manager, "delete_session"):
            session_manager.delete_session(name)
        self._refresh_list()

    def _go_back(self):
        self.manager.current = "chat"


# ============================================================================
# 设置界面
# ============================================================================

class SettingsScreen(Screen):
    """设置界面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_ui()

    def _init_ui(self):
        layout = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)])

        # 标题
        top_layout = BoxLayout(
            size_hint_y=None, height=dp(52),
            spacing=dp(8),
        )
        back_btn = Button(
            text="← 返回",
            size_hint=(None, None), size=(dp(72), dp(44)),
            background_normal="", background_color=get_color("accent"),
        )
        back_btn.bind(on_release=lambda x: self._go_back())
        top_layout.add_widget(back_btn)

        title = Label(
            text="⚙ 设置",
            font_size=sp(20),
            size_hint_x=1,
        )
        top_layout.add_widget(title)
        layout.add_widget(top_layout)

        # 设置滚动内容
        scroll = ScrollView()
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=[dp(4), dp(4)],
        )
        content.bind(minimum_height=content.setter("height"))

        # ---- API 配置 ----
        content.add_widget(Label(
            text="[b]API 配置[/b]",
            markup=True,
            size_hint_y=None, height=dp(32),
            font_size=sp(16),
        ))

        # API 提供商选择
        provider_layout = BoxLayout(
            size_hint_y=None, height=dp(44),
            spacing=dp(8),
        )
        provider_layout.add_widget(Label(text="提供商:", size_hint_x=0.35))
        self.provider_spinner = Spinner(
            text="选择...",
            values=(
                api_key_manager.list_configs()
                if api_key_manager and hasattr(api_key_manager, "list_configs")
                else ["OpenAI"]
            ),
            size_hint_x=0.65,
        )
        self.provider_spinner.bind(text=self._on_provider_change)
        provider_layout.add_widget(self.provider_spinner)
        content.add_widget(provider_layout)

        # API Key
        api_layout = BoxLayout(
            size_hint_y=None, height=dp(44),
            spacing=dp(8),
        )
        api_layout.add_widget(Label(text="API Key:", size_hint_x=0.35))
        self.api_key_input = TextInput(
            size_hint_x=0.65,
            multiline=False,
            hint_text="sk-...",
            password=True,
        )
        api_layout.add_widget(self.api_key_input)
        content.add_widget(api_layout)

        # Base URL
        url_layout = BoxLayout(
            size_hint_y=None, height=dp(44),
            spacing=dp(8),
        )
        url_layout.add_widget(Label(text="Base URL:", size_hint_x=0.35))
        self.base_url_input = TextInput(
            size_hint_x=0.65,
            multiline=False,
            hint_text="https://...",
        )
        url_layout.add_widget(self.base_url_input)
        content.add_widget(url_layout)

        # 模型名
        model_layout = BoxLayout(
            size_hint_y=None, height=dp(44),
            spacing=dp(8),
        )
        model_layout.add_widget(Label(text="模型:", size_hint_x=0.35))
        self.model_input = TextInput(
            size_hint_x=0.5,
            multiline=False,
            hint_text="gpt-3.5-turbo",
        )
        model_layout.add_widget(self.model_input)
        refresh_btn = Button(
            text="🔄", size_hint=(None, None), size=(dp(44), dp(44)),
            background_normal="", background_color=get_color("secondary"),
        )
        refresh_btn.bind(on_release=lambda x: self._refresh_models())
        model_layout.add_widget(refresh_btn)
        content.add_widget(model_layout)

        # 测试连接按钮
        test_btn = Button(
            text="🔌 测试连接",
            size_hint_y=None, height=dp(40),
            background_normal="", background_color=get_color("primary"),
        )
        test_btn.bind(on_release=lambda x: self._test_connection())
        content.add_widget(test_btn)

        # ---- 模型参数 ----
        content.add_widget(Label(
            text="",
            size_hint_y=None, height=dp(8),
        ))
        content.add_widget(Label(
            text="[b]模型参数[/b]",
            markup=True,
            size_hint_y=None, height=dp(32),
            font_size=sp(16),
        ))

        # Temperature
        temp_layout = BoxLayout(
            size_hint_y=None, height=dp(44),
            spacing=dp(8),
        )
        temp_layout.add_widget(Label(text="Temperature:", size_hint_x=0.5))
        temp_right = BoxLayout(size_hint_x=0.5, spacing=dp(4))
        self.temp_slider = __import__("kivy.uix.slider", fromlist=["Slider"]).Slider(
            min=0.0, max=2.0, value=0.7, step=0.1,
        )
        self.temp_label = Label(text="0.7", size_hint=(None, None), size=(dp(36), dp(24)))
        temp_right.add_widget(self.temp_slider)
        temp_right.add_widget(self.temp_label)
        temp_layout.add_widget(temp_right)
        content.add_widget(temp_layout)
        self.temp_slider.bind(value=lambda s, v: setattr(self.temp_label, "text", "%.1f" % v))

        # ---- 主题 ----
        content.add_widget(Label(
            text="",
            size_hint_y=None, height=dp(8),
        ))
        content.add_widget(Label(
            text="[b]主题[/b]",
            markup=True,
            size_hint_y=None, height=dp(32),
            font_size=sp(16),
        ))

        theme_layout = BoxLayout(
            size_hint_y=None, height=dp(44),
            spacing=dp(8),
        )
        theme_layout.add_widget(Label(text="主题模式:", size_hint_x=0.4))
        self.theme_spinner = Spinner(
            text="浅色",
            values=["浅色", "深色"],
            size_hint_x=0.6,
        )
        self.theme_spinner.bind(text=self._on_theme_change)
        theme_layout.add_widget(self.theme_spinner)
        content.add_widget(theme_layout)

        # 保存按钮
        save_btn = Button(
            text="💾 保存设置",
            size_hint_y=None, height=dp(48),
            background_normal="", background_color=get_color("primary"),
            font_size=sp(18),
        )
        save_btn.bind(on_release=lambda x: self._save_settings())
        content.add_widget(save_btn)

        # 底部留白
        content.add_widget(BoxLayout(size_hint_y=None, height=dp(40)))
        content.add_widget(Label(
            text="AI Chat v2.0.0 for Android",
            size_hint_y=None, height=dp(24),
            font_size=sp(12),
            color=get_color_from_hex("#888888"),
        ))

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def on_enter(self):
        self._load_current_config()

    def _load_current_config(self):
        if not api_key_manager:
            return
        cfg = api_key_manager.get_current_config()
        if cfg:
            self.provider_spinner.text = api_key_manager.current_name
            self.api_key_input.text = cfg.get("api_key", "")
            self.base_url_input.text = cfg.get("base_url", "")
            self.model_input.text = cfg.get("model", "")
            self.temp_slider.value = cfg.get("temperature", 0.7)

        theme_name = app_settings.get("theme", "light") if app_settings else "light"
        self.theme_spinner.text = "浅色" if theme_name == "light" else "深色"

    def _on_provider_change(self, spinner, text):
        cfg = api_key_manager.get_config(text) if api_key_manager else None
        if cfg:
            self.api_key_input.text = cfg.get("api_key", "")
            self.base_url_input.text = cfg.get("base_url", "")
            self.model_input.text = cfg.get("model", "")

    def _refresh_models(self):
        """刷新本地模型列表"""
        if not api_key_manager:
            return
        base_url = self.base_url_input.text.strip()
        api_key = self.api_key_input.text.strip()
        temp_cfg = {"base_url": base_url, "api_key": api_key}
        models = api_key_manager.fetch_local_models(temp_cfg)
        if models:
            self.model_input.text = models[0]
            popup = Popup(
                title="找到 %d 个模型" % len(models),
                content=Label(text="已填入: %s" % models[0]),
                size_hint=(0.8, 0.4),
            )
            popup.open()
        else:
            popup = Popup(
                title="未找到模型",
                content=Label(text="请确认本地服务已启动"),
                size_hint=(0.8, 0.4),
            )
            popup.open()

    def _test_connection(self):
        """测试连接"""
        base_url = self.base_url_input.text.strip()
        if not base_url:
            popup = Popup(
                title="提示",
                content=Label(text="请先填写 Base URL"),
                size_hint=(0.8, 0.4),
            )
            popup.open()
            return

        import requests
        try:
            resp = requests.get(base_url, timeout=5)
            popup = Popup(
                title="连接成功",
                content=Label(text="HTTP %d" % resp.status_code),
                size_hint=(0.8, 0.4),
            )
        except Exception as e:
            popup = Popup(
                title="连接失败",
                content=Label(text=str(e)[:100]),
                size_hint=(0.8, 0.4),
            )
        popup.open()

    def _on_theme_change(self, spinner, text):
        theme = "dark" if text == "深色" else "light"
        if app_settings:
            app_settings.set("theme", theme)

    def _save_settings(self):
        if not api_key_manager:
            return

        provider = self.provider_spinner.text
        api_key = self.api_key_input.text.strip()
        base_url = self.base_url_input.text.strip()
        model = self.model_input.text.strip()
        temperature = self.temp_slider.value

        cfg = api_key_manager.get_config(provider)
        if cfg:
            api_key_manager.update_config(provider,
                                           api_key=api_key,
                                           base_url=base_url,
                                           model=model,
                                           temperature=temperature)
            if provider != api_key_manager.current_name:
                api_key_manager.switch_to(provider)

        popup = Popup(
            title="保存成功",
            content=Label(text="设置已保存"),
            size_hint=(0.8, 0.3),
        )
        popup.open()

    def _go_back(self):
        self.manager.current = "chat"


# ============================================================================
# 应用入口
# ============================================================================

class AIChatApp(App):
    """AI Chat Kivy 应用"""

    def build(self):
        # 初始化核心模块
        init_globals()

        # 设置窗口
        Window.softinput_mode = "below_target"
        Window.keyboard_anim_args = {"d": 0.2, "t": "linear"}

        # 创建屏幕管理器
        sm = ScreenManager(transition=SlideTransition(duration=0.2))
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(SessionListScreen(name="sessions"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.current = "chat"

        # 应用主题
        self._apply_theme()

        return sm

    def _apply_theme(self):
        theme = get_theme()
        Window.clearcolor = get_color_from_hex(theme["bg"])


if __name__ == "__main__":
    AIChatApp().run()
