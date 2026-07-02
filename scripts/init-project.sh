#!/usr/bin/env bash
set -euo pipefail

# Lincoln Project Initialization Script
# Run this after creating a new project from the Lincoln GitHub template.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🚀 Initializing Lincoln project at $PROJECT_ROOT"

# ---------------------------------------------------------------------------
# 1. Verify git repository
# ---------------------------------------------------------------------------
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "❌ Error: not a git repository. Please run 'git init' first."
  exit 1
fi

INITIAL_STATUS="$(git status --porcelain)"

# ---------------------------------------------------------------------------
# 2. Ensure placeholder files exist for empty tracked directories
# ---------------------------------------------------------------------------
mkdir -p recordings interviews requirements designs openspec/changes .context docs/knowledge/assets

touch recordings/.gitkeep
[ -f interviews/.gitkeep ] || touch interviews/.gitkeep
[ -f requirements/.gitkeep ] || touch requirements/.gitkeep
[ -f designs/.gitkeep ] || touch designs/.gitkeep
[ -f openspec/changes/.gitkeep ] || touch openspec/changes/.gitkeep
[ -f docs/knowledge/assets/.gitkeep ] || touch docs/knowledge/assets/.gitkeep

# ---------------------------------------------------------------------------
# 3. Check dependencies
# ---------------------------------------------------------------------------
MISSING=()

check_command() {
  if ! command -v "$1" > /dev/null 2>&1; then
    MISSING+=("$2")
  fi
}

check_command ffmpeg "ffmpeg (install via brew install ffmpeg)"
check_command gh "GitHub CLI (install via brew install gh)"
check_command openspec "OpenSpec CLI (npm install -g @fission-ai/openspec)"

# Check for a Whisper implementation
if ! command -v faster-whisper > /dev/null 2>&1 && \
   ! python3 -c "import whisper" > /dev/null 2>&1 && \
   ! command -v whisper > /dev/null 2>&1; then
  MISSING+=("Whisper implementation (faster-whisper, openai-whisper, or whisper CLI)")
fi

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "❌ Missing dependencies:"
  for dep in "${MISSING[@]}"; do
    echo "  - $dep"
  done
  echo ""
  echo "Please install missing dependencies and re-run this script."
  exit 1
fi

echo "✅ All required dependencies found"

# ---------------------------------------------------------------------------
# 4. Validate OpenSpec config
# ---------------------------------------------------------------------------
CONFIG_FILE=".github/openspec-config.yml"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Error: $CONFIG_FILE not found"
  exit 1
fi

if ! grep -qE "^repository:" "$CONFIG_FILE" || \
   ! grep -qE "owner:\s*\S+" "$CONFIG_FILE" || \
   ! grep -qE "name:\s*\S+" "$CONFIG_FILE"; then
  echo "❌ Error: $CONFIG_FILE must define repository.owner and repository.name"
  echo "   Please edit $CONFIG_FILE and set your target GitHub repository."
  exit 1
fi

REPO_OWNER="$(sed -nE 's/^[[:space:]]*owner:[[:space:]]*"?([^"#]+)"?.*/\1/p' "$CONFIG_FILE" | head -1 | xargs)"
REPO_NAME="$(sed -nE 's/^[[:space:]]*name:[[:space:]]*"?([^"#]+)"?.*/\1/p' "$CONFIG_FILE" | head -1 | xargs)"

if [ "$REPO_OWNER" = "your-org" ] || [ "$REPO_NAME" = "your-product-repo" ]; then
  echo "❌ Error: $CONFIG_FILE still contains the default placeholder repository."
  echo "   Set repository.owner and repository.name to the real target repository before initialization."
  exit 1
fi

echo "✅ OpenSpec config valid"

# ---------------------------------------------------------------------------
# 5. Make validator executable
# ---------------------------------------------------------------------------
VALIDATOR="scripts/validate_stage.py"
if [ -f "$VALIDATOR" ]; then
  chmod +x "$VALIDATOR"
  echo "✅ Validator made executable"
fi

# ---------------------------------------------------------------------------
# 6. GitHub CLI auth check
# ---------------------------------------------------------------------------
if ! gh auth status > /dev/null 2>&1; then
  echo "⚠️  GitHub CLI is not authenticated. Run 'gh auth login' before using split-to-github."
else
  echo "✅ GitHub CLI authenticated"
fi

# ---------------------------------------------------------------------------
# 7. Initial commit for files created by this script
# ---------------------------------------------------------------------------
if [ -z "$(git status --porcelain)" ]; then
  echo "ℹ️  No changes to commit"
elif [ -n "$INITIAL_STATUS" ]; then
  echo "⚠️  Existing local changes detected before initialization; skipping automatic commit."
  echo "   Review and commit the changes manually when ready."
else
  git add \
    recordings/.gitkeep \
    interviews/.gitkeep \
    requirements/.gitkeep \
    designs/.gitkeep \
    openspec/changes/.gitkeep \
    docs/knowledge/assets/.gitkeep
  if git diff --cached --quiet; then
    echo "ℹ️  No tracked initialization changes to commit"
  else
    git commit -m "chore: init project with Lincoln workflow"
    echo "✅ Initial commit created"
  fi
fi

echo ""
echo "🎉 Lincoln project initialized successfully!"
echo ""
echo "Next steps:"
echo "  1. Place an interview recording in recordings/"
echo "  2. Say to Claude Code: '处理一下这个访谈录音 recordings/<file>'"
