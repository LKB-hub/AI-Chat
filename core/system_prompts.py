#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统提示词管理器
"""

from typing import Optional, Dict, List
from collections import OrderedDict


class SystemPromptManager:
    """系统提示词管理器"""

    PRESETS = OrderedDict([
        ("默认助手", "你是一个有用的助手。"),
        ("代码专家", "你是一个专业的编程专家，擅长多种编程语言。请用简洁、清晰的方式回答编程问题，并提供代码示例。"),
        ("翻译助手", "你是一个专业的翻译助手。请将用户输入的内容翻译为目标语言，保持原文的语气和风格。如果未指定目标语言，默认翻译为英文。"),
        ("写作助手", "你是一个专业的写作助手。请帮助用户润色文章、修改语法错误、提供写作建议。保持原文的核心意思不变。"),
        ("数学老师", "你是一个耐心的数学老师。请逐步解释数学问题的解题过程，确保学生能够理解每一步。使用 LaTeX 格式表示数学公式。"),
        ("创意伙伴", "你是一个充满创意的伙伴。请用富有想象力和幽默感的方式回答问题，鼓励用户发散思维。"),
        ("知识问答", "你是一个知识渊博的助手。请准确、全面地回答用户的问题。如果不确定，请诚实说明。"),
        ("面试官", "你是一个专业的面试官。请根据用户提供的职位信息，提出相关的面试问题，并对用户的回答给出评价和建议。"),
        ("生活顾问", "你是一个贴心的生活顾问。请为用户提供实用的生活建议，包括健康、理财、人际关系等方面。"),
        ("论文助手", "你是一个学术论文写作助手。请帮助用户进行论文结构规划、文献综述、数据分析方法选择等。使用学术风格的语言。"),
    ])

    def __init__(self):
        self.prompts: Dict[str, str] = {}
        self.session_prompts: Dict[str, str] = {}  # 每个会话的自定义提示词
        self.load()

    def load(self) -> None:
        from . import SYSTEM_PROMPTS_FILE
        from .helpers import FileHelper
        data = FileHelper.read_json(SYSTEM_PROMPTS_FILE, {})
        if data:
            self.prompts = data.get("custom", {})
            self.session_prompts = data.get("session", {})
        else:
            self.prompts = dict(self.PRESETS)
            self.session_prompts = {}
            self.save()

    def save(self) -> None:
        from . import SYSTEM_PROMPTS_FILE
        from .helpers import FileHelper
        data = {
            "custom": self.prompts,
            "session": self.session_prompts,
        }
        FileHelper.write_json(SYSTEM_PROMPTS_FILE, data)

    def get_prompt(self, session_name: str) -> str:
        """获取指定会话的系统提示词"""
        if session_name in self.session_prompts:
            return self.session_prompts[session_name]
        return self.prompts.get("默认助手", "你是一个有用的助手。")

    def set_session_prompt(self, session_name: str, prompt: str) -> None:
        self.session_prompts[session_name] = prompt
        self.save()

    def remove_session_prompt(self, session_name: str) -> None:
        if session_name in self.session_prompts:
            del self.session_prompts[session_name]
            self.save()

    def list_presets(self) -> List[str]:
        return list(self.PRESETS.keys())

    def get_preset(self, name: str) -> Optional[str]:
        return self.PRESETS.get(name)

    def add_custom(self, name: str, prompt: str) -> bool:
        if name in self.prompts:
            return False
        self.prompts[name] = prompt
        self.save()
        return True

    def update_custom(self, name: str, prompt: str) -> bool:
        if name not in self.prompts:
            return False
        self.prompts[name] = prompt
        self.save()
        return True

    def delete_custom(self, name: str) -> bool:
        if name not in self.prompts or name in self.PRESETS:
            return False
        del self.prompts[name]
        self.save()
        return True
