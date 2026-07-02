# Clarify 阶段执行检查清单

## 准入检查 (Entry Checks)

执行阶段前必须全部通过：

- [ ] **摘要就绪检查**: `summary_ready {session_id}`
  - `interviews/{session_id}/summary.md` 存在且非空
  - 失败时：提示人类先完成 `ingest` 阶段（`claude process-interview <recording-path>`）

## 执行中检查 (During Execution)

- [ ] 外部计划已检查（如存在）：调用 `gsd-import`
- [ ] 已调用 `superpowers:brainstorming` 探索 ≥2 种需求视角
- [ ] Brainstorming HARD-GATE 通过：PM 已确认方向
- [ ] 读取 `interviews/{session_id}/transcript.md`
- [ ] 读取 `interviews/{session_id}/summary.md`
- [ ] 读取 `interviews/{session_id}/raw-insights.md`
- [ ] 创建目录 `requirements/{session_id}/`
- [ ] 起草初始 `requirements.md`，包含以下章节：
  - 背景
  - 问题
  - 用户
  - 方案
  - 验收标准
  - 非目标
  - 开放问题
- [ ] 识别 1-3 个模糊点或缺失细节
- [ ] 每轮向人类 PM 提出最多 3 个澄清问题
- [ ] 根据人类回答更新 `requirements.md`
- [ ] 展示变更部分给人类确认
- [ ] 重复澄清直到 PM 确认需求清晰
- [ ] 生成 `user-stories.md`
- [ ] 生成 `prd.md`
- [ ] 在 `requirements.md` 中添加 `<!-- status: approved -->` 标记

## 退出检查 (Exit Checks)

阶段完成后必须全部通过：

- [ ] **需求完整性检查**: `requirements_has_background_problem_solution_acceptance {session_id}`
  - `requirements.md` 存在且包含以下章节：
    - 背景 / Background
    - 问题 / Problem
    - 用户 / Users / Personas
    - 方案 / Proposed Solution / Solution
    - 验收标准 / Acceptance Criteria
  - 失败时：补充缺失章节

- [ ] **人类确认检查**: `human_approved {session_id}`
  - `requirements.md` 中包含 `<!-- status: approved -->` 或 `[x] PM 已确认`
  - 失败时：工作流暂停，等待人类确认

## 产物验证

- [ ] `requirements/{session_id}/requirements.md` — 非空，包含所有必要章节，含审批标记
- [ ] `requirements/{session_id}/user-stories.md` — 非空，从已确认需求派生
- [ ] `requirements/{session_id}/prd.md` — 非空，从已确认需求派生
- [ ] 每个需求项关联访谈时间戳（如 `(来源: 00:03:22)`）

## 人类确认节点

- [ ] 本阶段 **有** `human_gate: true`，强制人类确认
- [ ] 确认方式：
  - 对话中输入 `confirm` 或 "确认"
  - 或编辑 `requirements.md` 添加 `<!-- status: approved -->` 后运行 `workflow-continue`
- [ ] 未确认时工作流必须暂停，不得进入下一阶段
- [ ] 确认后向人类汇报：需求已锁定，产物位置，下一阶段入口

## 状态文件更新

阶段完成后，更新 `.claude/workflow-stage.yaml`：

```yaml
stages:
  clarify:
    status: completed
    entry_checks_passed: true
    exit_checks_passed: true
    human_gate_passed: true
    artifacts_produced:
      - requirements/{session_id}/requirements.md
      - requirements/{session_id}/user-stories.md
      - requirements/{session_id}/prd.md
```

## 失败恢复

- 准入校验失败：提示人类先完成 `ingest` 阶段
- 人类未确认：暂停，等待人类输入 `confirm` 或编辑文件后运行 `workflow-continue`
- 退出校验失败（需求不完整）：根据校验器反馈补充缺失章节，重新校验
- 人类直接编辑文件后：运行 `workflow-continue`，Agent 重新读取文件并继续
