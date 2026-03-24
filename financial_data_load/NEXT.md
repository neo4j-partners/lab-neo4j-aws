# Next Steps: Full Pipeline

## Run the full pipeline

```bash
cd financial_data_load
./run_cleanse.sh .env.final
```

## Resume from a specific step

```bash
./run_cleanse.sh .env.final 3    # start from validation (skip load/backup)
./run_cleanse.sh .env.final 5    # start from apply-cleanse (uses latest plan)
./run_cleanse.sh .env.final 6    # just normalize + finalize
./run_cleanse.sh .env.final 7    # just finalize
```

## What each step does

1. **Load** — clear DB, load CSV metadata, process all PDFs via LLM (~25 min)
2. **Backup** — snapshot post-load state to JSON (skip PDF reprocessing on reruns)
3. **Validation** — parallel LLM validation across all entity types, removes non-entities
4. **Dedup** — runs dedup sequentially across all entity types
5. **Apply cleanse** — executes removals and merges (no normalization)
6. **Normalize** — LLM-based description/field cleanup (parallel across entity types)
7. **Finalize** — constraints, indexes, asset managers, verify

## Notes

- Each cleanse step checkpoints after every completed entity label
- If a step fails, re-run from that step number — it picks up the latest plan from `plans/`
- RiskFactor and FinancialMetric dedup thresholds are set to 0.95 to keep candidate pairs manageable
- To review the plan before applying: `cat plans/cleanse_plan_*.json | python -m json.tool`
- Normalize can be rerun independently: `uv run python main.py normalize`
