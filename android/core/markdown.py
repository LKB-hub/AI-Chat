#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 渲染器 - 纯解析功能，不依赖 tkinter
"""

import re
from typing import List, Tuple


class MarkdownRenderer:
    """简单的 Markdown 渲染器 - 纯后端版本"""

    # 代码语言关键词着色
    KEYWORDS = {
        "python": ["def", "class", "import", "from", "return", "if", "elif", "else",
                    "for", "while", "try", "except", "finally", "with", "as", "yield",
                    "lambda", "pass", "break", "continue", "and", "or", "not", "in",
                    "is", "None", "True", "False", "self", "raise", "global", "nonlocal",
                    "assert", "del", "async", "await"],
        "javascript": ["function", "class", "const", "let", "var", "return", "if", "else",
                       "for", "while", "switch", "case", "break", "continue", "try",
                       "catch", "finally", "throw", "new", "this", "typeof", "instanceof",
                       "import", "export", "default", "async", "await", "yield", "true",
                       "false", "null", "undefined", "void", "delete", "in", "of"],
        "java": ["public", "private", "protected", "class", "interface", "extends",
                 "implements", "static", "final", "abstract", "void", "int", "long",
                 "double", "float", "boolean", "char", "String", "return", "if",
                 "else", "for", "while", "switch", "case", "break", "continue",
                 "try", "catch", "finally", "throw", "throws", "new", "this",
                 "super", "null", "true", "false", "import", "package"],
        "c": ["int", "long", "double", "float", "char", "void", "struct", "enum",
              "union", "typedef", "const", "static", "extern", "register", "volatile",
              "return", "if", "else", "for", "while", "do", "switch", "case",
              "break", "continue", "default", "goto", "sizeof", "NULL", "true",
              "false", "include", "define", "ifdef", "ifndef", "endif"],
        "cpp": ["int", "long", "double", "float", "char", "void", "bool", "class",
                "struct", "enum", "union", "namespace", "using", "public", "private",
                "protected", "virtual", "override", "const", "static", "template",
                "typename", "return", "if", "else", "for", "while", "do", "switch",
                "case", "break", "continue", "new", "delete", "nullptr", "true",
                "false", "auto", "include", "define"],
        "go": ["func", "package", "import", "var", "const", "type", "struct", "interface",
               "map", "chan", "go", "select", "case", "default", "if", "else", "for",
               "range", "switch", "break", "continue", "return", "defer", "fallthrough",
               "nil", "true", "false", "make", "new", "len", "cap", "append", "copy"],
        "rust": ["fn", "let", "mut", "const", "static", "struct", "enum", "impl", "trait",
                 "pub", "use", "mod", "crate", "self", "super", "match", "if", "else",
                 "for", "while", "loop", "break", "continue", "return", "as", "in",
                 "ref", "move", "type", "where", "async", "await", "unsafe", "extern",
                 "true", "false", "Some", "None", "Ok", "Err"],
        "sql": ["SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
                "DELETE", "CREATE", "TABLE", "ALTER", "DROP", "INDEX", "JOIN", "LEFT",
                "RIGHT", "INNER", "OUTER", "ON", "AND", "OR", "NOT", "NULL", "IS",
                "IN", "BETWEEN", "LIKE", "ORDER", "BY", "GROUP", "HAVING", "LIMIT",
                "OFFSET", "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MAX", "MIN"],
        "html": ["html", "head", "body", "div", "span", "p", "a", "img", "ul", "ol",
                 "li", "table", "tr", "td", "th", "form", "input", "button", "select",
                 "option", "textarea", "h1", "h2", "h3", "h4", "h5", "h6", "script",
                 "style", "link", "meta", "title", "class", "id", "src", "href"],
        "css": ["color", "background", "margin", "padding", "border", "font", "display",
                "position", "width", "height", "top", "left", "right", "bottom",
                "flex", "grid", "align", "justify", "overflow", "opacity", "z-index",
                "transition", "animation", "transform", "none", "auto", "inherit"],
    }

    # 语言标识到文件后缀的映射
    LANG_TO_EXT = {
        "python": "py", "py": "py", "javascript": "js", "js": "js",
        "typescript": "ts", "ts": "ts", "java": "java", "c": "c",
        "cpp": "cpp", "cxx": "cpp", "c++": "cpp", "cc": "cpp",
        "csharp": "cs", "cs": "cs", "go": "go", "golang": "go",
        "rust": "rs", "ruby": "rb", "rb": "rb", "php": "php",
        "swift": "swift", "kotlin": "kt", "kt": "kt", "scala": "scala",
        "r": "r", "sql": "sql", "html": "html", "css": "css",
        "xml": "xml", "yaml": "yml", "yml": "yml", "json": "json",
        "markdown": "md", "md": "md", "shell": "sh", "bash": "sh",
        "sh": "sh", "zsh": "sh", "powershell": "ps1", "ps1": "ps1",
        "dockerfile": "dockerfile", "makefile": "mk", "perl": "pl",
        "lua": "lua", "matlab": "m", "haskell": "hs", "erlang": "erl",
        "elixir": "ex", "clojure": "clj", "groovy": "groovy",
        "dart": "dart", "julia": "jl", "fortran": "f90",
        "pascal": "pas", "vb": "vb", "vba": "bas",
        "objc": "m", "objectivec": "m", "asm": "asm",
        "svelte": "svelte", "vue": "vue", "jsx": "jsx", "tsx": "tsx",
        "toml": "toml", "ini": "ini", "cfg": "cfg", "conf": "conf",
        "protobuf": "proto", "graphql": "graphql", "proto": "proto",
        "text": "txt", "plaintext": "txt", "plain": "txt",
        "bat": "bat", "cmd": "bat",
        "latex": "tex", "tex": "tex", "bib": "bib",
        "diff": "diff", "patch": "diff",
    }

    @staticmethod
    def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
        """从文本中提取 Markdown 代码块"""
        pattern = r'```(\w*)\n(.*?)\n```'
        return re.findall(pattern, text, re.DOTALL)

    @staticmethod
    def get_extension(lang: str) -> str:
        """获取语言对应的文件后缀"""
        if not lang:
            return "txt"
        return MarkdownRenderer.LANG_TO_EXT.get(lang.lower(), lang.lower())

    @staticmethod
    def _parse_markdown(text: str) -> List[Tuple]:
        """解析 Markdown 文本为各部分"""
        parts = []
        code_pattern = r'```(\w*)\n(.*?)\n```'
        last_end = 0

        for match in re.finditer(code_pattern, text, re.DOTALL):
            before = text[last_end:match.start()]
            if before.strip():
                parts.extend(MarkdownRenderer._parse_inline(before))
            lang = match.group(1)
            code = match.group(2)
            parts.append(("code", code, lang))
            last_end = match.end()

        remaining = text[last_end:]
        if remaining.strip():
            parts.extend(MarkdownRenderer._parse_inline(remaining))

        return parts

    @staticmethod
    def _parse_inline(text: str) -> List[Tuple]:
        """解析行内 Markdown 元素"""
        parts = []
        lines = text.split("\n")

        for line in lines:
            if not line.strip():
                parts.append(("normal", "\n", ""))
                continue

            # 标题
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                parts.append(("heading", line + "\n", ""))
                continue

            # 列表项
            list_match = re.match(r'^(\s*[-*+]\s+|\s*\d+\.\s+)(.+)$', line)
            if list_match:
                parts.append(("list_item", line + "\n", ""))
                continue

            # 引用
            quote_match = re.match(r'^>\s*(.+)$', line)
            if quote_match:
                parts.append(("blockquote", line + "\n", ""))
                continue

            # 加粗
            line = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            # 斜体
            line = re.sub(r'\*(.+?)\*', r'\1', line)
            # 链接
            line = re.sub(r'\[(.+?)\]\((.+?)\)', r'\1', line)

            parts.append(("normal", line + "\n", ""))

        return parts

    @staticmethod
    def render_to_plain_text(text: str) -> str:
        """将 Markdown 文本渲染为纯文本（去掉标记符号）"""
        parts = MarkdownRenderer._parse_markdown(text)
        result = []
        for part_type, content, lang in parts:
            if part_type == "code":
                result.append(f"```{lang}\n{content}\n```")
            else:
                result.append(content)
        return "".join(result)

    @staticmethod
    def render_to_html(text: str) -> str:
        """将 Markdown 文本渲染为简单的 HTML 片段"""
        from .helpers import TextHelper
        parts = MarkdownRenderer._parse_markdown(text)
        html_parts = []
        for part_type, content, lang in parts:
            if part_type == "code":
                escaped = TextHelper.escape_html(content)
                lang_label = lang if lang else "code"
                html_parts.append(
                    f'<pre><code class="language-{lang_label}">{escaped}</code></pre>'
                )
            elif part_type == "heading":
                level = 1
                m = re.match(r'^(#{1,6})\s+', content)
                if m:
                    level = len(m.group(1))
                text_content = re.sub(r'^#{1,6}\s+', '', content)
                html_parts.append(f'<h{level}>{text_content.strip()}</h{level}>')
            elif part_type == "list_item":
                text_content = re.sub(r'^\s*[-*+]\s+|\s*\d+\.\s+', '', content)
                html_parts.append(f'<li>{text_content.strip()}</li>')
            elif part_type == "blockquote":
                text_content = re.sub(r'^>\s*', '', content)
                html_parts.append(f'<blockquote>{text_content.strip()}</blockquote>')
            elif part_type == "normal":
                escaped = TextHelper.escape_html(content)
                html_parts.append(f'<p>{escaped}</p>')
        return "\n".join(html_parts)
