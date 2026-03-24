#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# ---------------------------------------------------------------------------
# Usage: ./run_cleanse.sh <env-file> [start-step]
#
#   ./run_cleanse.sh .env.final        # Full pipeline from PDF load to finalize
#   ./run_cleanse.sh .env.final 3      # Start from validation (skip load/backup)
# ---------------------------------------------------------------------------

if [ $# -lt 1 ]; then
    echo "Usage: $0 <env-file> [start-step]"
    echo ""
    echo "  env-file    Path to .env file (e.g. .env, .env.final)"
    echo "  start-step  Step to start from (1-7, default: 1)"
    echo ""
    echo "Steps:"
    echo "  1  Load (clear DB, load CSV metadata, process PDFs via LLM)"
    echo "  2  Backup (snapshot post-load state to JSON)"
    echo "  3  Validation (parallel LLM validation across entity types)"
    echo "  4  Dedup (sequential dedup across entity types)"
    echo "  5  Apply cleanse (removals + merges, skip normalize)"
    echo "  6  Normalize (LLM description cleanup)"
    echo "  7  Finalize (constraints, indexes, asset managers, verify)"
    exit 1
fi

ENV_FILE="$1"
START_STEP="${2:-1}"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: env file not found: $ENV_FILE"
    exit 1
fi

# Export all variables from the env file. load_dotenv won't override
# existing env vars, so the sourced values take precedence.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

echo "Using env: $ENV_FILE"
echo ""

latest_plan() {
    ls -t plans/cleanse_plan_*.json 2>/dev/null | head -1
}

if [ "$START_STEP" -le 1 ]; then
    echo "=== Step 1: Load (clear + CSV metadata + PDF processing) ==="
    uv run python main.py load --clear
fi

if [ "$START_STEP" -le 2 ]; then
    echo ""
    echo "=== Step 2: Backup ==="
    uv run python main.py backup
fi

if [ "$START_STEP" -le 3 ]; then
    echo ""
    echo "=== Step 3: Validation (parallel across entity types) ==="
    uv run python main.py cleanse --phase validate

    PLAN=$(latest_plan)
    if [ -z "$PLAN" ]; then
        echo "ERROR: No cleanse plan found after validation"
        exit 1
    fi
    echo "Plan after validation: $PLAN"
fi

if [ "$START_STEP" -le 4 ]; then
    PLAN=$(latest_plan)
    if [ -z "$PLAN" ]; then
        echo "ERROR: No cleanse plan found. Run from step 3."
        exit 1
    fi

    echo ""
    echo "=== Step 4: Dedup (all entity types) ==="
    echo "Using base plan: $PLAN"
    uv run python main.py cleanse --phase dedup --base-plan "$PLAN"

    PLAN=$(latest_plan)
    echo "Dedup plan: $PLAN"
fi

if [ "$START_STEP" -le 5 ]; then
    PLAN=$(latest_plan)
    if [ -z "$PLAN" ]; then
        echo "ERROR: No cleanse plan found. Run from step 3."
        exit 1
    fi

    echo ""
    echo "=== Step 5: Apply cleanse (removals -> merges) ==="
    uv run python main.py apply-cleanse --plan "$PLAN" --skip-normalize
fi

if [ "$START_STEP" -le 6 ]; then
    echo ""
    echo "=== Step 6: Normalize ==="
    uv run python main.py normalize
fi

if [ "$START_STEP" -le 7 ]; then
    echo ""
    echo "=== Step 7: Finalize ==="
    uv run python main.py finalize
fi

echo ""
echo "=== Done ==="
