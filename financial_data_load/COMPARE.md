# Model Comparison: gpt-4o vs gpt-4.1-mini

Entity extraction quality comparison for SEC 10-K knowledge graph pipeline.

## Current State (gpt-4o baseline)

| Entity Type     | Count |
|-----------------|-------|
| Company         | 186   |
| RiskFactor      | 579   |
| Product         | 461   |
| Executive       | 54    |
| FinancialMetric | 412   |
| Chunk           | 390   |
| Document        | 8     |

Total entities: 1,692 (excluding Chunk/Document)
Total schema relationships: 1,637

## TODO

- [x] Export gpt-4o baseline snapshot → `model_snapshots/gpt-4o_20260322_122912.json`
- [x] Deploy gpt-4.1-mini to Azure AI Services (GlobalStandard, 360 capacity)
- [ ] Clear database and re-extract with gpt-4.1-mini (first attempt failed — `financial_data_load/.env` had stale `gpt-4o`, fixed)
- [ ] Export gpt-4.1-mini snapshot
- [ ] Run comparison and record results below

## Results

_Pending — will be filled in after both extractions complete._
