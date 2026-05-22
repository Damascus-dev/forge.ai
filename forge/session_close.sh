#!/usr/bin/env bash
set -euo pipefail
# session_close.sh — Finalize session logs, generate summary, update bootstrap
# Run at the end of each orchestrator session.

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$FORGE_DIR/.." && pwd)"
LOG_FILE="/tmp/forge-agent-log.jsonl"
SESSION_LOG="${FORGE_DIR}/logs/sessions.jsonl"
SUMMARY="${FORGE_DIR}/logs/session-summary.md"
BOOTSTRAP="${REPO_DIR}/BOOTSTRAP.md"
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "=== session_close.sh — $DATE ==="

# 1. Check if there are logs to process
if [ ! -s "$LOG_FILE" ] || [ "$(jq length "$LOG_FILE" 2>/dev/null || echo 0)" -eq 0 ]; then
    echo "No logs to process. Skipping."
    exit 0
fi

# 2. Group logs by agent
echo "Processing agent logs..."

AGENTS_RAW=$(jq -r '[.[].agent] | unique[]' "$LOG_FILE" 2>/dev/null || echo "unknown")
AGENTS=$(echo "$AGENTS_RAW" | tr '\n' ', ' | sed 's/,$//')
ACTION_COUNT=$(jq length "$LOG_FILE" 2>/dev/null || echo 0)

declare -A COUNTS
for agent in $AGENTS_RAW; do
    count=$(jq "[.[] | select(.agent == \"$agent\")] | length" "$LOG_FILE" 2>/dev/null || echo 0)
    COUNTS["$agent"]=$count
done

# 3. Append raw logs to cumulative archive
echo "Archiving $ACTION_COUNT actions to sessions.jsonl..."
jq -c ".[]" "$LOG_FILE" >> "$SESSION_LOG"

# 4. Extract action details for summary
ACTIONS_DETAILS=$(jq -r '.[] | "- \(.agent): \(.action) → \(.result)"' "$LOG_FILE" 2>/dev/null || echo "- No detailed logs")

# 5. Generate session-summary.md
echo "Writing session summary..."

cat > "$SUMMARY" <<SUMMARYEOF
# Session Summary — $(date -u +"%Y-%m-%d %H:%M UTC")

## Overview
- **Total actions**: $ACTION_COUNT
- **Agents active**: $AGENTS
- **Date**: $DATE

## Actions by Agent
SUMMARYEOF

for agent in $AGENTS_RAW; do
    count=${COUNTS[$agent]:-0}
    echo "- **@$agent**: $count actions" >> "$SUMMARY"
done

cat >> "$SUMMARY" <<SUMMARYEOF

## Action Log
\`\`\`
$ACTIONS_DETAILS
\`\`\`

## Files Changed
\`\`\`
$(cd "$REPO_DIR" && git diff --name-only 2>/dev/null || true)
$(cd "$REPO_DIR" && git diff --cached --name-only 2>/dev/null || true)
\`\`\`

## Git Diff Stats
\`\`\`
$(cd "$REPO_DIR" && git diff --stat 2>/dev/null || echo "(clean working tree)")
\`\`\`

## Handoff
- Full details: \`forge/SESSION_HANDOFF.md\`
- Raw archive: \`forge/logs/sessions.jsonl\`
- Bootstrap: \`BOOTSTRAP.md\`
SUMMARYEOF

echo "Summary written to $SUMMARY"

# 6. Update BOOTSTRAP.md session reference
echo "Updating BOOTSTRAP.md session link..."

if grep -q "<!-- SESSION_LATEST -->" "$BOOTSTRAP" 2>/dev/null; then
    sed -i "s|<!-- SESSION_LATEST -->.*|<a href=\"forge/logs/session-summary.md\">$DATE</a>|" "$BOOTSTRAP"
    echo "Bootstrap session link updated → $DATE"
else
    echo "Warning: <!-- SESSION_LATEST --> anchor not found in BOOTSTRAP.md"
fi

# 7. Clear temp log
echo "Clearing temp log..."
echo '[]' > "$LOG_FILE"

echo "=== Session close complete ==="
echo "Summary: $SUMMARY"
echo "Actions archived: $ACTION_COUNT"
