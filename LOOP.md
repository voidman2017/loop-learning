# LOOP — 循环策略定义

> 本文档定义本仓库的活跃循环、触发方式、文件权限、预算控制与安全边界。**禁止 AI 自动修改。**

## Active Loops

| Loop | 频率 | 模式 | 风险等级 |
|------|------|------|----------|
| Daily Learning Loop | 每天 UTC 11:00 | L1 report-only | 低 |
| (规划中) Weekly Review | 每周 | L1 report-only | 中 |
| (规划中) Project Research | 手动触发 | L1 report-only | 中 |

## Allowed Write Paths

日常 loop 只允许修改以下路径：

- `STATE.md`
- `REVIEW-QUEUE.md`
- `state/learning-state.json`
- `state/review-queue.json`
- `content/reports/daily/**`
- `content/reports/weekly/**`
- `content/research/**`
- `content/dashboards/**`
- `SOURCES.md`

## Forbidden Paths

禁止一切日常 loop 修改以下路径：

- `.github/**`
- `scripts/**`
- `site/**`
- `skills/**`
- `prompts/**`
- `loop-constraints.md`
- `loop-budget.md`
- `LOOP.md`
- 任意 secret、credential、token、环境配置文件

## Human Gates

| 变更类型 | 是否必须 PR | 是否必须人工审核 |
|----------|------------|-----------------|
| 内容类（日报/复习题） | 是 | 是 |
| 路线类（roadmap 变更） | 是 | 是，且强制 |
| 控制面提案 | 是（仅提案，不落地） | 是 |
| 超过 10 个文件的 PR | 是 | 标记 `needs-human-deep-review` |

## Budget & Observability

| 指标 | 限制 |
|------|------|
| Daily Loop 调用频率 | 最多 1 次/天 |
| 每日 LLM 调用 | 主模型 1 次 + 审查模型 1 次 |
| Weekly Loop 调用频率 | 最多 1 次/周 |
| Research Loop | 默认手动触发 |
| 连续 2 天 PR 未处理 | 自动暂停 schedule |

详见 `loop-budget.md`。

## PR Policy

- **分支名格式**：`loop/daily-YYYY-MM-DD`
- **Commit message 格式**：`loop(daily): <description>`
- **PR 标题格式**：`loop(daily): <summary>`
- PR 描述必须包含：Scope、Inputs、Files changed、Risk level、Validation passed、Human review checklist
- 默认不 auto-merge

## Kill Switch

任一为真，workflow 立即退出：

- `STATE.md` frontmatter: `kill_switch: true`
- 仓库变量 `LOOP_PAUSED=true`

## L1 → L2 → L3 升级路径

| 级别 | 说明 | 条件 |
|------|------|------|
| L1 | report-only，自动 PR 但不自动落地 | 初始状态 |
| L2 | assisted，低风险内容可自动合并 | 连续数周低噪音后 |
| L3 | unattended，完全自动化 | 暂不启用 |

**新 pattern 必须从 L1 起步。**