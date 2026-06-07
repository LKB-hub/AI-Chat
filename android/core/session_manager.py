#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理器
"""

from typing import Optional, List, Dict, Any


class SessionManager:
    """会话管理器"""

    def __init__(self):
        self.sessions: Dict[str, List[Dict]] = {}
        self.current_session: str = "默认会话"
        self._load()

    def _load(self) -> None:
        from . import SESSIONS_FILE, MAX_HISTORY_ROUNDS
        from .helpers import FileHelper
        data = FileHelper.read_json(SESSIONS_FILE, {})
        if data and "sessions" in data:
            self.sessions = data["sessions"]
            self.current_session = data.get("current_session", "默认会话")
        else:
            self.sessions = {"默认会话": []}
            self.current_session = "默认会话"
        if self.current_session not in self.sessions:
            if self.sessions:
                self.current_session = list(self.sessions.keys())[0]
            else:
                self.sessions["默认会话"] = []
                self.current_session = "默认会话"

    def save(self) -> None:
        from . import SESSIONS_FILE
        from .helpers import FileHelper
        data = {
            "current_session": self.current_session,
            "sessions": self.sessions,
        }
        FileHelper.write_json(SESSIONS_FILE, data)

    @property
    def conversation_history(self) -> List[Dict]:
        return self.sessions.get(self.current_session, [])

    @conversation_history.setter
    def conversation_history(self, value: List[Dict]) -> None:
        self.sessions[self.current_session] = value

    def create_session(self, name: str) -> bool:
        from . import signal_session_changed
        from .helpers import Validator
        if not Validator.is_valid_session_name(name):
            return False
        name = name.strip()
        if name in self.sessions:
            return False
        self.sessions[name] = []
        self.current_session = name
        self.save()
        signal_session_changed.emit()
        return True

    def delete_session(self, name: str) -> bool:
        from . import signal_session_changed
        from . import system_prompt_manager
        if len(self.sessions) <= 1:
            return False
        if name not in self.sessions:
            return False
        del self.sessions[name]
        if system_prompt_manager:
            system_prompt_manager.remove_session_prompt(name)
        if self.current_session == name:
            self.current_session = list(self.sessions.keys())[0]
        self.save()
        signal_session_changed.emit()
        return True

    def switch_session(self, name: str) -> bool:
        from . import signal_session_changed
        if name not in self.sessions or name == self.current_session:
            return False
        self.current_session = name
        self.save()
        signal_session_changed.emit()
        return True

    def rename_session(self, old_name: str, new_name: str) -> bool:
        from . import signal_session_changed
        from .helpers import Validator
        from . import system_prompt_manager
        if old_name not in self.sessions:
            return False
        if new_name in self.sessions:
            return False
        if not Validator.is_valid_session_name(new_name):
            return False
        new_name = new_name.strip()
        self.sessions[new_name] = self.sessions.pop(old_name)
        if system_prompt_manager and old_name in system_prompt_manager.session_prompts:
            system_prompt_manager.session_prompts[new_name] = \
                system_prompt_manager.session_prompts.pop(old_name)
            system_prompt_manager.save()
        if self.current_session == old_name:
            self.current_session = new_name
        self.save()
        signal_session_changed.emit()
        return True

    def clear_session(self, name: str = None) -> None:
        if name is None:
            name = self.current_session
        self.sessions[name] = []
        self.save()

    def clear_all_sessions(self) -> None:
        for name in self.sessions:
            self.sessions[name] = []
        self.save()

    def add_message(self, role: str, content: str, session_name: str = None) -> None:
        from . import MAX_HISTORY_ROUNDS
        if session_name is None:
            session_name = self.current_session
        if session_name not in self.sessions:
            return
        self.sessions[session_name].append({"role": role, "content": content})
        while len(self.sessions[session_name]) > MAX_HISTORY_ROUNDS * 2:
            self.sessions[session_name].pop(0)
        self.save()

    def delete_message(self, index: int, session_name: str = None) -> bool:
        if session_name is None:
            session_name = self.current_session
        history = self.sessions.get(session_name, [])
        if 0 <= index < len(history):
            history.pop(index)
            self.save()
            return True
        return False

    def get_message_count(self, session_name: str = None) -> int:
        if session_name is None:
            session_name = self.current_session
        return len(self.sessions.get(session_name, []))

    def get_session_names(self) -> List[str]:
        return list(self.sessions.keys())

    def get_session_info(self, name: str) -> Dict:
        from .helpers import TextHelper
        history = self.sessions.get(name, [])
        total_chars = sum(len(m.get("content", "")) for m in history)
        user_msgs = sum(1 for m in history if m["role"] == "user")
        ai_msgs = sum(1 for m in history if m["role"] == "assistant")
        return {
            "name": name,
            "total_messages": len(history),
            "user_messages": user_msgs,
            "ai_messages": ai_msgs,
            "total_chars": total_chars,
            "estimated_tokens": TextHelper.estimate_tokens(
                " ".join(m.get("content", "") for m in history)
            ),
        }

    def get_all_stats(self) -> Dict:
        from .helpers import TextHelper
        total_sessions = len(self.sessions)
        total_messages = sum(len(v) for v in self.sessions.values())
        total_chars = sum(
            len(m.get("content", ""))
            for v in self.sessions.values()
            for m in v
        )
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_chars": total_chars,
            "estimated_tokens": TextHelper.estimate_tokens(
                " ".join(
                    m.get("content", "")
                    for v in self.sessions.values()
                    for m in v
                )
            ),
        }

    def search_messages(self, keyword: str) -> List[Dict]:
        """搜索所有会话中的消息"""
        from .helpers import TextHelper
        results = []
        keyword_lower = keyword.lower()
        for session_name, messages in self.sessions.items():
            for idx, msg in enumerate(messages):
                if keyword_lower in msg.get("content", "").lower():
                    results.append({
                        "session": session_name,
                        "index": idx,
                        "role": msg["role"],
                        "content": msg["content"],
                        "preview": TextHelper.truncate(msg["content"], 80),
                    })
        return results
