#!/bin/bash
# Script to check CI/CD workflows after push and fix issues until all are green

set -e

MAX_ITERATIONS=10
ITERATION=0

echo "🔍 Starting CI/CD check and fix loop..."
echo ""

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))
    echo "📊 Iteration $ITERATION: Checking workflow runs..."

    # Wait for workflows to complete
    sleep 10

    # Get latest runs
    LATEST_RUNS=$(gh run list --limit 5 --json databaseId,conclusion,status,workflowName --jq '.[] | select(.status == "completed") | {id: .databaseId, conclusion: .conclusion, workflow: .workflowName}')

    # Check for failures
    FAILED_RUNS=$(echo "$LATEST_RUNS" | jq -r 'select(.conclusion != "success" and .conclusion != null) | "\(.workflow):\(.id)"')

    if [ -z "$FAILED_RUNS" ]; then
        echo "✅ All workflows are passing!"
        exit 0
    fi

    echo "❌ Found failed workflows:"
    echo "$FAILED_RUNS"
    echo ""

    # Check specific failures
    NEEDS_FIX=false

    for RUN_INFO in $FAILED_RUNS; do
        WORKFLOW=$(echo "$RUN_INFO" | cut -d: -f1)
        RUN_ID=$(echo "$RUN_INFO" | cut -d: -f2)

        echo "🔍 Checking $WORKFLOW (run $RUN_ID)..."

        # Check for pre-commit failures (missing newlines)
        PRE_COMMIT_FAILURE=$(gh run view "$RUN_ID" --log-failed 2>&1 | grep -i "end-of-file\|newline" | head -1 || true)

        if [ -n "$PRE_COMMIT_FAILURE" ]; then
            echo "🔧 Fixing pre-commit issues (missing newlines)..."
            uv run pre-commit run --all-files || true
            git add -A
            if git diff --cached --quiet; then
                echo "ℹ️  No changes to commit"
            else
                git commit -m "fix: Auto-fix pre-commit issues (missing newlines)"
                NEEDS_FIX=true
            fi
        fi

        # Check for other specific failures
        FAILURE_LOG=$(gh run view "$RUN_ID" --log-failed 2>&1 | head -100)

        echo "📋 Failure details:"
        echo "$FAILURE_LOG" | head -20
        echo ""
    done

    if [ "$NEEDS_FIX" = true ]; then
        echo "🚀 Pushing fixes..."
        git push
        echo "⏳ Waiting for workflows to run..."
        sleep 20
    else
        echo "⚠️  No automatic fixes available. Manual intervention needed."
        exit 1
    fi

    echo ""
done

echo "⚠️  Reached maximum iterations ($MAX_ITERATIONS). Some workflows may still be failing."
exit 1
