# Budget & Cost Control

> 预算上限、停机规则、每类 loop 配额。**禁止 AI 自动修改。**

## 全局限制

| 维度 | 上限 |
|------|------|
| 每日总 LLM 调用 | 主模型 1 次 + 审查模型 1 次 |
| 每日总 token 预算 | 100K（估计） |
| 每日最大 PR 数 | 1 |
| 连续失败重试 | 最多 2 次后暂停 |

## 各 Loop 配额

| Loop | 频率上限 | 预算 |
|------|---------|------|
| Daily Learning Loop | 1 次/天 | ~50K tokens |
| Weekly Review | 1 次/周 | ~100K tokens |
| Project Research | 手动触发 | ~150K tokens |

## 停机规则

- 超出每日 token 预算后停止开新 PR
- 连续 2 天 PR 未处理，自动暂停 schedule
- `STATE.md` frontmatter `kill_switch: true` 立即停机

## 观察指标

- 每次运行记录 token 消耗到 `loop-run-log.md`
- `loop-audit` readiness 分数应在 60+ 分
- 每周检查一次预算执行情况