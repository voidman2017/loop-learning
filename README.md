# AI Learning Loop Site

> 一个以 Git 仓库为记忆、以 PR 为审阅、以 GitHub Pages 为展示、以 loop 为节律、以人工 gate 为边界的**个人长期学习操作系统**。

## 项目定位

这不是一个传统的"学习笔记网站"。它是一个**自迭代的知识操作系统**：

- **内容层**由 AI 辅助生成（日报、复习题、研究摘要）
- **控制层**由你本人把控（PR 审阅、策略决策、主题更新）
- **自动化层**由 GitHub Actions 定时触发，不越界、不自动发布

## 核心原则

| 原则 | 说明 |
|------|------|
| 内容可改，主题不可改 | AI 只写 Markdown/JSON，不改网站主题与布局 |
| 全部经过 PR | 任何自动化产出都通过 Pull Request 提交 |
| 人工审阅 | 所有 PR 必须人工 merge |
| 可回滚 | 每一个变更都在 Git 历史中，可 revert |
| 引用来源可查 | 所有结论必须附带来源 |

## 运行方式

1. **Daily Learning Loop** 每天早上定时触发
2. Agent 读取学习状态、最近笔记、复习队列
3. 生成：今日日报、复习题、状态更新
4. 自动创建 Pull Request
5. 你审阅后 merge 到 `main`
6. GitHub Pages 自动发布

## 仓库结构

```
/
├── LOOP.md              # 循环策略定义
├── STATE.md             # 当前学习状态
├── REVIEW-QUEUE.md      # 复习队列
├── SOURCES.md           # 引用来源登记
├── loop-constraints.md  # 约束与边界
├── loop-budget.md       # 预算控制
├── loop-run-log.md      # 运行日志
├── content/             # 学习内容（AI 主要修改区）
├── state/               # 机器可读状态（JSON）
├── prompts/             # AI 提示词模板
├── skills/              # 领域能力规则
├── scripts/             # 控制与验证脚本
└── .github/workflows/   # GitHub Actions（禁止自动修改）
```

## 安全边界

- **允许 AI 修改**：`content/`、`STATE.md`、`REVIEW-QUEUE.md`、`state/`、`SOURCES.md`
- **禁止 AI 修改**：`.github/`、`scripts/`、`site/`、`skills/`、`prompts/`、`loop-*`、`LOOP.md`
- **三层防线**：Prompt 约束 → 脚本硬校验 → 分支保护 required checks