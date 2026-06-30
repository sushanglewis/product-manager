# Lincoln 评估标准

本文档定义 Lincoln 工作流的健康度评估维度、自动检查命令、人工抽查要点，以及 PASS/WARN/FAIL 判定标准。

---

## 评估维度

### 1. 阶段可追溯性（Stage Traceability）

**定义**：每个产物是否能追溯到生成它的阶段、Run、分支和触发命令。

**自动检查**：

```bash
# 检查 workflow-state.yaml 中所有 completed_stages 是否有对应产物记录
python scripts/lincoln-audit.py --dimension traceability

# 检查产物 frontmatter 是否包含 stage / run_id / branch 字段
python scripts/lincoln-audit.py --check-artifact-frontmatter
```

**人工抽查要点**：
- 随机抽取 3 个产物文件，检查 frontmatter 是否包含 `lincoln_stage`、`lincoln_run_id`、`generated_at`
- 检查 `.claude/workflow-state.yaml` 中的 `completed_stages` 与产物目录结构是否一致
- 确认不存在"孤儿产物"（有文件但无阶段记录）或"幽灵阶段"（有记录但无产物）

**判定标准**：

| 等级 | 条件 |
|------|------|
| PASS | 100% 产物有 frontmatter，0 个孤儿产物，0 个幽灵阶段 |
| WARN | 90% 产物有 frontmatter，或存在 1-2 个孤儿/幽灵项 |
| FAIL | 低于 90% 产物有 frontmatter，或存在 3+ 个孤儿/幽灵项 |

---

### 2. 人工门控合规性（Human Gate Compliance）

**定义**：标记 `human_gate: true` 的阶段是否都获得了人类 PM 的显式确认。

**自动检查**：

```bash
# 检查所有 human_gate=true 阶段是否有确认记录
python scripts/lincoln-audit.py --dimension human-gate

# 检查 stage-manifest.yaml 中 human_gate 标记与 workflow-state.yaml 中确认记录的一致性
python scripts/lincoln-audit.py --check-gate-consistency
```

**人工抽查要点**：
- 检查 `workflow-state.yaml` 中每个 `human_gate: true` 阶段的 `human_confirmed_at` 时间戳是否存在
- 检查确认时间戳是否合理（不早于阶段开始时间，不晚于下一阶段开始时间）
- 抽查 1-2 个门控阶段的产物文件，确认内容确实经过人类修改或确认标记

**判定标准**：

| 等级 | 条件 |
|------|------|
| PASS | 100% human_gate 阶段有确认记录，时间戳合理 |
| WARN | 存在 1 个门控阶段缺少确认记录，但产物内容完整 |
| FAIL | 存在 2+ 门控阶段缺少确认记录，或确认时间戳异常 |

---

### 3. 产物完整性（Artifact Completeness）

**定义**：每个阶段应生成的产物是否全部存在、格式正确、内容非空。

**自动检查**：

```bash
# 检查所有 required_artifacts 是否存在
python scripts/lincoln-audit.py --dimension artifacts

# 检查产物文件大小（排除空文件）
python scripts/lincoln-audit.py --check-artifact-size --min-bytes 100

# 检查 YAML/JSON 产物格式正确性
python scripts/lincoln-audit.py --check-format-validity
```

**人工抽查要点**：
- 随机抽取 2 个阶段的产物，检查是否覆盖该阶段 CHECKLIST.md 中列出的全部输出项
- 检查 Markdown 产物是否有合理的标题结构和内容（非模板占位符）
- 检查 `.pen` 文件是否只能通过 Pencil 工具处理（非文本编辑痕迹）

**判定标准**：

| 等级 | 条件 |
|------|------|
| PASS | 100% required_artifacts 存在、非空、格式正确 |
| WARN | 90% 产物存在且完整，或存在 1-2 个格式警告 |
| FAIL | 低于 90% 产物存在，或存在空文件、格式错误 |

---

### 4. 技能覆盖度（Skill Coverage）

**定义**：每个阶段是否调用了 `skill-routing.yaml` 中声明的 required 技能，optional 技能使用是否合理。

**自动检查**：

```bash
# 检查 workflow-state.yaml 中 skills_invoked 与 skill-routing.yaml 的一致性
python scripts/lincoln-audit.py --dimension skill-coverage

# 检查是否有阶段完全未记录技能调用
python scripts/lincoln-audit.py --check-empty-skill-runs
```

**人工抽查要点**：
- 检查 `.omc/state/lincoln-trace.jsonl` 中技能调用记录是否与阶段匹配
- 抽查 2-3 个阶段，确认 required 技能确实被调用
- 检查是否有不合理的技能调用（如 `implement` 阶段调用 `openspec:explore`）

**判定标准**：

| 等级 | 条件 |
|------|------|
| PASS | 100% 阶段有技能调用记录，required 技能全部覆盖，无异常调用 |
| WARN | 存在 1-2 个阶段缺少技能记录，或存在 1 个异常调用 |
| FAIL | 存在 3+ 阶段无技能记录，或存在 2+ 异常调用 |

