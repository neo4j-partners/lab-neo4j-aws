#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

START_STEP="${1:-1}"

latest_plan() {
    ls -t plans/cleanse_plan_*.json 2>/dev/null | head -1
}

if [ "$START_STEP" -le 1 ]; then
    echo "=== Step 1: Validation (parallel across entity types) ==="
    uv run python main.py cleanse --phase validate

    PLAN=$(latest_plan)
    if [ -z "$PLAN" ]; then
        echo "ERROR: No cleanse plan found after validation"
        exit 1
    fi
    echo "Plan after validation: $PLAN"
fi

if [ "$START_STEP" -le 2 ]; then
    PLAN=$(latest_plan)
    if [ -z "$PLAN" ]; then
        echo "ERROR: No cleanse plan found. Run from step 1."
        exit 1
    fi

    echo ""
    echo "=== Step 2: Dedup (all entity types) ==="
    echo "Using base plan: $PLAN"
    uv run python main.py cleanse --phase dedup --base-plan "$PLAN"

    PLAN=$(latest_plan)
    echo "Dedup plan: $PLAN"
fi

if [ "$START_STEP" -le 3 ]; then
    PLAN=$(latest_plan)
    if [ -z "$PLAN" ]; then
        echo "ERROR: No cleanse plan found. Run from step 1."
        exit 1
    fi

    echo ""
    echo "=== Step 3: Apply cleanse (removals -> merges) ==="
    uv run python main.py apply-cleanse --plan "$PLAN" --skip-normalize
fi

if [ "$START_STEP" -le 4 ]; then
    echo ""
    echo "=== Step 4: Normalize ==="
    uv run python main.py normalize
fi

if [ "$START_STEP" -le 5 ]; then
    echo ""
    echo "=== Step 5: Finalize ==="
    uv run python main.py finalize
fi

echo ""
echo "=== Done ==="
