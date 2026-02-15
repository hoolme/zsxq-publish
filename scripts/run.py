#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识星球发布工具 - 通用运行器

自动管理虚拟环境和依赖安装，确保脚本在隔离环境中运行。
用法: python run.py <script_name> [args...]
"""

import subprocess
import sys
import os
from pathlib import Path

# Windows UTF-8 console support
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
VENV_DIR = SKILL_DIR / ".venv"
REQUIREMENTS_FILE = SKILL_DIR / "requirements.txt"


def get_python_path() -> str:
    """获取虚拟环境中的 Python 路径"""
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def get_pip_path() -> str:
    """获取虚拟环境中的 pip 路径"""
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "pip.exe")
    return str(VENV_DIR / "bin" / "pip")


def ensure_venv():
    """确保虚拟环境存在且依赖已安装"""
    python_path = get_python_path()

    if not Path(python_path).exists():
        print("[setup] 创建虚拟环境...")
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
        )

    # 检查是否需要安装依赖
    marker = VENV_DIR / ".deps_installed"
    req_mtime = REQUIREMENTS_FILE.stat().st_mtime if REQUIREMENTS_FILE.exists() else 0
    marker_mtime = marker.stat().st_mtime if marker.exists() else 0

    if req_mtime > marker_mtime:
        print("[setup] 安装依赖...")
        subprocess.run(
            [get_pip_path(), "install", "-q", "-r", str(REQUIREMENTS_FILE)],
            check=True,
        )
        marker.touch()


def main():
    if len(sys.argv) < 2:
        print("用法: python run.py <script_name> [args...]")
        print("示例: python run.py main.py publish --file test.md")
        sys.exit(1)

    script_name = sys.argv[1]
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        print(f"[error] 脚本不存在: {script_path}")
        sys.exit(1)

    ensure_venv()

    # 在虚拟环境中运行目标脚本
    python_path = get_python_path()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [python_path, str(script_path)] + sys.argv[2:],
        cwd=str(SCRIPTS_DIR),
        env=env,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
