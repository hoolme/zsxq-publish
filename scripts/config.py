#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识星球发布工具 - 配置模块

用户配置存储在 data/user_config.json 中，首次运行时自动引导设置。
"""

import json
import sys
from pathlib import Path

# 目录配置（固定，不随用户变化）
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
DATA_DIR = SKILL_DIR / "data"
PUBLISH_HISTORY_FILE = DATA_DIR / "publish_history.json"
USER_CONFIG_FILE = DATA_DIR / "user_config.json"

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 知识星球 API 固定配置
API_BASE = "https://api.zsxq.com/v2"
API_VERSION = "2.89.0"
ARTICLE_THRESHOLD = 500
TOPIC_MAX_TEXT_LENGTH = 10000
TOPIC_MAX_IMAGE_COUNT = 9


def _load_user_config() -> dict:
    """加载用户配置，不存在则返回空字典"""
    if USER_CONFIG_FILE.exists():
        with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_user_config(config: dict) -> None:
    """保存用户配置"""
    with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def setup_wizard() -> dict:
    """交互式配置向导，首次运行时调用"""
    print("=" * 50)
    print("  知识星球发布工具 - 首次配置")
    print("=" * 50)
    print()

    # 1. 星球 ID
    print("请输入你的知识星球 ID（从星球页面 URL 中获取）:")
    print("  例如: https://wx.zsxq.com/group/15554418212152")
    print("  星球ID就是 group/ 后面的数字")
    group_id = input("  星球ID: ").strip()
    if not group_id.isdigit():
        print("[error] 星球ID必须是纯数字")
        sys.exit(1)

    # 2. auth.json 路径
    print()
    print("请输入 auth.json 文件的存放路径:")
    print("  (Cookie 认证文件，留空则存在技能 data/ 目录下)")
    auth_path = input("  路径: ").strip()
    if not auth_path:
        auth_path = str(DATA_DIR / "auth.json")
    else:
        auth_path = str(Path(auth_path).resolve())

    config = {
        "group_id": group_id,
        "auth_file": auth_path,
    }

    _save_user_config(config)
    print()
    print(f"[OK] 配置已保存到 {USER_CONFIG_FILE}")
    print(f"  星球ID: {group_id}")
    print(f"  认证文件: {auth_path}")
    print()
    return config


def get_user_config() -> dict:
    """获取用户配置，不存在则运行配置向导"""
    config = _load_user_config()
    if not config.get("group_id"):
        config = setup_wizard()
    return config


# --- 加载用户配置并构建运行时常量 ---
_user_config = _load_user_config()

GROUP_ID = _user_config.get("group_id", "")
AUTH_FILE = Path(_user_config.get("auth_file", str(DATA_DIR / "auth.json")))

ENDPOINTS = {
    "create_article": f"{API_BASE}/articles",
    "create_topic": f"{API_BASE}/groups/{GROUP_ID}/topics",
    "settings": f"{API_BASE}/settings",
    "hashtags": f"{API_BASE}/users/self/groups/{GROUP_ID}/hashtags",
}
