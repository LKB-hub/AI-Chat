#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快捷键管理器 - 纯后端版本
"""

import os
from typing import Optional
from collections import OrderedDict


class ShortcutManager:
    """快捷键管理器"""

    DEFAULT_SHORTCUTS = OrderedDict([
        ("发送消息", "Return"),
        ("新建会话", "<Control-n>"),
        ("删除会话", "<Control-Delete>"),
        ("清空对话", "<Control-l>"),
        ("搜索消息", "<Control-f>"),
        ("导出对话", "<Control-e>"),
        ("API设置", "<Control-comma>"),
        ("切换主题", "<Control-t>"),
        ("放大字体", "<Control-plus>"),
        ("缩小字体", "<Control-minus>"),
        ("重置字体", "<Control-0>"),
        ("全选输入", "<Control-a>"),
        ("复制选中", "<Control-c>"),
        ("粘贴内容", "<Control-v>"),
        ("撤销输入", "<Control-z>"),
        ("关于", "<F1>"),
        ("关闭窗口", "<Escape>"),
    ])

    def __init__(self):
        self.shortcuts = dict(self.DEFAULT_SHORTCUTS)
        self._handlers = {}
        self.load()

    def load(self) -> None:
        from . import DATA_DIR
        from .helpers import FileHelper
        data = FileHelper.read_json(os.path.join(DATA_DIR, "shortcuts.json"), {})
        if data:
            self.shortcuts = {**self.DEFAULT_SHORTCUTS, **data}

    def save(self) -> None:
        from . import DATA_DIR
        from .helpers import FileHelper
        FileHelper.write_json(os.path.join(DATA_DIR, "shortcuts.json"), self.shortcuts)

    def get(self, action: str) -> str:
        return self.shortcuts.get(action, "")

    def set(self, action: str, key: str) -> None:
        self.shortcuts[action] = key
        self.save()

    def register_handler(self, action: str, handler) -> None:
        self._handlers[action] = handler

    def get_handler(self, action: str):
        """获取指定动作的处理函数"""
        return self._handlers.get(action)

    def bind_all(self, target) -> None:
        """绑定所有快捷键（子类重写此方法进行平台适配）"""
        for action, key in self.shortcuts.items():
            if action in self._handlers:
                try:
                    if hasattr(target, 'bind'):
                        target.bind(key, lambda e, a=action: self._handlers[a]())
                except Exception:
                    pass
