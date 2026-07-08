# Daily Learning Triage Skill

> 日常学习循环的领域能力定义。**AI 可读，不可自动修改。**

## 职责

- 分析当前学习状态、笔记内容与复习队列
- 识别知识盲区与遗忘风险
- 生成今日学习日报
- 更新复习队列
- 更新 STATE.md 进展摘要

## 输入

- `STATE.md` — 当前学习状态摘要
- `state/learning-state.json` — 机器学习状态
- `content/notes/` — 最近新增的笔记
- `content/research/` — 最近的研究草稿
- 最近 3 天 `content/reports/daily/` — 历史日报
- `REVIEW-QUEUE.md` — 当前复习队列
- `state/review-queue.json` — 机器队列数据

## 输出

- `content/reports/daily/YYYY-MM-DD.md` — 今日日报
- `content/dashboards/today.md` — 今日仪表盘
- `state/review-queue.json` — 更新后的复习队列
- `REVIEW-QUEUE.md` — 更新后的可读队列摘要
- `STATE.md` — 更新进展摘要与盲区

## 规则

1. 只修改白名单内的路径
2. 不确定的结论必须标记"待确认"
3. 每天最多新增 5 个复习问题
4. 所有新结论必须附来源引用
5. 不得重写 roadmap、site、scripts、workflows
6. 每天最多归档 5 个过期条目
7. 输出 PR 摘要所需的 change summary

## 风险控制

- 低风险：日报内容偏差 — 人工审阅时修正
- 中风险：复习队列膨胀 — 每天限新增 5 条，总量不超过 200 条
- 高风险：越界修改 — guard_changed_files.py 硬校验

## 升级条件

- 从 L1 report-only 起步
- 连续 2 周无越界、低噪音 → 考虑 L2 assisted
- 禁止跳过 L1 阶段