#!/usr/bin/env python3
"""
文件变更守卫脚本 — 对 git diff 做硬校验

功能：
1. 检查 git diff --name-only 中所有变更文件
2. 验证所有变更是否在白名单路径内
3. 检测是否触碰了黑名单路径
4. 越界时返回非零退出码

用法：
  python guard_changed_files.py \\
    --allow "STATE.md" \\
    --allow "REVIEW-QUEUE.md" \\
    --allow "content/reports/daily/"
"""

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="Guard changed files against allowed paths"
    )
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        help="允许的路径前缀（可多次指定）"
    )
    parser.add_argument(
        "--deny",
        action="append",
        default=[
            ".github/",
            "scripts/",
            "site/",
            "skills/",
            "prompts/",
            "loop-constraints.md",
            "loop-budget.md",
            "LOOP.md",
        ],
        help="禁止的路径前缀（可多次指定，有默认值）"
    )
    parser.add_argument(
        "--base",
        default="main",
        help="对比的基准分支（默认 main）"
    )
    parser.add_argument(
        "--print-diff",
        action="store_true",
        help="打印变更文件列表"
    )
    return parser.parse_args()


def get_changed_files(base: str = "main") -> list[str]:
    """
    获取当前分支与基准分支之间的变更文件列表。
    优先使用 `git diff --name-only`，fallback 到 `git status --porcelain`。
    """
    try:
        # 尝试获取与 base 分支的 diff
        result = subprocess.run(
            ["git", "diff", "--name-only", base, "--"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        files = [f.strip() for f in result.stdout.split("\\n") if f.strip()]
        if files:
            return files
    except subprocess.CalledProcessError:
        pass

    # Fallback: 使用 git status 获取未提交变更
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        files = []
        for line in result.stdout.strip().split("\\n"):
            if line.strip():
                # 格式: XY filename
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    files.append(parts[1])
        return files
    except subprocess.CalledProcessError:
        return []


def is_path_allowed(filepath: str, allow_patterns: list[str]) -> bool:
    """检查文件路径是否在允许列表内。"""
    for pattern in allow_patterns:
        if filepath == pattern or filepath.startswith(pattern):
            return True
    return False


def is_path_denied(filepath: str, deny_patterns: list[str]) -> bool:
    """检查文件路径是否在黑名单内（白名单优先级高于黑名单）。"""
    for pattern in deny_patterns:
        if filepath == pattern or filepath.startswith(pattern):
            return True
    return False


def main() -> int:
    """主逻辑，返回退出码。"""
    args = parse_args()

    print("=" * 60)
    print("File Change Guard")
    print("=" * 60)

    # 获取变更文件
    changed_files = get_changed_files(args.base)

    if not changed_files:
        print("\\nNo file changes detected. All clear.")
        return 0

    print(f"\\nChanged files ({len(changed_files)}):")
    if args.print_diff:
        for f in changed_files:
            print(f"  - {f}")

    violations = []
    allowed_count = 0

    for filepath in changed_files:
        # 白名单检查：在白名单内直接通过
        if is_path_allowed(filepath, args.allow):
            allowed_count += 1
            continue

        # 黑名单检查
        if is_path_denied(filepath, args.deny):
            violations.append(filepath)
            print(f"  DENIED: {filepath}")
        else:
            # 既不在白名单也不在黑名单中
            violations.append(filepath)
            print(f"  NOT ALLOWED: {filepath}")

    print(f"\\nSummary:")
    print(f"  Allowed:   {allowed_count}")
    print(f"  Violations: {len(violations)}")

    if violations:
        print("\\n" + "!" * 60)
        print("GUARD FAILED: Restricted files have been modified!")
        print("!" * 60)
        return 1

    print("\\nAll changes are within allowed paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())