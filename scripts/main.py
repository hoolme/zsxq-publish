#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识星球发布工具 - 主入口

用法:
  main.py setup                          首次配置（星球ID、认证路径）
  main.py login                          浏览器登录授权
  main.py publish --file <path>          发布文件（自动判断话题/文章）
  main.py topic --text <text> [--tags t] 发布话题（短内容）
  main.py article --file <path>          发布文章（长内容）
  main.py history                        查看发布历史
  main.py check-auth                     检查认证状态
"""

import argparse
import json
import sys


def _ensure_configured():
    """确保用户已完成首次配置，未配置则自动引导"""
    from config import get_user_config

    get_user_config()


def cmd_setup(args):
    """首次配置或重新配置"""
    from config import setup_wizard

    setup_wizard()
    return 0


def cmd_publish(args):
    """发布文件（自动判断模式）"""
    from publisher import ZsxqPublisher

    pub = ZsxqPublisher()
    tags = args.tags.split(",") if args.tags else None
    result = pub.publish_file(args.file, mode="auto", tags=tags)
    return 0 if result.get("succeeded") else 1


def cmd_topic(args):
    """发布话题"""
    from publisher import ZsxqPublisher

    pub = ZsxqPublisher()
    tags = args.tags.split(",") if args.tags else None

    if args.file:
        from pathlib import Path

        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        print("[error] 请提供 --text 或 --file 参数")
        return 1

    result = pub.publish_topic(text, title=args.title or "", tags=tags)
    return 0 if result.get("succeeded") else 1


def cmd_article(args):
    """发布文章"""
    from publisher import ZsxqPublisher

    pub = ZsxqPublisher()
    tags = args.tags.split(",") if args.tags else None

    if not args.file:
        print("[error] 文章模式必须提供 --file 参数")
        return 1

    from pathlib import Path

    md_content = Path(args.file).read_text(encoding="utf-8")
    result = pub.publish_article(md_content, title=args.title or "", tags=tags)
    return 0 if result.get("succeeded") else 1


def cmd_history(args):
    """查看发布历史"""
    from publisher import ZsxqPublisher

    pub = ZsxqPublisher()
    records = pub.get_history(count=args.count)

    if not records:
        print("暂无发布历史")
        return 0

    print(f"最近 {len(records)} 条发布记录:\n")
    for i, rec in enumerate(reversed(records), 1):
        print(f"  {i}. [{rec.get('publish_type', '?')}] {rec.get('title', '未知')}")
        print(f"     时间: {rec.get('timestamp', '?')}")
        print(f"     状态: {rec.get('status', '?')}")
        if rec.get("article_url"):
            print(f"     链接: {rec['article_url']}")
        print()

    return 0


def cmd_check_auth(args):
    """检查认证状态"""
    from auth import load_auth, check_auth_status

    try:
        cookies, headers = load_auth()
        print("[OK] auth.json 加载成功")
        print(f"  access_token: {cookies.get('zsxq_access_token', '?')[:20]}...")
    except Exception as e:
        print(f"[FAIL] {e}")
        print("\n提示: 运行 login 命令进行浏览器登录授权")
        return 1

    print("正在验证认证有效性...")
    if check_auth_status(cookies, headers):
        print("[OK] 认证有效")
        return 0
    else:
        print("[FAIL] 认证已过期")
        print("\n提示: 运行 login 命令进行浏览器登录授权")
        return 1


def cmd_login(args):
    """浏览器登录授权"""
    from login import browser_login

    print("启动浏览器登录知识星球...")
    print("请在弹出的浏览器窗口中扫码登录\n")

    timeout = args.timeout if hasattr(args, "timeout") else 120
    success = browser_login(timeout=timeout)

    if success:
        # 登录后验证
        print("\n正在验证新的认证信息...")
        from auth import load_auth, check_auth_status

        try:
            cookies, headers = load_auth()
            if check_auth_status(cookies, headers):
                print("[OK] 认证验证通过，可以正常发布了！")
                return 0
            else:
                print("[WARN] Cookie 已保存但 API 验证未通过，请稍后重试")
                return 1
        except Exception as e:
            print(f"[WARN] 验证异常: {e}")
            return 1
    else:
        print("[FAIL] 登录失败，请重试")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="知识星球内容发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # setup 命令
    p_setup = subparsers.add_parser("setup", help="首次配置（星球ID、认证路径）")
    p_setup.set_defaults(func=cmd_setup)

    # publish 命令
    p_publish = subparsers.add_parser("publish", help="发布文件（自动判断模式）")
    p_publish.add_argument("--file", "-f", required=True, help="Markdown 文件路径")
    p_publish.add_argument("--tags", "-t", help="标签（逗号分隔）")
    p_publish.set_defaults(func=cmd_publish)

    # topic 命令
    p_topic = subparsers.add_parser("topic", help="发布话题（短内容）")
    p_topic.add_argument("--text", help="话题文本内容")
    p_topic.add_argument("--file", "-f", help="从文件读取内容")
    p_topic.add_argument("--title", help="话题标题")
    p_topic.add_argument("--tags", "-t", help="标签（逗号分隔）")
    p_topic.set_defaults(func=cmd_topic)

    # article 命令
    p_article = subparsers.add_parser("article", help="发布文章（长内容）")
    p_article.add_argument("--file", "-f", required=True, help="Markdown 文件路径")
    p_article.add_argument("--title", help="文章标题（默认从 Markdown 提取）")
    p_article.add_argument("--tags", "-t", help="标签（逗号分隔）")
    p_article.set_defaults(func=cmd_article)

    # history 命令
    p_history = subparsers.add_parser("history", help="查看发布历史")
    p_history.add_argument("--count", "-n", type=int, default=10, help="显示条数")
    p_history.set_defaults(func=cmd_history)

    # check-auth 命令
    p_auth = subparsers.add_parser("check-auth", help="检查认证状态")
    p_auth.set_defaults(func=cmd_check_auth)

    # login 命令
    p_login = subparsers.add_parser("login", help="浏览器登录授权")
    p_login.add_argument(
        "--timeout", type=int, default=120, help="登录超时时间（秒，默认120）"
    )
    p_login.set_defaults(func=cmd_login)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
