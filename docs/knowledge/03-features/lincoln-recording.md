---
id: FEAT-001
title: Lincoln Recording TUI
status: shipped
merged_at: 2026-06-29
source_interview: [[01-interviews/2026-06-28-stakeholder-checkout]]
source_requirement: [[02-requirements/REQ-001]]
source_decision: [[04-decisions/DEC-001]]
source_issue: "3"
source_pr: "9"
related_issues: "#3 #4 #5 #6"
related_prs: "#7 #8 #9"
---

# Lincoln Recording TUI

Lincoln Recording 是一个基于终端的交互式录音工具，让产品经理可以在访谈现场一键启动录音、实时查看音量和时长，并在停止后生成对应的访谈处理命令。

## 业务知识

### 背景

产品经理在需求调研时需要快速录制用户访谈，并把录音自动转写、摘要、沉淀到项目知识库。原来的 `record-interview` Python CLI 已经能完成录音和触发 `process-interview`，但缺少一个统一的、可视化的入口。Lincoln Recording TUI 把配置加载、录音界面、快捷键和后续命令提示整合到一个 React + Ink 终端应用中。

### 用户需求

- 作为 **产品经理**，我希望输入一次命令就能打开录音界面，以便 **减少录制前的配置步骤**。
- 作为 **产品经理**，我希望在录制过程中看到实时音量和时长，以便 **确认录音质量**。
- 作为 **产品经理**，我希望停止录音后拿到下一步命令，以便 **继续触发转写和摘要流程**。

### 验收标准

- [x] `lincoln` 全局命令启动 TUI
- [x] 启动前显示 Ready Screen，展示 session、topic、design、branch
- [x] ↑/↓ 选择菜单项，Enter 确认，q/Esc 退出
- [x] 录音中显示实时时长和音量条
- [x] 停止后显示 `claude process-interview <sessionId>` 命令
- [x] 所有快捷键在测试中被覆盖

### 业务价值

把分散的录音脚本封装成统一的 TUI 入口，降低访谈录制的心智负担，保证每次录音都按 Lincoln 规范生成 session ID 和元数据。

## 技术知识

### 实现概述

Lincoln Recording TUI 是一个 Node.js + TypeScript 项目，使用 Ink（React for Terminal）渲染界面。它通过 `spawn` 调用 `record-interview` Python 后端完成实际录音，自身只负责 UI 状态管理和用户输入处理。

### 代码位置

- CLI 入口：`tools/lincoln/src/main.ts`
- 配置加载：`tools/lincoln/src/config/loadConfig.ts`
- TUI 应用根组件：`tools/lincoln/src/components/RecordingApp.tsx`
- 界面组件：`tools/lincoln/src/components/ReadyScreen.tsx`、`RecordingScreen.tsx`、`StopConfirmation.tsx`、`CancelledScreen.tsx`
- 录音控制器：`tools/lincoln/src/recording/useRecorder.ts`
- 按键处理：`tools/lincoln/src/hooks/useKeyHandler.ts`
- 测试：`tools/lincoln/tests/`

### 关键设计决策

- **TUI 不直接操作 ffmpeg**：录音逻辑保留在 `tools/record-interview` Python 后端，TUI 通过子进程通信。这样后端可以独立升级、独立测试。
- **不嵌套 spawn `claude`**：停止录音后，TUI 只打印 `claude process-interview <sessionId>` 命令，由用户在当前 shell 中执行。避免嵌套 Claude Code 会话和权限问题。
- **配置分层**：CLI 参数 > `.lincolnrc`（项目级）> `~/.lincolnrc`（用户级）> 默认值，保证不同项目的配置隔离。
- **状态机驱动 UI**：`RecordingApp` 通过 `phase` 和 `useRecorder` 的 `status` 决定渲染哪个界面，避免组件级条件判断扩散。
- **React hooks 依赖稳定化**：`useRecorder` 把 options 解构为原始值再传给 `useCallback`，防止每次渲染创建新对象导致无限重渲染。

### 依赖

- `ink` — React for Terminal
- `react` — UI 组件模型
- `js-yaml` — 解析 `.lincolnrc` YAML 配置
- `record-interview` — Python 后端录音和元数据生成

### API / 数据模型

#### CLI

```bash
lincoln [session-id] [options]
```

选项：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--topic` | 访谈主题 | "" |
| `--design-id` | 设计 ID | "" |
| `--branch` | Lincoln feature 分支名 | "" |
| `--workspace-root` | 工作区根目录 | `process.cwd()` |
| `--audio-meter-style` | 音量条样式（bar/dot/wave） | `bar` |
| `--config` | 配置文件路径 | `.lincolnrc` 或 `~/.lincolnrc` |
| `--record-interview-path` | `record-interview` 可执行文件路径 | 在 PATH 中查找 |

#### 配置示例（`.lincolnrc`）

```yaml
topic: "结算流程 redesign 需求访谈"
design-id: checkout-redesign
branch: lincoln/2026-06-28-recording-checkout-redesign
audio-meter-style: wave
```

### 测试要点

- Ready Screen 渲染 session/topic/design/branch
- 菜单选择器响应 ↑/↓ 和 Enter
- q/Esc 调用 `useApp().exit()`
- 录音中调用 `stop()` / `cancel()`
- 停止后显示 process-interview 命令
- `useRecorder` 依赖稳定，不会无限重渲染

## 关联

- 访谈：[[01-interviews/2026-06-28-stakeholder-checkout]]
- 需求：[[02-requirements/REQ-001]]
- 决策：[[04-decisions/DEC-001]]
- Issue：#3、#4、#5、#6
- PR：#7、#8、#9
- OpenSpec 变更：[[06-references/openspec-changes#lincoln-tui-recorder]]
- 详细使用说明：[[../../tools/lincoln/README]]
- 后端说明：[[../../tools/record-interview/README]]
