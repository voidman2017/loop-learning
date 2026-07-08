#!/usr/bin/env python3
"""
Research Loop — 自动研究脚本

方案 A：从 content/research/inbox/ 读取课题，自动研究生成笔记
方案 B：从 RSS 源自动发现技术文章，生成学习笔记

输出：
  - content/research/YYYY/MM/<topic>.md — 研究笔记
  - SOURCES.md — 更新引用来源
  - 可选的复习题条目追加到 state/review-queue.json
"""

import json
import os
import re
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 路径常量
INBOX_DIR = REPO_ROOT / "content" / "research" / "inbox"
DONE_DIR = REPO_ROOT / "content" / "research" / "done"
RESEARCH_DIR = REPO_ROOT / "content" / "research"
SOURCES_MD = REPO_ROOT / "SOURCES.md"
SOURCES_CONFIG = REPO_ROOT / "site" / "config" / "sources.yml"
REVIEW_QUEUE_JSON = REPO_ROOT / "state" / "review-queue.json"
STATE_JSON = REPO_ROOT / "state" / "learning-state.json"


def read_file(path: Path) -> str:
    """安全读取文件内容。"""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_file(path: Path, content: str) -> None:
    """写入文件，自动创建父目录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def get_inbox_items() -> list[dict]:
    """读取 inbox 中的研究课题。"""
    if not INBOX_DIR.exists():
        return []

    items = []
    for f in sorted(INBOX_DIR.glob("*.md")):
        if f.name == "README.md":
            continue

        content = f.read_text(encoding="utf-8")
        # 解析 frontmatter
        meta = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        meta[key.strip()] = val.strip()
                body = parts[2].strip()

        items.append({
            "file": f.name,
            "path": str(f),
            "type": meta.get("type", "topic"),
            "url": meta.get("url", ""),
            "description": body,
            "meta": meta,
        })

    return items


def fetch_rss_sources() -> list[dict]:
    """读取 RSS 源配置。"""
    if not SOURCES_CONFIG.exists():
        return []

    try:
        with open(SOURCES_CONFIG, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("sources", [])
    except Exception as e:
        print(f"  WARNING: Failed to read sources config: {e}")
        return []


def fetch_rss_articles(sources: list[dict], max_per_source: int = 3) -> list[dict]:
    """从 RSS 源获取最新文章。"""
    import feedparser
    import time

    articles = []
    for source in sources:
        try:
            print(f"  Fetching RSS: {source.get('name', 'unknown')}...")
            feed = feedparser.parse(source["url"])

            count = 0
            for entry in feed.entries[:max_per_source]:
                articles.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:500],
                    "published": entry.get("published", ""),
                    "source": source.get("name", ""),
                    "tags": source.get("tags", []),
                    "lang": source.get("lang", "en"),
                })
                count += 1

            print(f"    Got {count} articles")
            time.sleep(0.5)  # 避免请求过快

        except Exception as e:
            print(f"    FAILED: {e}")

    return articles


def filter_relevant_articles(articles: list[dict], current_themes: list[str]) -> list[dict]:
    """
    根据当前学习主题筛选相关文章。
    MVP 版：关键词匹配 + 取前 3 篇。
    """
    if not current_themes:
        # 没有主题时取最新的 3 篇
        return articles[:3]

    keywords = [t.lower() for t in current_themes]
    scored = []

    for article in articles:
        text = f"{article['title']} {article['summary']}".lower()
        score = sum(1 for kw in keywords if kw in text)
        scored.append((score, article))

    # 按相关度排序
    scored.sort(key=lambda x: x[0], reverse=True)

    # 取相关度最高的 3 篇
    selected = [a for s, a in scored if s > 0][:3]

    # 如果不够 3 篇，补充最新的
    if len(selected) < 3:
        for a in articles[:5]:
            if a not in selected and len(selected) < 3:
                selected.append(a)

    return selected


def call_llm(system_prompt: str, user_message: str) -> str:
    """通过 Anthropic 协议调用 LLM API。"""
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    base_url = os.environ.get("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding").strip()
    if base_url.endswith("/"):
        base_url = base_url.rstrip("/")
    model = os.environ.get("LLM_MODEL", "DeepSeek-V4-Flash").strip()

    if not api_key:
        print("  WARNING: LLM_API_KEY not set, skipping research")
        return ""

    try:
        import httpx

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message}
            ],
        }

        request_url = f"{base_url}/v1/messages"

        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                request_url,
                headers=headers,
                json=payload,
            )

        if response.status_code != 200:
            print(f"  API Error: status={response.status_code}")
            print(f"  Response: {response.text[:300]}")
            return ""

        result = response.json()
        content = ""
        for block in result.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
        return content

    except Exception as e:
        print(f"  ERROR: LLM call failed: {e}")
        return ""


def research_topic(item: dict) -> str:
    """
    研究单个 inbox 课题，生成笔记。
    返回 Markdown 格式的研究笔记。
    """
    topic_type = item["type"]
    description = item["description"]
    url = item["url"]

    if topic_type == "github":
        prompt = (
            f"请研究以下 GitHub 项目并生成研究笔记：\n"
            f"项目地址：{url}\n"
            f"研究要求：{description}\n\n"
            f"请输出包含以下内容的 Markdown 笔记：\n"
            f"1. 项目简介与定位\n"
            f"2. 核心架构/核心概念\n"
            f"3. 主要功能与能力\n"
            f"4. 对我学习价值的判断\n"
            f"5. 来源引用"
        )
    elif topic_type == "article":
        prompt = (
            f"请研究以下文章并生成学习笔记：\n"
            f"文章地址：{url}\n"
            f"研究要求：{description}\n\n"
            f"请输出包含以下内容的 Markdown 笔记：\n"
            f"1. 文章核心观点\n"
            f"2. 关键论据\n"
            f"3. 我的思考与判断\n"
            f"4. 是否值得深入阅读\n"
            f"5. 来源引用"
        )
    else:  # topic / url
        prompt = (
            f"请研究以下技术话题并生成学习笔记：\n"
            f"{description}\n\n"
            f"请输出包含以下内容的 Markdown 笔记：\n"
            f"1. 话题概述\n"
            f"2. 核心概念\n"
            f"3. 关键资源\n"
            f"4. 学习路径建议\n"
            f"5. 来源引用"
        )

    system = "你是一个技术研究助手。你的研究必须基于真实信息，不确定的内容要标注'待确认'。输出格式为 Markdown。"

    print(f"  Researching: {item['file']}...")
    result = call_llm(system, prompt)
    return result


def summarize_article(article: dict) -> str:
    """
    对 RSS 文章进行摘要，生成学习笔记。
    """
    prompt = (
        f"请阅读以下技术文章并生成学习摘要：\n\n"
        f"标题：{article['title']}\n"
        f"来源：{article['source']}\n"
        f"URL：{article['url']}\n"
        f"摘要：{article['summary']}\n\n"
        f"请输出包含以下内容的 Markdown 笔记：\n"
        f"1. 文章核心内容\n"
        f"2. 关键技术点\n"
        f"3. 值得关注的部分\n"
        f"4. 来源引用"
    )

    system = "你是一个技术学习助手。请基于提供的文章信息生成学习笔记，不确定的内容要标注'待确认'。输出格式为 Markdown。"

    print(f"  Summarizing: {article['title'][:40]}...")
    result = call_llm(system, prompt)
    return result


def update_sources(topic: str, url: str, source_type: str) -> None:
    """更新 SOURCES.md，追加引用记录。"""
    if not url:
        return

    # 读取现有 SOURCES.md，找最大 ID
    sources_content = read_file(SOURCES_MD)
    src_ids = re.findall(r'\[SRC-(\d+)\]', sources_content)
    next_id = max([int(x) for x in src_ids], default=0) + 1

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = (
        f"\n| [SRC-{next_id:03d}] | {topic} | {url} | {today} | {source_type} |"
    )

    # 追加到表格后面
    if "|---|" in sources_content:
        # 找到表格末尾
        lines = sources_content.strip().split("\n")
        # 在最后一行前插入
        sources_content = sources_content.rstrip() + entry + "\n"
    else:
        sources_content += (
            f"\n| ID | 来源名称 | URL | 访问日期 | 类型 |\n"
            f"|---|---------|-----|---------|------|\n"
            f"| [SRC-{next_id:03d}] | {topic} | {url} | {today} | {source_type} |\n"
        )

    write_file(SOURCES_MD, sources_content)
    print(f"  Added SRC-{next_id:03d} to SOURCES.md")


def move_to_done(item: dict) -> None:
    """将已处理的 inbox 文件移到 done 目录。"""
    src = Path(item["path"])
    if not src.exists():
        return

    DONE_DIR.mkdir(parents=True, exist_ok=True)
    dest = DONE_DIR / src.name

    # 如果 done 目录已有同名文件，加时间戳
    if dest.exists():
        timestamp = datetime.now().strftime("%H%M%S")
        dest = DONE_DIR / f"{src.stem}_{timestamp}{src.suffix}"

    src.rename(dest)
    print(f"  Moved to done/: {src.name}")


def generate_research_filename(topic: str) -> str:
    """根据话题生成文件名。"""
    # 取第一行或前 20 个字符作为文件名
    name = topic.strip().split("\n")[0][:30]
    # 清理文件名非法字符
    name = re.sub(r'[^\w\s-]', '', name)
    name = name.strip().replace(" ", "-").lower()
    return name


def process_inbox() -> list[dict]:
    """方案 A：处理 inbox 研究课题。"""
    items = get_inbox_items()
    if not items:
        print("  No inbox items found.")
        return []

    results = []
    for item in items:
        print(f"\n  [{items.index(item)+1}/{len(items)}] Processing: {item['file']}")

        # 调用 AI 研究
        note = research_topic(item)
        if not note:
            print(f"  SKIP: Research failed for {item['file']}")
            continue

        # 生成文件名
        filename = generate_research_filename(item["description"])
        today = datetime.now(timezone.utc)
        output_path = RESEARCH_DIR / str(today.year) / f"{today.month:02d}" / f"{filename}.md"
        write_file(output_path, note)

        # 更新 SOURCES.md
        if item["url"]:
            update_sources(
                item["description"][:50],
                item["url"],
                f"inbox-{item['type']}"
            )

        # 移到 done
        move_to_done(item)

        results.append({
            "file": item["file"],
            "output": str(output_path.relative_to(REPO_ROOT)),
            "type": item["type"],
        })

    return results


def process_rss(current_themes: list[str]) -> list[dict]:
    """方案 B：从 RSS 自动发现文章。"""
    sources = fetch_rss_sources()
    if not sources:
        print("  No RSS sources configured.")
        return []

    print(f"\n  Fetching RSS feeds ({len(sources)} sources)...")
    articles = fetch_rss_articles(sources)

    if not articles:
        print("  No articles found.")
        return []

    print(f"  Total articles: {len(articles)}")

    # 筛选相关文章
    selected = filter_relevant_articles(articles, current_themes)
    print(f"  Selected: {len(selected)} articles (themes: {current_themes})")

    results = []
    for article in selected[:2]:  # 最多处理 2 篇
        print(f"\n  Processing: {article['title'][:50]}")

        note = summarize_article(article)
        if not note:
            continue

        # 生成文件名
        filename = generate_research_filename(article["title"])
        today = datetime.now(timezone.utc)
        output_path = RESEARCH_DIR / str(today.year) / f"{today.month:02d}" / f"rss-{filename}.md"
        write_file(output_path, note)

        # 更新 SOURCES.md
        update_sources(
            article["title"][:50],
            article["url"],
            f"rss-{article['source']}"
        )

        results.append({
            "title": article["title"],
            "output": str(output_path.relative_to(REPO_ROOT)),
            "source": article["source"],
        })

    return results


def get_current_themes() -> list[str]:
    """从 state 文件中读取当前学习主题。"""
    content = read_file(STATE_JSON)
    try:
        data = json.loads(content)
        return data.get("current_theme", [])
    except json.JSONDecodeError:
        return []


def main():
    """Research Loop 主流程。"""
    print("=" * 50)
    print("Research Loop")
    print("=" * 50)

    # 读取当前学习主题，用于 RSS 筛选
    themes = get_current_themes()
    print(f"\nCurrent themes: {themes}")

    # 方案 A：处理 inbox 课题
    print("\n[Plan A] Processing research inbox...")
    inbox_results = process_inbox()

    # 方案 B：扫描 RSS 源
    print("\n[Plan B] Scanning RSS feeds...")
    rss_results = process_rss(themes)

    # 汇总
    print("\n" + "=" * 50)
    print("Research Loop Summary")
    print("=" * 50)
    print(f"  Inbox researches: {len(inbox_results)}")
    for r in inbox_results:
        print(f"    - {r['file']} → {r['output']}")
    print(f"  RSS articles: {len(rss_results)}")
    for r in rss_results:
        print(f"    - {r['title'][:50]} → {r['output']}")

    return {
        "inbox": inbox_results,
        "rss": rss_results,
    }


if __name__ == "__main__":
    main()