# Lincoln — 产品经理需求调研工作流模板

这是一个 **GitHub Template Repository**，用于快速初始化一个基于 **Conductor + Claude Code + OpenSpec + GitHub + Obsidian** 的产品经理需求调研与研发协作工作区。

每个从该模板创建的项目都拥有：
- 独立的文件空间
- 独立的 Obsidian Wiki Vault（项目知识库）
- 标准的访谈 → 需求 → OpenSpec → GitHub Issues → 知识库沉淀 工作流
- Claude Code skill 包约束 Agent 按规范执行

## 快速开始

### 1. 从模板创建项目

在 GitHub 上点击 **Use this template**，创建新项目仓库，然后 clone 到本地 Conductor 工作区。

### 2. 初始化项目

进入项目目录后运行：

```bash
scripts/init-project.sh
```

脚本会：
- 校验依赖（ffmpeg、whisper、gh、openspec CLI）
- 创建 Obsidian vault 基础结构
- 读取 `.github/openspec-config.yml` 中的目标仓库配置
- 提交初始 commit

### 3. 配置 GitHub 目标仓库

编辑 `.github/openspec-config.yml`：

```yaml
repository:
  owner: your-org
  name: your-product-repo
  default_branch: main
```

### 4. 运行工作流

#### Step 1: 放入访谈录音

将音频文件放入 `recordings/`：

```bash
cp ~/Downloads/2026-06-27-stakeholder.m4a recordings/
```

#### Step 2: 触发访谈处理

```bash
claude process-interview recordings/2026-06-27-stakeholder.m4a
```

Agent 会生成：
- `interviews/2026-06-27-stakeholder/metadata.json`
- `interviews/2026-06-27-stakeholder/transcript.md`
- `interviews/2026-06-27-stakeholder/summary.md`
- `interviews/2026-06-27-stakeholder/raw-insights.md`

#### Step 3: 需求澄清

```bash
claude clarify-requirements 2026-06-27-stakeholder
```

Agent 会基于访谈内容提问，与你多轮澄清后生成：
- `requirements/2026-06-27-stakeholder/requirements.md`
- `requirements/2026-06-27-stakeholder/user-stories.md`
- `requirements/2026-06-27-stakeholder/prd.md`

#### Step 4: OpenSpec 提案

```bash
claude propose-with-openspec 2026-06-27-stakeholder
```

Agent 调用 `openspec propose` 生成：
- `openspec/changes/<change-name>/proposal.md`
- `openspec/changes/<change-name>/specs/`
- `openspec/changes/<change-name>/design.md`
- `openspec/changes/<change-name>/tasks.md`

#### Step 5: 拆分到 GitHub

```bash
claude split-to-github 2026-06-27-stakeholder
```

Agent 将 OpenSpec tasks 拆分为 GitHub Issues。

#### Step 6: 研发实现

研发团队基于 GitHub Issues 开发，提交 PR。

#### Step 7: 同步到知识库

PR 合并后，GitHub Action 自动触发 Agent 更新 Obsidian vault：
- `docs/knowledge/01-interviews/2026-06-27-stakeholder.md`
- `docs/knowledge/02-requirements/REQ-xxx.md`
- `docs/knowledge/03-features/<feature-slug>.md`
- `docs/knowledge/04-decisions/<decision-id>.md`

## 工作流概览

```
访谈录音 → 转写摘要 → 需求澄清 → OpenSpec 提案 → GitHub Issues → 代码实现 → PR 合并 → Obsidian 知识库
```

## 目录结构

```
.
├── recordings/              # 原始音频（gitignored）
├── interviews/              # 转写和摘要产物
├── requirements/            # 需求文档
├── openspec/                # OpenSpec 变更目录
├── docs/knowledge/          # 项目独立 Obsidian vault
├── .claude/                 # Claude Code skill 与工作流
├── .github/                 # GitHub issue 模板、Actions、配置
└── scripts/                 # 初始化脚本
```

## 依赖

- `ffmpeg`
- `faster-whisper` 或 OpenAI Whisper API key
- `gh` CLI（已登录）
- `openspec` CLI：`npm install -g @fission-ai/openspec`
- `ecc` CLI（来自 everything-claude-code）
- Obsidian（可选，用于可视化浏览 vault）

## 规范约束

Agent 必须遵守：
- `.claude/AGENTS.md` — Agent 行为总则
- `.claude/workflows/interview-to-knowledge.yaml` — 工作流定义
- `.claude/skills/interview-workflow/validators/` — 准入准出校验

人类产品经理拥有以下节点的最终确认权：
- 需求澄清完成
- OpenSpec 提案确认
- GitHub Issues 拆分确认
- 研发实现完成

## 了解更多

- [OpenSpec 文档](https://github.com/Fission-AI/openspec)
- [Obsidian WikiLinks](https://help.obsidian.md/Linking+notes+and+files/Internal+links)
