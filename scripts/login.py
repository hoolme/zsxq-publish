#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识星球发布工具 - 浏览器登录模块

使用 Selenium 打开知识星球登录页面，等待用户扫码登录，
成功后提取 Cookie 并持久化到 auth.json。
"""

import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

from config import AUTH_FILE


LOGIN_URL = "https://wx.zsxq.com/login"
POST_LOGIN_URL_PREFIX = "https://wx.zsxq.com/"
COOKIE_NAME = "zsxq_access_token"
MAX_WAIT_SECONDS = 120


def browser_login(headless: bool = False, timeout: int = MAX_WAIT_SECONDS) -> bool:
    """打开浏览器登录知识星球，登录成功后保存 Cookie

    Args:
        headless: 是否无头模式（默认否，需要用户扫码）
        timeout: 最大等待时间（秒）

    Returns:
        True 表示登录成功并已保存，False 表示失败或超时
    """
    driver = _create_driver(headless)
    if driver is None:
        return False

    try:
        print(f"[login] 正在打开登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        print(f"[login] 请在浏览器中扫码登录（{timeout}秒超时）...")

        # 等待登录成功（检测 cookie 出现）
        token = _wait_for_login(driver, timeout)

        if not token:
            print("[login] 登录超时或失败")
            return False

        # 提取完整信息
        cookies = _extract_cookies(driver)
        headers = _extract_headers(driver)

        # 保存到 auth.json
        _save_auth(cookies, headers)

        print(f"[login] 登录成功！Cookie 已保存到 {AUTH_FILE}")
        print(f"[login] zsxq_access_token: {token[:20]}...")
        return True

    except Exception as e:
        print(f"[login] 登录过程出错: {e}")
        return False

    finally:
        driver.quit()


def _create_driver(headless: bool = False) -> Optional[Any]:
    """创建 Selenium WebDriver（优先 Chrome，回退 Edge）"""
    driver = _try_chrome(headless)
    if driver:
        return driver

    driver = _try_edge(headless)
    if driver:
        return driver

    print("[login] 未找到可用的浏览器（需要 Chrome 或 Edge）")
    print("[login] 请安装 Chrome: https://www.google.com/chrome/")
    return None


def _try_chrome(headless: bool) -> Optional[Any]:
    """尝试创建 Chrome WebDriver"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=500,700")

        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception:
        return None


def _try_edge(headless: bool) -> Optional[Any]:
    """尝试创建 Edge WebDriver"""
    try:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        from selenium.webdriver.edge.service import Service

        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=500,700")

        service = Service()
        driver = webdriver.Edge(service=service, options=options)
        return driver
    except Exception:
        return None


def _wait_for_login(driver: Any, timeout: int) -> Optional[str]:
    """轮询等待登录成功，返回 access_token 或 None"""
    start = time.time()
    last_msg_time = start

    while time.time() - start < timeout:
        # 检查 cookie
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie.get("name") == COOKIE_NAME:
                value = cookie.get("value", "")
                if value:
                    return value

        # 每 15 秒提醒一次
        elapsed = time.time() - start
        if elapsed - (last_msg_time - start) >= 15:
            remaining = timeout - int(elapsed)
            print(f"[login] 等待扫码中... 剩余 {remaining} 秒")
            last_msg_time = time.time()

        time.sleep(2)

    return None


def _extract_cookies(driver: Any) -> Dict[str, str]:
    """从浏览器提取所有相关 Cookie"""
    result = {}
    for cookie in driver.get_cookies():
        name = cookie.get("name", "")
        if name in (COOKIE_NAME, "zsxqsessionid", "abtest_env"):
            result[name] = cookie.get("value", "")
    return result


def _extract_headers(driver: Any) -> Dict[str, str]:
    """提取浏览器 User-Agent 等信息作为请求头"""
    user_agent = driver.execute_script("return navigator.userAgent")
    return {
        "User-Agent": user_agent,
        "Referer": "https://wx.zsxq.com/",
        "Origin": "https://wx.zsxq.com",
    }


def _save_auth(cookies: Dict[str, str], headers: Dict[str, str]) -> None:
    """保存认证信息到 auth.json"""
    auth_data = {
        "cookies": cookies,
        "headers": headers,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, ensure_ascii=False, indent=2)
