#!/usr/bin/env python3
"""
站点构建脚本 — 从 Markdown 内容生成 GitHub Pages 站点

职责：
1. 读取 content/ 下的 Markdown 文件
2. 应用 site/templates/ 中的模板
3. 生成 HTML 到 site/public/
4. 支持 GitHub Pages 部署

当前为 MVP 版本，生成最简单的静态站点结构。
后续可扩展为使用 Jekyll、Hugo、或自定义 SSG。
"""

import json
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
TEMPLATES_DIR = REPO_ROOT / "site" / "templates"
PUBLIC_DIR = REPO_ROOT / "site" / "public"
CONFIG_DIR = REPO_ROOT / "site" / "config"


def read_file(path: Path) -> str:
    """安全读取文件内容。"""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def markdown_to_html(markdown_text: str) -> str:
    """
    简单 Markdown 转 HTML（MVP 版本）。
    后续可以用 markdown 库替换。
    """
    html = markdown_text

    # 代码块：匹配 ```lang\n...\n```
    html = re.sub(
        r'```(\w*)\n(.*?)\n```',
        lambda m: '<pre><code class="language-{}">{}</code></pre>'.format(m.group(1), m.group(2)),
        html,
        flags=re.DOTALL,
    )

    # 行内代码：`code`
    html = re.sub(r'`([^`]+)`', lambda m: '<code>{}</code>'.format(m.group(1)), html)

    # 标题：## Title
    for i in range(6, 0, -1):
        html = re.sub(
            r'^{} +(.+?)$'.format('#' * i),
            lambda m, level=i: '<h{}>{}</h{}>'.format(level, m.group(1), level),
            html,
            flags=re.MULTILINE,
        )

    # 粗体：**text**
    html = re.sub(r'\*\*(.+?)\*\*', lambda m: '<strong>{}</strong>'.format(m.group(1)), html)

    # 列表项：- item
    html = re.sub(r'^- (.+)$', lambda m: '<li>{}</li>'.format(m.group(1)), html, flags=re.MULTILINE)

    # 将连续 li 包裹成 ul
    html = re.sub(r'(<li>.*?</li>(?:\n<li>.*?</li>)*)', lambda m: '<ul>{}</ul>'.format(m.group(1)), html)

    # 段落：未被 HTML 标签包裹的文本块
    paragraphs = []
    for block in html.split('\n\n'):
        block = block.strip()
        if block and not block.startswith('<'):
            block = '<p>{}</p>'.format(block)
        paragraphs.append(block)

    return '\n\n'.join(paragraphs)


