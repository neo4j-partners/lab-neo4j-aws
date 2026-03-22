# SEC 10-K Financial Data Architecture

This document describes the graph data model used for the SEC 10-K financial filing workshop.

## Graph Schema

### Node Types and Properties

| Node Label | Properties | Source File |
|---|---|---|
| **Company** | company_id, name, ticker, sector, cik, fiscal_year_end | `companies.csv` |
| **Product** | product_id, name, description, category | `products.csv` |
| **Service** | service_id, name, description, category | `services.csv` |
| **RiskFactor** | risk_id, name, description, category, severity | `risk_factors.csv` |
| **FinancialMetric** | metric_id, company_id, metric_name, value, unit, fiscal_year | `financial_metrics.csv` |
| **Executive** | executive_id, name, title, company_id | `executives.csv` |
| **AssetManager** | manager_id, name, aum_billions, type | `asset_managers.csv` |
| **Document** | filing_id, company_id, filing_type, filing_date, fiscal_year, url | `sec_filings.csv` |

### Relationships

| Relationship | From | To | Properties | Source File |
|---|---|---|---|---|
| `OFFERS_PRODUCT` | Company | Product | - | `company_products.csv` |
| `OFFERS_SERVICE` | Company | Service | - | `company_services.csv` |
| `FACES_RISK` | Company | RiskFactor | - | `company_risk_factors.csv` |
| `HAS_METRIC` | Company | FinancialMetric | - | `financial_metrics.csv` (via company_id) |
| `HAS_EXECUTIVE` | Company | Executive | - | `executives.csv` (via company_id) |
| `OWNS` | AssetManager | Company | ownership_percentage | `asset_manager_companies.csv` |
| `FILED` | Company | Document | - | `sec_filings.csv` (via company_id) |

## Key Traversal Patterns

### 1. Company to Risk Analysis

Find all risk factors for a given company, grouped by category and severity.

```cypher
MATCH (c:Company {ticker: 'AAPL'})-[:FACES_RISK]->(r:RiskFactor)
RETURN r.name, r.category, r.severity
ORDER BY r.severity DESC
```

### 2. Cross-Company Risk Exposure

Identify risk factors shared across multiple companies.

```cypher
MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
WITH r, collect(c.ticker) AS affected_companies, count(c) AS company_count
WHERE company_count > 1
RETURN r.name, r.category, affected_companies, company_count
ORDER BY company_count DESC
```

### 3. Asset Manager Portfolio Analysis

Analyze an asset manager's portfolio holdings and total exposure.

```cypher
MATCH (am:AssetManager {name: 'The Vanguard Group'})-[o:OWNS]->(c:Company)
RETURN c.name, c.ticker, o.ownership_percentage
ORDER BY o.ownership_percentage DESC
```

### 4. Portfolio Risk Aggregation

Determine aggregate risk exposure across an asset manager's portfolio.

```cypher
MATCH (am:AssetManager)-[:OWNS]->(c:Company)-[:FACES_RISK]->(r:RiskFactor)
WITH am, r, count(DISTINCT c) AS companies_exposed
RETURN am.name, r.name, r.severity, companies_exposed
ORDER BY companies_exposed DESC
```

### 5. Filing to Entity Traversal

Starting from a SEC filing, traverse to all related entities.

```cypher
MATCH (c:Company)-[:FILED]->(d:Document {filing_type: '10-K', fiscal_year: 2024})
OPTIONAL MATCH (c)-[:OFFERS_PRODUCT]->(p:Product)
OPTIONAL MATCH (c)-[:OFFERS_SERVICE]->(s:Service)
OPTIONAL MATCH (c)-[:FACES_RISK]->(r:RiskFactor)
OPTIONAL MATCH (c)-[:HAS_METRIC]->(fm:FinancialMetric)
RETURN c.name, collect(DISTINCT p.name) AS products,
       collect(DISTINCT s.name) AS services,
       collect(DISTINCT r.name) AS risks,
       collect(DISTINCT fm.metric_name) AS metrics
```

### 6. Financial Comparison Across Companies

Compare a specific metric across all companies.

```cypher
MATCH (c:Company)-[:HAS_METRIC]->(fm:FinancialMetric {metric_name: 'Revenue', fiscal_year: 2024})
RETURN c.ticker, fm.value, fm.unit
ORDER BY fm.value DESC
```

### 7. Executive Network

Find all executives and their companies.

```cypher
MATCH (c:Company)-[:HAS_EXECUTIVE]->(e:Executive)
RETURN c.name, e.name, e.title
ORDER BY c.name, e.title
```

## Embedding Targets

For semantic search and RAG (Retrieval-Augmented Generation) use cases, the following fields are candidates for vector embeddings:

| Target | Field | Purpose |
|---|---|---|
| **RiskFactor.description** | Text description of each risk factor | Semantic search over risk factors to find similar risks across filings |
| **Product.description** | Text description of each product | Product similarity and comparison queries |
| **Service.description** | Text description of each service | Service similarity and overlap detection |
| **Chunk.text** | (Future) Chunked text extracted from 10-K filing documents | Full-text semantic search over filing content |

The primary embedding target for the workshop is **Chunk.text**, which would be created by chunking the raw 10-K filing text and storing each chunk as a node linked to its source Document. This enables semantic search queries such as:

```cypher
// Find chunks semantically similar to a query, then traverse to the filing's company
MATCH (chunk:Chunk)
WHERE chunk.embedding IS NOT NULL
WITH chunk, gds.similarity.cosine(chunk.embedding, $query_embedding) AS score
ORDER BY score DESC
LIMIT 5
MATCH (c:Company)-[:FILED]->(d:Document)-[:HAS_CHUNK]->(chunk)
RETURN c.name, d.filing_type, d.fiscal_year, chunk.text, score
```

## Entity Counts (Expected After Loading)

| Entity | Count |
|---|---|
| Company | 5 |
| Product | 15 |
| Service | 12 |
| RiskFactor | 15 |
| FinancialMetric | 20 |
| Executive | 15 |
| AssetManager | 4 |
| Document (SEC Filing) | 10 |
| **Total Nodes** | **96** |

| Relationship | Count |
|---|---|
| OFFERS_PRODUCT | 15 |
| OFFERS_SERVICE | 12 |
| FACES_RISK | 34 |
| HAS_METRIC | 20 |
| HAS_EXECUTIVE | 15 |
| OWNS | 20 |
| FILED | 10 |
| **Total Relationships** | **126** |
