# 系统搭建笔记

## 2026-07-08：AI Learning Loop Site 初始化

基于 deep-research-report 的推荐 MVP 方案创建本项目。

### 项目架构

- 内容层：Markdown/JSON/YAML，AI 主要修改区
- 展示层：GitHub Pages，构建脚本生成
- 控制层：GitHub Actions + PR + 人工审核
- 状态层：`STATE.md` + `state/*.json` 双重表示

### 安全边界

- 文件白名单限制 AI 修改范围
- `guard_changed_files.py` 做硬校验
- 分支保护要求所有 PR 必须审阅后才能 merge
- CODEOWNERS 将敏感路径指向本人

### 关键决策

- 采用"主要借鉴 + 选择性使用工具"的 loop-engineering 策略
- 从 L1 report-only 起步，不跳过自动化级别
- 网站主题与内容分离，AI 不碰主题文件