def get_nav_config() -> dict:
    """读取导航配置。"""
    nav_file = CONFIG_DIR / "nav.json"
    if nav_file.exists():
        try:
            return json.loads(nav_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {
        "title": "AI Learning Loop",
        "items": [
            {"label": "Home", "path": "/"},
            {"label": "Today", "path": "/today"},
            {"label": "Daily Reports", "path": "/daily"},
            {"label": "Review Queue", "path": "/review-queue"},
        ]
    }


def render_page(title: str, content_html: str, nav: dict) -> str:
    """
    渲染完整 HTML 页面。
    使用内联样式以保持 MVP 简洁。
    """
    base_path = nav.get("basePath", "")
    nav_items = "".join(
        f'<a href="{base_path}{item["path"]}" style="color: #ccc; text-decoration: none; margin-left: 1.5rem;">{item["label"]}</a>'
        for item in nav.get("items", [])
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <base href="{base_path}/">
    <title>{title} — {nav["title"]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 960px;
            margin: 0 auto;
            padding: 0 1rem;
        }}
        nav {{
            background: #1a1a2e;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            border-radius: 0 0 8px 8px;
        }}
        nav .brand {{
            color: #fff;
            font-weight: bold;
            font-size: 1.2rem;
        }}
        .content {{ padding: 2rem 0; }}
        h1 {{ font-size: 1.8rem; margin-bottom: 1rem; color: #1a1a2e; }}
        h2 {{ font-size: 1.4rem; margin: 1.5rem 0 0.5rem; color: #16213e; }}
        h3 {{ font-size: 1.2rem; margin: 1rem 0 0.5rem; }}
        p {{ margin-bottom: 1rem; }}
        ul {{ margin: 0.5rem 0 1rem 1.5rem; }}
        li {{ margin-bottom: 0.3rem; }}
        code {{
            background: #f4f4f4;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        pre {{
            background: #f4f4f4;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
            margin-bottom: 1rem;
        }}
        .meta {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }}
        footer {{
            text-align: center;
            color: #999;
            font-size: 0.8rem;
            padding: 2rem 0;
            border-top: 1px solid #eee;
            margin-top: 2rem;
        }}
    </style>
</head>
<body>
    <nav>
        <span class="brand">{nav["title"]}</span>
        {nav_items}
    </nav>
    <main class="content">
        <h1>{title}</h1>
        {content_html}
    </main>
    <footer>
        <p>Generated by AI Learning Loop — Content automatically produced, human-reviewed.</p>
    </footer>
</body>
</html>"""


def build_index():
    """生成首页。"""
    today_content = read_file(CONTENT_DIR / "dashboards" / "today.md")
    state_md = read_file(REPO_ROOT / "STATE.md")

    content_parts = []

    # 今日摘要
    if today_content:
        content_parts.append("## Today's Dashboard")
        content_parts.append(markdown_to_html(today_content[:500]))

    # 学习状态摘要
    if state_md:
        # 提取 frontmatter 之后的内容
        parts = state_md.split("---", 2)
        if len(parts) >= 3:
            state_body = parts[2].strip()
            content_parts.append("## Learning State")
            content_parts.append(markdown_to_html(state_body[:500]))

    return "\\n\\n".join(content_parts)


def build_today():
    """生成 Today 页面。"""
    today_content = read_file(CONTENT_DIR / "dashboards" / "today.md")
    if today_content:
        return markdown_to_html(today_content)
    return "<p>No dashboard data yet. The daily learning loop will generate one.</p>"


def build_daily_list(base_path: str = ""):
    """生成日报列表页面。"""
    daily_dir = CONTENT_DIR / "reports" / "daily"
    if not daily_dir.exists():
        return "<p>No daily reports yet.</p>"

    files = sorted(daily_dir.glob("*.md"), reverse=True)
    if not files:
        return "<p>No daily reports yet.</p>"

    items = []
    for f in files:
        date_str = f.stem
        content = f.read_text(encoding="utf-8")
        # 提取第一行作为摘要
        first_line = content.strip().split("\\n")[0] if content.strip() else "No content"
        items.append(
            f'<li><a href="{base_path}/daily/{date_str}">{date_str}</a> — {first_line}</li>'
        )

    return "<ul>" + "\n".join(items) + "</ul>"


def build_review_queue():
    """生成复习队列页面。"""
    queue_content = read_file(REPO_ROOT / "REVIEW-QUEUE.md")
    if queue_content:
        return markdown_to_html(queue_content)
    return "<p>No review queue data yet.</p>"


def main():
    """站点构建主流程。"""
    print("=" * 50)
    print("Building Site")
    print("=" * 50)

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    nav = get_nav_config()

    # 页面构建映射
    pages = {
        "index": ("Home", build_index()),
        "today": ("Today's Dashboard", build_today()),
        "daily/index": ("Daily Reports", build_daily_list(nav.get("basePath", ""))),
        "review-queue": ("Review Queue", build_review_queue()),
    }

    for page_path, (title, content_html) in pages.items():
        html = render_page(title, content_html, nav)
        output_path = PUBLIC_DIR / f"{page_path}.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        print(f"  Built: {output_path.relative_to(REPO_ROOT)}")

    # 生成每日报告的独立页面
    daily_dir = CONTENT_DIR / "reports" / "daily"
    if daily_dir.exists():
        for f in sorted(daily_dir.glob("*.md")):
            date_str = f.stem
            content = f.read_text(encoding="utf-8")
            html = render_page(
                f"Daily Report — {date_str}",
                markdown_to_html(content),
                nav,
            )
            output_path = PUBLIC_DIR / "daily" / f"{date_str}.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")
            print(f"  Built: {output_path.relative_to(REPO_ROOT)}")

    print("\\nSite build complete!")
    print(f"Output directory: {PUBLIC_DIR}")


if __name__ == "__main__":
    main()