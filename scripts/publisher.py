#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识星球发布工具 - 发布模块

支持两种发布模式:
1. 话题发布（短内容）: POST /v2/groups/{group_id}/topics
2. 文章发布（长内容）: 先 POST /v2/articles 创建文章，再 POST topics 引用文章
"""

import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests

from config import ENDPOINTS, GROUP_ID, PUBLISH_HISTORY_FILE
from auth import load_auth, build_request_headers
from markdown_converter import (
    markdown_to_article_html,
    markdown_to_topic_text,
    extract_title_from_markdown,
    format_hashtags,
)


class ZsxqPublisher:
    """知识星球内容发布器"""

    def __init__(self):
        self.cookies, self.base_headers = load_auth()
        self.history = self._load_history()

    def publish_topic(
        self, text: str, title: str = "", tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """发布话题（短内容）

        Args:
            text: 话题正文
            title: 可选标题（会加粗显示）
            tags: 可选标签列表
        Returns:
            API 响应数据
        """
        # 构建话题文本
        topic_text = markdown_to_topic_text(text, title=title)

        # 添加标签
        if tags:
            topic_text += "\n" + format_hashtags(tags)

        # 构建请求体
        payload = {"req_data": {"type": "talk", "text": topic_text}}

        # 发送请求
        result = self._post(ENDPOINTS["create_topic"], payload)

        if result and result.get("succeeded"):
            topic_data = result.get("resp_data", {}).get("topic", {})
            self._record_history(
                publish_type="topic",
                title=title or text[:50],
                topic_id=topic_data.get("topic_id"),
                status=topic_data.get("process_status", "unknown"),
            )
            print(f"  [OK] 话题发布成功!")
            print(f"  话题ID: {topic_data.get('topic_id')}")
            print(f"  状态: {topic_data.get('process_status', 'unknown')}")
        else:
            print(f"  [FAIL] 话题发布失败")
            if result:
                print(f"  响应: {json.dumps(result, ensure_ascii=False)}")

        return result or {}

    def publish_article(
        self, md_content: str, title: str = "", tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """发布文章（长内容，两步流程）

        Step 1: POST /v2/articles 创建文章 → 获取 article_id
        Step 2: POST /v2/groups/{id}/topics 创建引用文章的话题

        Args:
            md_content: Markdown 格式的文章内容
            title: 文章标题（如果为空，从 Markdown 中提取）
            tags: 可选标签列表
        Returns:
            API 响应数据
        """
        # 提取标题和正文
        if not title:
            title, body = extract_title_from_markdown(md_content)
        else:
            _, body = extract_title_from_markdown(md_content)

        if not title:
            title = "未命名文章"

        # Step 1: 创建文章
        print(f"  Step 1: 创建文章 '{title}'...")
        article_html = markdown_to_article_html(md_content)

        article_payload = {
            "req_data": {
                "title": title,
                "content": article_html,
            }
        }

        article_result = self._post(ENDPOINTS["create_article"], article_payload)

        if not article_result or not article_result.get("succeeded"):
            print(f"  [FAIL] 文章创建失败")
            if article_result:
                print(f"  响应: {json.dumps(article_result, ensure_ascii=False)}")
            return article_result or {}

        article_id = article_result["resp_data"]["article_id"]
        article_url = article_result["resp_data"]["article_url"]
        print(f"  [OK] 文章已创建: {article_id}")
        print(f"  文章链接: {article_url}")

        # 适当延迟，避免请求过快
        time.sleep(random.uniform(0.5, 1.5))

        # Step 2: 创建话题引用文章
        print(f"  Step 2: 创建话题引用文章...")

        # 构建话题文本（摘要 + 标签）
        summary = body[:200] if body else ""
        topic_text = markdown_to_topic_text(summary, title=title)

        if tags:
            topic_text += "\n" + format_hashtags(tags)

        topic_payload = {
            "req_data": {
                "type": "talk",
                "text": topic_text,
                "article_id": article_id,
            }
        }

        topic_result = self._post(ENDPOINTS["create_topic"], topic_payload)

        if topic_result and topic_result.get("succeeded"):
            topic_data = topic_result.get("resp_data", {}).get("topic", {})
            self._record_history(
                publish_type="article",
                title=title,
                topic_id=topic_data.get("topic_id"),
                article_id=article_id,
                article_url=article_url,
                status=topic_data.get("process_status", "unknown"),
            )
            print(f"  [OK] 文章发布成功!")
            print(f"  话题ID: {topic_data.get('topic_id')}")
            print(f"  文章ID: {article_id}")
            print(f"  文章链接: {article_url}")
            print(f"  状态: {topic_data.get('process_status', 'unknown')}")
        else:
            print(f"  [WARN] 文章已创建但话题关联失败")
            print(f"  文章ID: {article_id} (可手动关联)")
            self._record_history(
                publish_type="article",
                title=title,
                article_id=article_id,
                article_url=article_url,
                status="topic_failed",
            )

        return topic_result or article_result or {}

    def publish_file(
        self, file_path: str, mode: str = "auto", tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """发布文件

        Args:
            file_path: Markdown 文件路径
            mode: 发布模式 - "auto" (自动判断), "topic" (话题), "article" (文章)
            tags: 可选标签列表
        """
        from pathlib import Path
        from config import ARTICLE_THRESHOLD

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        md_content = path.read_text(encoding="utf-8")
        title, _ = extract_title_from_markdown(md_content)

        print(f"发布文件: {path.name}")
        print(f"标题: {title}")
        print(f"字符数: {len(md_content)}")

        # 自动判断模式
        if mode == "auto":
            mode = "article" if len(md_content) > ARTICLE_THRESHOLD else "topic"
            print(f"自动选择模式: {mode}")

        if mode == "article":
            return self.publish_article(md_content, title=title, tags=tags)
        else:
            return self.publish_topic(md_content, title=title, tags=tags)

    def _post(self, url: str, payload: Dict) -> Optional[Dict]:
        """发送 POST 请求"""
        headers = build_request_headers(self.base_headers)

        try:
            resp = requests.post(
                url,
                headers=headers,
                cookies=self.cookies,
                json=payload,
                timeout=30,
            )

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                print("  [ERROR] Cookie 已过期，请运行 login 命令重新登录授权")
                return None
            else:
                print(f"  [ERROR] HTTP {resp.status_code}: {resp.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            print("  [ERROR] 请求超时")
            return None
        except requests.exceptions.ConnectionError:
            print("  [ERROR] 网络连接失败")
            return None
        except Exception as e:
            print(f"  [ERROR] 请求异常: {e}")
            return None

    def _record_history(self, **kwargs):
        """记录发布历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "group_id": GROUP_ID,
            **kwargs,
        }
        self.history.append(record)
        self._save_history()

    def _load_history(self) -> list:
        """加载发布历史"""
        if PUBLISH_HISTORY_FILE.exists():
            try:
                with open(PUBLISH_HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return []
        return []

    def _save_history(self):
        """保存发布历史"""
        try:
            with open(PUBLISH_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  [WARN] 保存发布历史失败: {e}")

    def get_history(self, count: int = 10) -> list:
        """获取最近的发布历史"""
        return self.history[-count:]
