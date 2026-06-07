#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具类模块：日期时间、文本、文件、加密、剪贴板、验证、信号
"""

import json
import os
import re
import time
import base64
import hashlib
from datetime import datetime
from typing import Optional, Any, List


class DateTimeHelper:
    """日期时间工具"""

    @staticmethod
    def now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        return datetime.now().strftime(fmt)

    @staticmethod
    def timestamp() -> float:
        return time.time()

    @staticmethod
    def format_timestamp(ts: float, fmt: str = "%Y-%m-%d %H:%M") -> str:
        return datetime.fromtimestamp(ts).strftime(fmt)

    @staticmethod
    def time_ago(ts: float) -> str:
        diff = time.time() - ts
        if diff < 60:
            return "刚刚"
        elif diff < 3600:
            return f"{int(diff // 60)} 分钟前"
        elif diff < 86400:
            return f"{int(diff // 3600)} 小时前"
        elif diff < 604800:
            return f"{int(diff // 86400)} 天前"
        else:
            return DateTimeHelper.format_timestamp(ts)


class TextHelper:
    """文本处理工具"""

    @staticmethod
    def truncate(text: str, max_len: int = 50) -> str:
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."

    @staticmethod
    def count_words(text: str) -> int:
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        return chinese + english_words

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """粗略估算 token 数"""
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        other = len(text) - chinese
        return int(chinese * 1.5 + other * 0.25)

    @staticmethod
    def escape_html(text: str) -> str:
        return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    @staticmethod
    def mask_api_key(key: str) -> str:
        """遮蔽 API Key，只显示前4位和后4位"""
        if len(key) <= 12:
            return "****"
        return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


class FileHelper:
    """文件操作工具"""

    @staticmethod
    def ensure_dir(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def read_json(path: str, default: Any = None) -> Any:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    @staticmethod
    def write_json(path: str, data: Any) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def read_text(path: str) -> Optional[str]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            try:
                with open(path, "r", encoding="gbk") as f:
                    return f.read()
            except Exception:
                return None

    @staticmethod
    def write_text(path: str, content: str) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def get_file_extension(path: str) -> str:
        _, ext = os.path.splitext(path)
        return ext.lower()

    @staticmethod
    def get_filename(path: str) -> str:
        return os.path.basename(path)

    @staticmethod
    def file_size_str(path: str) -> str:
        try:
            size = os.path.getsize(path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except Exception:
            return "未知"


class EncryptionManager:
    """文件加密管理器 - 使用 PBKDF2 密钥派生 + XOR 加密"""

    @staticmethod
    def encrypt(data: str, password: str) -> str:
        """加密字符串，返回格式: base64(salt(16) + 密文)"""
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        data_bytes = data.encode('utf-8')
        encrypted = bytearray()
        for i, b in enumerate(data_bytes):
            encrypted.append(b ^ key[i % len(key)])
        combined = salt + bytes(encrypted)
        return base64.b64encode(combined).decode('utf-8')

    @staticmethod
    def decrypt(encrypted_str: str, password: str) -> str:
        """解密字符串"""
        try:
            combined = base64.b64decode(encrypted_str.encode('utf-8'))
            salt = combined[:16]
            encrypted_bytes = combined[16:]
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            decrypted = bytearray()
            for i, b in enumerate(encrypted_bytes):
                decrypted.append(b ^ key[i % len(key)])
            return decrypted.decode('utf-8')
        except Exception:
            raise ValueError("密码错误或数据损坏")

    @staticmethod
    def hash_password(password: str) -> str:
        """生成密码验证哈希"""
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        combined = salt + key
        return base64.b64encode(combined).decode('utf-8')

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """验证密码"""
        try:
            combined = base64.b64decode(stored_hash.encode('utf-8'))
            salt = combined[:16]
            stored_key = combined[16:]
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return key == stored_key
        except Exception:
            return False


class ClipboardHelper:
    """剪贴板工具"""

    @staticmethod
    def copy(text: str) -> bool:
        """复制文本到剪贴板"""
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception:
            pass
        try:
            import subprocess
            proc = subprocess.Popen(
                ["powershell", "-Command", "Set-Clipboard"],
                stdin=subprocess.PIPE, text=True
            )
            proc.communicate(input=text)
            return True
        except Exception:
            return False

    @staticmethod
    def paste() -> str:
        """从剪贴板获取文本"""
        try:
            import pyperclip
            return pyperclip.paste()
        except Exception:
            pass
        try:
            import subprocess
            proc = subprocess.Popen(
                ["powershell", "-Command", "Get-Clipboard"],
                stdout=subprocess.PIPE, text=True
            )
            return proc.communicate()[0].strip()
        except Exception:
            return ""


class Validator:
    """输入验证器"""

    @staticmethod
    def is_valid_api_key(key: str) -> bool:
        return bool(key and len(key) >= 8 and key.strip())

    @staticmethod
    def is_valid_url(url: str) -> bool:
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))

    @staticmethod
    def is_valid_session_name(name: str) -> bool:
        return bool(name and len(name.strip()) > 0 and len(name.strip()) <= 50)

    @staticmethod
    def is_valid_model_name(model: str) -> bool:
        return bool(model and len(model.strip()) > 0)


class Signal:
    """简单信号/槽机制"""

    def __init__(self):
        self._slots = []

    def connect(self, slot):
        if slot not in self._slots:
            self._slots.append(slot)

    def disconnect(self, slot):
        if slot in self._slots:
            self._slots.remove(slot)

    def emit(self, *args, **kwargs):
        for slot in self._slots:
            try:
                slot(*args, **kwargs)
            except Exception as e:
                print(f"Signal emit error: {e}")
