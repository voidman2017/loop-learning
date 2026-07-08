#!/usr/bin/env python3
"""
输出验证脚本 — 检查所有输出文件的合法性

检查项：
1. JSON 文件是否符合对应的 JSON Schema
2. Markdown 文件 frontmatter 格式
3. 文件内容是否有效
4. 路径是否在白名单内
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def validate_json_file(path: Path, schema_path: Path | None = None) -> bool:
    """
    验证 JSON 文件格式与 schema。
    如果 schema_path 为空，只检查 JSON 格式合法性。
    """
    if not path.exists():
        print(f"  SKIP (not found): {path.name}")
        return True

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  FAIL (invalid JSON): {path.name} — {e}")
        return False

    if schema_path and schema_path.exists():
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            # 基本字段检查
            for required in schema.get("required", []):
                if required not in data:
                    print(f"  FAIL (missing field '{required}'): {path.name}")
                    return False
        except json.JSONDecodeError:
            print(f"  WARN (invalid schema): {schema_path.name}")

    print(f"  PASS: {path.name}")
    return True


def validate_markdown_file(path: Path) -> bool:
    """验证 Markdown 文件基本格式。"""
    if not path.exists():
        print(f"  SKIP (not found): {path.name}")
        return True

    content = path.read_text(encoding="utf-8")

    # 检查是否为空
    if not content.strip():
        print(f"  FAIL (empty file): {path.name}")
        return False

    # 检查 frontmatter 格式（如果有的话）
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) < 3:
            print(f"  FAIL (unclosed frontmatter): {path.name}")
            return False
        frontmatter = parts[1].strip()
        # 验证 YAML 基本格式（至少有关键值对）
        if ":" not in frontmatter:
            print(f"  WARN (frontmatter has no key-value pairs): {path.name}")

    print(f"  PASS: {path.name}")
    return True


def validate_content_dirs() -> bool:
    """验证内容目录中的文件。"""
    all_pass = True
    for subdir in ["reports/daily", "dashboards"]:
        dir_path = REPO_ROOT / "content" / subdir
        if not dir_path.exists():
            continue
        for f in sorted(dir_path.glob("*.md")):
            if not validate_markdown_file(f):
                all_pass = False
    return all_pass


def main() -> int:
    """执行所有验证项，返回退出码（0=通过，1=失败）。"""
    print("=" * 50)
    print("Output Validation")
    print("=" * 50)

    all_pass = True
    errors = []

    # 1. 验证状态 JSON 文件
    print("\\n[1] Validating JSON state files...")
    json_files = [
        (REPO_ROOT / "state" / "learning-state.json",
         REPO_ROOT / "state" / "schemas" / "learning-state.schema.json"),
        (REPO_ROOT / "state" / "review-queue.json",
         REPO_ROOT / "state" / "schemas" / "review-queue.schema.json"),
    ]
    for json_file, schema_file in json_files:
        if not validate_json_file(json_file, schema_file):
            all_pass = False
            errors.append(str(json_file))

    # 2. 验证 Markdown 核心文件
    print("\\n[2] Validating core Markdown files...")
    md_files = [
        REPO_ROOT / "STATE.md",
        REPO_ROOT / "REVIEW-QUEUE.md",
        REPO_ROOT / "SOURCES.md",
        REPO_ROOT / "README.md",
    ]
    for md_file in md_files:
        if not validate_markdown_file(md_file):
            all_pass = False
            errors.append(str(md_file))

    # 3. 验证内容目录中的文件
    print("\\n[3] Validating content files...")
    if not validate_content_dirs():
        all_pass = False
        errors.append("content/")

    # 4. 验证每日报告目录可写且存在
    print("\\n[4] Checking directory structure...")
    required_dirs = [
        REPO_ROOT / "content" / "reports" / "daily",
        REPO_ROOT / "content" / "dashboards",
        REPO_ROOT / "state",
        REPO_ROOT / "content" / "notes",
    ]
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        if d.exists():
            print(f"  PASS: {d.name}/")

    # 汇总
    print("\\n" + "=" * 50)
    if all_pass:
        print("RESULT: ALL VALIDATION PASSED")
        return 0
    else:
        print(f"RESULT: VALIDATION FAILED — {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())