---

### 5. 跨会话状态一致性（Cross-Session State Consistency）

**定义**：同一分支在不同会话、不同 Agent 窗口中加载时，状态是否一致。

**自动检查**：

```bash
# 检查 workflow-state.yaml 与 stage-manifest.yaml 的一致性
python scripts/lincoln-audit.py --dimension state-consistency

# 检查当前分支状态与 git 历史是否一致（阶段推进是否有对应提交）
python scripts/lincoln-audit.py --check-git-history

# 运行状态命令验证可读性
python scripts/lincoln-status.py --format json
python scripts/lincoln-status.py --format markdown
```

**人工抽查要点**：
- 模拟新 Conductor 窗口打开分支，检查 Agent 是否能正确汇报当前阶段
- 检查 `.claude/workflow-state.yaml` 中的 `current_stage` 与最新 git 提交信息是否一致
- 检查 `.context/lincoln-handoff.md`（如有）是否包含准确的交接信息

**判定标准**：

| 等级 | 条件 |
|------|------|
| PASS | 状态文件与 git 历史一致，新窗口能正确加载，handoff 文档准确 |
| WARN | 存在轻微不一致（如时间戳偏差），但不影响阶段判断 |
| FAIL | 状态文件与 git 历史矛盾，或新窗口无法正确识别阶段 |

---

### 6. GitHub 交接完整性（GitHub Handoff Completeness）

**定义**：从 Lincoln 工作流到 GitHub Issues/PR 的交接是否完整，信息是否可追溯。

**自动检查**：

```bash
# 检查 GitHub Issues 是否包含 Lincoln 来源信息
python scripts/lincoln-audit.py --dimension github-handoff

# 检查 PR 是否使用 Lincoln 交接模板
python scripts/lincoln-audit.py --check-pr-template
```

**人工抽查要点**：
- 检查 GitHub Issues 是否包含：访谈来源、需求链接、OpenSpec 变更链接、验收标准
- 检查 PR 描述是否填写 `.github/PULL_REQUEST_TEMPLATE/lincoln-handoff.md` 中的字段
- 检查 PR 合并后是否有对应的 `.github/lincoln-sync-queue/pr-<number>.yaml` 文件

**判定标准**：

| 等级 | 条件 |
|------|------|
| PASS | 100% Issue/PR 包含 Lincoln 来源信息，交接模板填写完整 |
| WARN | 存在 1-2 个 Issue/PR 缺少部分来源信息 |
| FAIL | 存在 3+ 个 Issue/PR 缺少来源信息，或未使用交接模板 |

---

## 综合评估命令

### 一键审计

```bash
# 运行全部审计维度，输出综合报告
python scripts/lincoln-audit.py --all

# 输出示例：
# ============================================
# Lincoln 工作流健康度审计报告
# 分支: lincoln/2026-06-27-stakeholder-checkout-redesign
# 运行时间: 2026-06-30T14:32:00
# ============================================
# 
# 1. 阶段可追溯性    [PASS]  24/24 产物有 frontmatter
# 2. 人工门控合规性  [PASS]  5/5 门控已确认
# 3. 产物完整性      [WARN]  23/24 产物完整（designs/xxx/feasibility.md 为空）
# 4. 技能覆盖度      [PASS]  12/12 阶段有技能记录
# 5. 状态一致性      [PASS]  workflow-state.yaml 与 git 历史一致
# 6. GitHub 交接     [PASS]  8/8 Issue/PR 来源完整
# 
# 综合评级: PASS (1 项 WARN)
# 建议: 补充 feasibility.md 内容
```

### 状态检查

```bash
# 查看当前分支状态（人类可读）
python scripts/lincoln-status.py --format markdown

# 查看当前分支状态（机器可读）
python scripts/lincoln-status.py --format json

# 查看当前分支状态（表格）
python scripts/lincoln-status.py --format table
```

---

## 评估频率建议

| 时机 | 评估维度 | 执行者 |
|------|----------|--------|
| 每次阶段推进后 | 产物完整性、阶段可追溯性 | Agent（自动） |
| 每次人类门控后 | 人工门控合规性 | Agent（自动） |
| 每次会话启动时 | 跨会话状态一致性 | Agent（自动） |
| 每周 / 每里程碑 | 全部六维度 | Tech Lead（手动运行 `lincoln-audit.py --all`） |
| PR 合并前 | GitHub 交接完整性 | Engineer（手动检查） |

---

## 修复流程

当审计发现 WARN 或 FAIL 时：

1. **Agent 自动修复**：`scripts/lincoln-audit.py --auto-fix` 尝试修复格式错误、补充缺失的 frontmatter。
2. **人工审查**：Tech Lead 运行 `lincoln-status.py` 确认当前状态，判断是否需要回退阶段。
3. **阶段回退**：若状态严重不一致，使用 `scripts/stage_loader.py --stage <stage> --action recover` 回退到最近一致状态。
4. **重新执行**：从回退点重新执行阶段，确保产物和记录完整。
