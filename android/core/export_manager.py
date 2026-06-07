#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出管理器：支持 TXT、Markdown、HTML、JSON 格式导出
"""

import json
import re
from typing import List, Dict


class ExportManager:
    """聊天记录导出管理器"""

    @staticmethod
    def export_to_txt(session_name: str, messages: List[Dict], filepath: str) -> bool:
        """导出为纯文本"""
        from .helpers import DateTimeHelper, FileHelper
        try:
            lines = [f"会话: {session_name}", f"导出时间: {DateTimeHelper.now_str()}", "" + "=" * 60, ""]
            for msg in messages:
                role = "你" if msg["role"] == "user" else "AI"
                content = msg.get("content", "")
                lines.append(f"{role}: {content}")
                lines.append("" + "-" * 40)
            lines.append("")
            content = "\n".join(lines)
            return FileHelper.write_text(filepath, content)
        except Exception as e:
            print(f"导出TXT失败: {e}")
            return False

    @staticmethod
    def export_to_markdown(session_name: str, messages: List[Dict], filepath: str) -> bool:
        """导出为 Markdown"""
        from .helpers import DateTimeHelper, FileHelper
        try:
            lines = [f"# {session_name}", "", f"> 导出时间: {DateTimeHelper.now_str()}", "", "---", ""]
            for msg in messages:
                if msg["role"] == "user":
                    lines.append(f"## 你")
                else:
                    lines.append(f"## AI")
                lines.append("")
                lines.append(msg.get("content", ""))
                lines.append("")
                lines.append("---")
                lines.append("")
            content = "\n".join(lines)
            return FileHelper.write_text(filepath, content)
        except Exception as e:
            print(f"导出Markdown失败: {e}")
            return False

    @staticmethod
    def export_to_html(session_name: str, messages: List[Dict], filepath: str) -> bool:
        """导出为 HTML"""
        from .helpers import DateTimeHelper, TextHelper, FileHelper
        try:
            html_parts = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{TextHelper.escape_html(session_name)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: #f5f6fa; padding: 20px; max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #1a1a1a; margin-bottom: 8px; font-size: 24px; }}
        .meta {{ color: #888; font-size: 14px; margin-bottom: 20px; }}
        .message {{ background: white; border-radius: 12px; padding: 16px 20px;
                    margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
        .user {{ border-left: 4px solid #0084ff; }}
        .assistant {{ border-left: 4px solid #00a67e; }}
        .role {{ font-weight: bold; font-size: 14px; margin-bottom: 8px; }}
        .user .role {{ color: #0084ff; }}
        .assistant .role {{ color: #00a67e; }}
        .content {{ color: #333; line-height: 1.6; white-space: pre-wrap; }}
        .content code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px;
                        font-family: Consolas, monospace; font-size: 13px; }}
        .content pre {{ background: #1e1e2e; color: #e0e0e0; padding: 16px;
                       border-radius: 8px; overflow-x: auto; margin: 8px 0; }}
        .content pre code {{ background: none; color: inherit; padding: 0; }}
        hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 16px 0; }}
    </style>
</head>
<body>
    <h1>{TextHelper.escape_html(session_name)}</h1>
    <p class="meta">导出时间: {DateTimeHelper.now_str()}</p>
    <hr>
"""
            ]
            for msg in messages:
                role_cn = "你" if msg["role"] == "user" else "AI"
                css_class = msg["role"]
                content = TextHelper.escape_html(msg.get("content", ""))
                content = re.sub(r'```(\w*)\n(.*?)\n```',
                                r'<pre><code>\2</code></pre>', content, flags=re.DOTALL)
                content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)
                content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
                content = content.replace("\n", "<br>")
                html_parts.append(f"""    <div class="message {css_class}">
        <div class="role">{role_cn}</div>
        <div class="content">{content}</div>
    </div>
""")
            html_parts.append("</body>\n</html>")
            content = "\n".join(html_parts)
            return FileHelper.write_text(filepath, content)
        except Exception as e:
            print(f"导出HTML失败: {e}")
            return False

    @staticmethod
    def export_to_json(session_name: str, messages: List[Dict], filepath: str) -> bool:
        """导出为 JSON"""
        from .helpers import DateTimeHelper, FileHelper
        try:
            data = {
                "session_name": session_name,
                "export_time": DateTimeHelper.now_str(),
                "message_count": len(messages),
                "messages": messages,
            }
            return FileHelper.write_json(filepath, data)
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return False

    @staticmethod
    def export_all_sessions(sessions: Dict[str, List[Dict]], filepath: str) -> bool:
        """导出所有会话"""
        from .helpers import DateTimeHelper, FileHelper
        try:
            data = {
                "export_time": DateTimeHelper.now_str(),
                "session_count": len(sessions),
                "sessions": {},
            }
            for name, messages in sessions.items():
                data["sessions"][name] = {
                    "message_count": len(messages),
                    "messages": messages,
                }
            return FileHelper.write_json(filepath, data)
        except Exception as e:
            print(f"导出全部会话失败: {e}")
            return False
