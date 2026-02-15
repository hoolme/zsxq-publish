#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识星球发布工具 - 认证模块"""

import json
import time
import uuid
from typing import Dict, Tuple
from config import AUTH_FILE, API_VERSION


def load_auth() -> Tuple[Dict[str, str], Dict[str, str]]:
    """从 auth.json 加载认证信息，返回 (cookies, headers)"""
    if not AUTH_FILE.exists():
        raise FileNotFoundError(
            f"认证文件不存在: {AUTH_FILE}\n"
            "请按以下步骤创建:\n"
            "1. 打开 https://wx.zsxq.com/dweb/ 并登录\n"
            "2. F12 → Network → 找到 api.zsxq.com 请求\n"
            "3. 复制 Cookie 中的 zsxq_access_token\n"
            "4. 创建 auth.json 文件"
        )

    with open(AUTH_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    cookies = config.get("cookies", {})
    headers = config.get("headers", {})

    if "zsxq_access_token" not in cookies:
        raise ValueError("auth.json 中缺少 zsxq_access_token")

    return cookies, headers


def build_request_headers(base_headers: Dict[str, str]) -> Dict[str, str]:
    """构建完整的请求头（包含签名相关字段）"""
    timestamp = str(int(time.time()))
    request_id = _generate_request_id()

    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://wx.zsxq.com",
        "referer": "https://wx.zsxq.com/",
        "x-request-id": request_id,
        "x-version": API_VERSION,
        "x-timestamp": timestamp,
    }

    # 合并 auth.json 中的基础头（User-Agent 等）
    if "User-Agent" in base_headers:
        headers["user-agent"] = base_headers["User-Agent"]
    if "Referer" in base_headers:
        headers["referer"] = base_headers["Referer"]

    return headers


def _generate_request_id() -> str:
    """生成知识星球格式的 request-id"""
    raw = uuid.uuid4().hex
    # 知识星球的 request-id 格式略有不同：缩短的 UUID 带连字符
    return f"{raw[:9]}-{raw[9:13]}-{raw[13:17]}-{raw[17:21]}-{raw[21:32]}"


def check_auth_status(cookies: Dict[str, str], headers: Dict[str, str]) -> bool:
    """检查认证是否有效"""
    import requests
    from config import ENDPOINTS

    try:
        req_headers = build_request_headers(headers)
        resp = requests.get(
            ENDPOINTS["settings"],
            headers=req_headers,
            cookies=cookies,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("succeeded"):
                return True
        return False
    except Exception:
        return False
