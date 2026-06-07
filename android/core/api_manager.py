#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 密钥管理器
"""

import json
import os
from typing import Optional, Dict, List, Any
from openai import OpenAI
import requests


class APIKeyManager:
    """API 密钥管理器"""

    DEFAULT_CONFIGS = {
        "SiliconFlow": {
            "api_key": "sk-jpiwvjcgzbgfobhqmwimfsxxqnwpfklfzeenuypcgmahabsa",
            "base_url": "https://api.siliconflow.cn/v1",
            "model": "Pro/zai-org/GLM-4.7",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        "Moonshot": {
            "api_key": "",
            "base_url": "https://api.moonshot.cn/v1",
            "model": "moonshot-v1-8k",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        "DeepSeek": {
            "api_key": "",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-v4-pro",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "reasoning_effort": "high",
            "thinking_enabled": True,
        },
        "OpenAI": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        "ZhipuAI": {
            "api_key": "",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4-flash",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        # ---- 本地模型预设 ----
        "Ollama (本地)": {
            "api_key": "ollama",
            "base_url": "http://localhost:11434/v1",
            "model": "llama3",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "is_local": True,
        },
        "LM Studio (本地)": {
            "api_key": "not-needed",
            "base_url": "http://localhost:1234/v1",
            "model": "local-model",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "is_local": True,
        },
    }

    def __init__(self):
        self.configs: Dict[str, Dict] = {}
        self.current_name: str = "SiliconFlow"
        self._client: Optional[OpenAI] = None
        self.load()

    def load(self) -> None:
        """从本地文件加载配置（支持加密）"""
        from . import encryption_enabled, encryption_password, API_KEYS_FILE
        from .helpers import FileHelper, EncryptionManager

        if encryption_enabled and encryption_password and os.path.exists(API_KEYS_FILE):
            try:
                encrypted = FileHelper.read_text(API_KEYS_FILE)
                if encrypted:
                    decrypted = EncryptionManager.decrypt(encrypted.strip(), encryption_password)
                    data = json.loads(decrypted)
                    if "keys" in data:
                        self.configs = data["keys"]
                        self.current_name = data.get("current", "SiliconFlow")
                        self._init_client()
                        return
            except Exception:
                pass

        # 普通读取
        data = FileHelper.read_json(API_KEYS_FILE, {})
        if data and "keys" in data:
            self.configs = data["keys"]
            self.current_name = data.get("current", "SiliconFlow")
        else:
            # 首次运行，初始化默认配置
            for name, cfg in self.DEFAULT_CONFIGS.items():
                self.configs[name] = cfg.copy()
            self.current_name = "SiliconFlow"
        if self.current_name not in self.configs:
            if self.configs:
                self.current_name = list(self.configs.keys())[0]
            else:
                self.configs["SiliconFlow"] = self.DEFAULT_CONFIGS["SiliconFlow"].copy()
                self.current_name = "SiliconFlow"
        self._init_client()

    def save(self) -> None:
        """保存配置到本地文件（支持加密）"""
        from . import encryption_enabled, encryption_password, API_KEYS_FILE
        from .helpers import FileHelper, EncryptionManager

        data = {
            "current": self.current_name,
            "keys": self.configs,
        }
        content = json.dumps(data, ensure_ascii=False, indent=2)
        if encryption_enabled and encryption_password:
            encrypted = EncryptionManager.encrypt(content, encryption_password)
            FileHelper.write_text(API_KEYS_FILE, encrypted)
        else:
            FileHelper.write_json(API_KEYS_FILE, data)

    def _init_client(self) -> None:
        """初始化 OpenAI 客户端"""
        cfg = self.get_current_config()
        if cfg and cfg.get("api_key"):
            try:
                self._client = OpenAI(
                    api_key=cfg["api_key"],
                    base_url=cfg["base_url"]
                )
            except Exception as e:
                print(f"初始化客户端失败: {e}")
                self._client = None
        else:
            self._client = None

    def get_client(self) -> Optional[OpenAI]:
        return self._client

    def get_current_config(self) -> Optional[Dict]:
        return self.configs.get(self.current_name)

    def get_current_model(self) -> str:
        cfg = self.get_current_config()
        return cfg.get("model", "unknown") if cfg else "unknown"

    def get_current_info(self) -> str:
        """获取当前配置的显示信息"""
        return f"{self.current_name}  |  {self.get_current_model()}"

    def switch_to(self, name: str) -> bool:
        """切换到指定配置"""
        from . import signal_api_key_changed
        if name in self.configs:
            self.current_name = name
            self._init_client()
            self.save()
            signal_api_key_changed.emit()
            return True
        return False

    def add_config(self, name: str, api_key: str, base_url: str, model: str,
                   max_tokens: int = 4096, temperature: float = 0.7,
                   top_p: float = 0.9,
                   reasoning_effort: str = None,
                   thinking_enabled: bool = False) -> bool:
        """添加新配置"""
        from . import signal_api_key_changed
        from .helpers import Validator
        if name in self.configs:
            return False
        if not Validator.is_valid_api_key(api_key):
            return False
        if not Validator.is_valid_url(base_url):
            return False
        cfg = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        if reasoning_effort:
            cfg["reasoning_effort"] = reasoning_effort
        if thinking_enabled:
            cfg["thinking_enabled"] = True
        self.configs[name] = cfg
        self.current_name = name
        self._init_client()
        self.save()
        signal_api_key_changed.emit()
        return True

    def update_config(self, name: str, **kwargs) -> bool:
        """更新配置"""
        from . import signal_api_key_changed
        if name not in self.configs:
            return False
        cfg = self.configs[name]
        for key, value in kwargs.items():
            cfg[key] = value
        if name == self.current_name:
            self._init_client()
        self.save()
        signal_api_key_changed.emit()
        return True

    def delete_config(self, name: str) -> bool:
        """删除配置"""
        from . import signal_api_key_changed
        if len(self.configs) <= 1:
            return False
        if name not in self.configs:
            return False
        del self.configs[name]
        if self.current_name == name:
            self.current_name = list(self.configs.keys())[0]
            self._init_client()
        self.save()
        signal_api_key_changed.emit()
        return True

    def list_configs(self) -> List[str]:
        return list(self.configs.keys())

    def get_config(self, name: str) -> Optional[Dict]:
        return self.configs.get(name)

    def mask_current_key(self) -> str:
        from .helpers import TextHelper
        cfg = self.get_current_config()
        if cfg:
            return TextHelper.mask_api_key(cfg.get("api_key", ""))
        return "****"

    # ---- 本地模型支持 ----

    def is_local(self, name: str = None) -> bool:
        """判断指定配置是否为本地模型"""
        cfg = self.get_config(name) if name else self.get_current_config()
        return cfg.get("is_local", False) if cfg else False

    def fetch_local_models(self, name_or_cfg=None) -> List[str]:
        """从本地 API 获取可用模型列表
        支持: Ollama (/api/tags), LM Studio (/v1/models), OpenAI 兼容 (/v1/models)
        name_or_cfg: 配置名称(str) 或 配置字典(dict)
        """
        if isinstance(name_or_cfg, dict):
            cfg = name_or_cfg
        elif isinstance(name_or_cfg, str):
            cfg = self.get_config(name_or_cfg)
        else:
            cfg = self.get_current_config()
        if not cfg:
            return []

        base_url = cfg["base_url"].rstrip("/")
        api_key = cfg.get("api_key", "")
        models = []

        # 1. 尝试 OpenAI 兼容端点 /v1/models
        try:
            resp = requests.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("data", []):
                    mid = m.get("id", m.get("model", ""))
                    if mid:
                        models.append(mid)
                if models:
                    return models
        except Exception:
            pass

        # 2. 尝试 Ollama 端点 /api/tags
        try:
            # 从 /v1 回退到根地址
            ollama_base = base_url.replace("/v1", "").replace("/v1/", "")
            resp = requests.get(
                f"{ollama_base}/api/tags",
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("models", []):
                    mid = m.get("name", "")
                    if mid:
                        models.append(mid)
                return models
        except Exception:
            pass

        return models

    def ping_local(self, name: str = None) -> Dict:
        """测试本地模型是否可达"""
        cfg = self.get_config(name) if name else self.get_current_config()
        if not cfg:
            return {"success": False, "error": "未找到配置"}

        base_url = cfg["base_url"].rstrip("/")
        try:
            resp = requests.get(base_url.replace("/v1", ""), timeout=5)
            return {"success": resp.status_code < 500, "status": resp.status_code}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "无法连接，请确认本地服务已启动"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---- 余额查询 ----

    # 各平台余额查询 API 端点
    BALANCE_APIS = {
        "SiliconFlow": "https://api.siliconflow.cn/v1/user/info",
        "DeepSeek": "https://api.deepseek.com/user/balance",
        "Moonshot": None,
        "OpenAI": None,
        "ZhipuAI": None,
    }

    def check_balance(self) -> Dict:
        """查询当前 API 配置的余额信息"""
        cfg = self.get_current_config()
        if not cfg:
            return {"success": False, "error": "未找到当前配置"}

        name = self.current_name
        api_key = cfg.get("api_key", "")
        base_url = cfg.get("base_url", "")

        if not api_key:
            return {"success": False, "error": "API Key 未设置"}

        if "siliconflow" in base_url.lower():
            return self._check_siliconflow_balance(api_key)
        elif "deepseek" in base_url.lower():
            return self._check_deepseek_balance(api_key)
        else:
            return {
                "success": False,
                "error": f"{name} 暂不支持余额查询",
                "provider": name,
            }

    def _check_siliconflow_balance(self, api_key: str) -> Dict:
        """查询 SiliconFlow 余额"""
        for base in ["https://api.siliconflow.com", "https://api.siliconflow.cn"]:
            try:
                resp = requests.get(
                    f"{base}/v1/user/info",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                user_data = data.get("data", data)
                details = []
                total_balance = user_data.get("totalBalance", None)
                if total_balance is not None:
                    try:
                        details.append(("总余额", f"${float(total_balance):.4f}"))
                    except (ValueError, TypeError):
                        details.append(("总余额", str(total_balance)))
                balance = user_data.get("balance", None)
                if balance is not None:
                    try:
                        details.append(("可用余额", f"${float(balance):.4f}"))
                    except (ValueError, TypeError):
                        details.append(("可用余额", str(balance)))
                charge_balance = user_data.get("chargeBalance", None)
                if charge_balance is not None:
                    try:
                        details.append(("充值余额", f"${float(charge_balance):.4f}"))
                    except (ValueError, TypeError):
                        details.append(("充值余额", str(charge_balance)))
                status = user_data.get("status", None)
                if status is not None:
                    status_map = {"normal": "正常", "active": "活跃"}
                    details.append(("账户状态", status_map.get(str(status), str(status))))
                if not details:
                    for key, val in user_data.items():
                        if key not in ("id",) and val is not None and str(val).strip():
                            details.append((key, str(val)))
                return {
                    "success": True,
                    "provider": "SiliconFlow",
                    "raw": data,
                    "details": details,
                }
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.ConnectionError:
                continue
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else "未知"
                if status_code == 401:
                    return {"success": False, "error": f"认证失败 (HTTP {status_code})：请检查 API Key 是否正确"}
                if status_code == 404:
                    continue
                return {"success": False, "error": f"HTTP 错误 {status_code}：请稍后重试"}
            except Exception:
                continue
        return {"success": False, "error": "无法连接到 SiliconFlow 服务器，请检查网络"}

    def _check_deepseek_balance(self, api_key: str) -> Dict:
        """查询 DeepSeek 余额"""
        try:
            resp = requests.get(
                "https://api.deepseek.com/user/balance",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            balance_infos = data.get("balance_infos", [])
            details = []
            if balance_infos:
                for info in balance_infos:
                    currency = info.get("currency", "?")
                    total = info.get("total_balance", "未知")
                    granted = info.get("granted_balance", "0")
                    topped = info.get("topped_up_balance", "0")
                    details.append((f"总余额 ({currency})", str(total)))
                    details.append((f"赠送余额 ({currency})", str(granted)))
                    details.append((f"充值余额 ({currency})", str(topped)))
            else:
                for key, label in [("total_balance", "总余额"), ("balance", "余额")]:
                    if key in data:
                        details.append((label, str(data[key])))
            if not details:
                details.append(("原始数据", json.dumps(data, ensure_ascii=False)))
            return {
                "success": True,
                "provider": "DeepSeek",
                "raw": data,
                "details": details,
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时，请稍后重试"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "网络连接失败"}
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "未知"
            return {"success": False, "error": f"HTTP 错误 {status_code}: 请检查 API Key 是否正确"}
        except Exception as e:
            return {"success": False, "error": str(e)}
