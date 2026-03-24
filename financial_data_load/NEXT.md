# Next Steps: Cleanse Pipeline

## Run the full pipeline

```bash
cd financial_data_load
./run_cleanse.sh
```

## Resume from a specific step

```bash
./run_cleanse.sh 2    # start from dedup (skip validation)
./run_cleanse.sh 3    # start from apply-cleanse (uses latest plan)
./run_cleanse.sh 4    # just finalize
```

## What each step does

1. **Validation** — parallel LLM validation across all entity types, removes non-entities
2. **Dedup** — runs dedup sequentially across all entity types
3. **Apply cleanse** — executes removals, merges, then normalization (parallel across entity types)
4. **Finalize** — constraints, indexes, asset managers, verify

## Notes

- Each step checkpoints after every completed entity label
- If a step fails, re-run from that step number — it picks up the latest plan from `plans/`
- RiskFactor and FinancialMetric dedup thresholds are set to 0.85 to keep candidate pairs manageable
- To review the plan before applying: `cat plans/cleanse_plan_*.json | python -m json.tool`
