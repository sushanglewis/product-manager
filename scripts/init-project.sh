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

# ---------------------------------------------------------------------------
# 2. Ensure placeholder files exist for empty tracked directories
# ---------------------------------------------------------------------------
mkdir -p recordings interviews requirements openspec/changes .context docs/knowledge/assets

touch recordings/.gitkeep
[ -f interviews/.gitkeep ] || touch interviews/.gitkeep
[ -f requirements/.gitkeep ] || touch requirements/.gitkeep
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

echo "✅ OpenSpec config valid"

# ---------------------------------------------------------------------------
# 5. Make validator executable
# ---------------------------------------------------------------------------
VALIDATOR=".claude/skills/interview-workflow/validators/validate.py"
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
# 7. Initial commit
# ---------------------------------------------------------------------------
if [ -z "$(git status --porcelain)" ]; then
  echo "ℹ️  No changes to commit"
else
  git add -A
  git commit -m "chore: init project with Lincoln workflow" || true
  echo "✅ Initial commit created"
fi

echo ""
echo "🎉 Lincoln project initialized successfully!"
echo ""
echo "Next steps:"
echo "  1. Place an interview recording in recordings/"
echo "  2. Run: claude process-interview recordings/<file>"
