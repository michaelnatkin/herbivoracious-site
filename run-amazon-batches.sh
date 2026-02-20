#!/bin/bash
# Run amazon-links batches one at a time, fresh context each run.
# Each invocation picks the next open batch bead and processes it.
# Stops when no "Amazon links batch" beads remain.

set -e

LOG="amazon-batches.log"
BATCH=0

while true; do
  # Check how many batch beads remain
  REMAINING=$(bd list --status=open 2>/dev/null | grep -c "Amazon links batch" || true)

  if [ "$REMAINING" -eq 0 ]; then
    echo "=== All amazon links batches complete! ==="
    break
  fi

  BATCH=$((BATCH + 1))
  echo ""
  echo "========================================"
  echo "  Starting batch run #$BATCH  ($REMAINING remaining)"
  echo "  $(date)"
  echo "========================================"

  claude -p \
    --allowedTools "Bash,Edit,Read,Write,Glob,Grep,WebFetch,WebSearch,Skill,Task" \
    --max-turns 100 \
    "Pick the LOWEST-numbered open 'Amazon links batch' bead (use bd list --status=open | grep 'Amazon links batch').
Mark it in_progress, then process ALL 10 posts in that batch by running /amazon-links on each one.
Use 5 parallel Task agents (with model='sonnet') to process 2 posts each.
After all posts are done, commit the changes, close the bead, and run bd sync.
Do NOT push to remote." \
    2>&1 | tee -a "$LOG"

  echo ""
  echo "--- Batch run #$BATCH finished at $(date) ---" | tee -a "$LOG"
done

echo ""
echo "Done! Processed $BATCH batch runs. Full log in $LOG"
