# Loop Constraints

> 不可违反的约束、黑白名单、禁止改动区。**禁止 AI 自动修改。**

## 不可违反原则

1. **AI 只改内容，不改主题。** 禁止修改 `site/`、`.github/`、`scripts/` 下的任何文件。
2. **所有自动化产出必须通过 PR 提交。** 禁止直接 push 到 `main`。
3. **所有 PR 必须人工审阅后 merge。** 禁止 auto-merge。
4. **不确定的结论必须标记"待确认"。** 禁止将未验证的判断写成定论。
5. **引用必须有来源。** 研究文档必须附带来源引用。

## 文件白名单

日常 loop 操作范围：

- `STATE.md`
- `REVIEW-QUEUE.md`
- `state/learning-state.json`
- `state/review-queue.json`
- `content/reports/daily/**`
- `content/reports/weekly/**`
- `content/research/**`
- `content/dashboards/**`
- `SOURCES.md`

## 文件黑名单

日常 loop 禁止触碰：

- `.github/**`
- `scripts/**`
- `site/**`
- `skills/**`
- `prompts/**`
- `loop-constraints.md`
- `loop-budget.md`
- `LOOP.md`
- 任意 secret、credential、token、环境配置文件

## Kill Switch

`STATE.md` frontmatter `kill_switch: true` → 所有 workflow 立即退出并跳过执行。
仓库变量 `LOOP_PAUSED=true` → 同上。

## 违规处理

- `guard_changed_files.py` 对 `git diff --name-only` 做 hard check
- 越界文件导致脚本返回非零状态 → workflow 失败
- 连续 2 次越界 → 自动暂停 schedule，直到人工恢复