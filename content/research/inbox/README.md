# Research Inbox

> 把你想研究的话题放这里，系统会自动生成研究笔记。

## 使用方法

在 `inbox/` 目录下创建一个 `.md` 文件，文件名任意，内容包含你要研究的话题。

### 示例 1：研究一个开源项目

```markdown
---
type: github
url: https://github.com/vercel/next.js
---
研究 Next.js 的 App Router 架构设计
```

### 示例 2：研究一个技术话题

```markdown
---
type: topic
---
请帮我研究一下 "RAG (Retrieval-Augmented Generation) 的最新进展"，重点了解 2025-2026 年的新方法
```

### 示例 3：研究一篇文章

```markdown
---
type: article
url: https://example.com/some-article
---
总结这篇文章的核心观点
```

## 处理流程

1. 你把课题文件放到 `inbox/`
2. 下次 Daily Loop 运行时自动发现
3. 系统调用 AI 研究并生成笔记到 `content/research/YYYY/MM/`
4. 原文件自动移到 `content/research/done/`
5. 研究结果会出现在当天的日报中

## 支持的 type

| type | 说明 | 必填字段 |
|------|------|---------|
| `github` | 研究 GitHub 项目 | `url` |
| `topic` | 研究一个技术话题 | 无（标题和描述即可） |
| `article` | 研究一篇文章 | `url` |
| `url` | 研究任意 URL | `url` |