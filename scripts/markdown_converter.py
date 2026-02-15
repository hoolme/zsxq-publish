#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识星球发布工具 - Markdown 转换模块

将 Markdown 转换为知识星球支持的两种格式:
1. 话题文本格式: 纯文本 + <e type="text_bold"/> + <e type="hashtag"/> 标签
2. 文章 HTML 格式: 标准 HTML（<p>, <h2>, <strong>, <img> 等）
"""

import re
from typing import List, Tuple
from urllib.parse import quote


def markdown_to_article_html(md_text: str) -> str:
    """将 Markdown 转换为知识星球文章 HTML 格式"""
    try:
        import markdown
        html = markdown.markdown(
            md_text,
            extensions=["extra", "nl2br", "sane_lists"],
        )
    except ImportError:
        html = _simple_md_to_html(md_text)

    return html


def markdown_to_topic_text(md_text: str, title: str = "") -> str:
    """将 Markdown 转换为知识星球话题文本格式

    话题格式:
    - 标题用 <e type="text_bold" title="URL编码标题" /> 标签
    - 正文为纯文本（去除 Markdown 标记）
    - 标签用 <e type="hashtag" title="URL编码#标签#" /> 标签
    """
    parts = []

    # 添加加粗标题
    if title:
        encoded_title = quote(title, safe="")
        parts.append(f'<e type="text_bold" title="{encoded_title}" />')
        parts.append("")  # 空行

    # 转换正文为纯文本
    plain_text = _strip_markdown(md_text)
    parts.append(plain_text)

    return "\n".join(parts)


def extract_title_from_markdown(md_text: str) -> Tuple[str, str]:
    """从 Markdown 中提取标题和正文

    Returns:
        (title, body) 元组
    """
    lines = md_text.strip().split("\n")

    title = ""
    body_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 匹配 # 标题
        match = re.match(r"^#{1,3}\s+(.+)$", stripped)
        if match:
            title = match.group(1).strip()
            body_start = i + 1
            break
        # 跳过空行
        if stripped:
            # 第一个非空非标题行作为标题
            title = stripped
            body_start = i + 1
            break

    body = "\n".join(lines[body_start:]).strip()
    return title, body


def format_hashtags(tags: List[str]) -> str:
    """将标签列表格式化为知识星球标签格式"""
    formatted = []
    for tag in tags:
        tag = tag.strip().strip("#")
        if tag:
            encoded = quote(f"#{tag}#", safe="")
            formatted.append(f'<e type="hashtag" title="{encoded}" />')
    return " ".join(formatted)


def _strip_markdown(md_text: str) -> str:
    """去除 Markdown 标记，转为纯文本"""
    text = md_text

    # 去除标题标记
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # 去除加粗和斜体
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)

    # 转换链接 [text](url) → text (url)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text)

    # 去除图片标记
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # 去除代码块标记
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`(.+?)`", r"\1", text)

    # 去除水平线
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # 去除列表标记但保留内容
    text = re.sub(r"^[\s]*[-*+]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)

    # 清理多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _simple_md_to_html(md_text: str) -> str:
    """简单的 Markdown → HTML 转换（markdown 库不可用时的回退方案）"""
    html_parts = []
    lines = md_text.split("\n")
    in_code_block = False
    in_list = False

    for line in lines:
        # 代码块
        if line.strip().startswith("```"):
            if in_code_block:
                html_parts.append("</code></pre>")
                in_code_block = False
            else:
                html_parts.append("<pre><code>")
                in_code_block = True
            continue

        if in_code_block:
            html_parts.append(line)
            continue

        stripped = line.strip()

        # 空行
        if not stripped:
            if in_list:
                in_list = False
            html_parts.append("<p><br></p>")
            continue

        # 标题
        h_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if h_match:
            level = len(h_match.group(1))
            content = _inline_format(h_match.group(2))
            html_parts.append(f"<h{level}><strong>{content}</strong></h{level}>")
            continue

        # 水平线
        if re.match(r"^[-*_]{3,}$", stripped):
            html_parts.append('<hr class="article-hr" style="height: 0px">')
            continue

        # 普通段落（应用行内格式）
        content = _inline_format(stripped)
        html_parts.append(f"<p>{content}</p>")

    return "\n".join(html_parts)


def _inline_format(text: str) -> str:
    """处理行内 Markdown 格式"""
    # 加粗
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # 斜体
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # 行内代码
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # 链接
    text = re.sub(
        r"\[(.+?)\]\((.+?)\)",
        r'<a href="\2" rel="noopener noreferrer" target="_blank">\1</a>',
        text,
    )
    return text
