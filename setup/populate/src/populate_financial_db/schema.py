"""
Neo4j schema definitions: uniqueness constraints and property indexes
for the SEC financial knowledge graph.
"""

# ── Uniqueness constraints ──────────────────────────────────────────────────

CONSTRAINTS: list[dict[str, str]] = [
    {
        "name": "company_id_unique",
        "cypher": (
            "CREATE CONSTRAINT company_id_unique IF NOT EXISTS "
            "FOR (n:Company) REQUIRE n.company_id IS UNIQUE"
        ),
    },
    {
        "name": "product_id_unique",
        "cypher": (
            "CREATE CONSTRAINT product_id_unique IF NOT EXISTS "
            "FOR (n:Product) REQUIRE n.product_id IS UNIQUE"
        ),
    },
    {
        "name": "service_id_unique",
        "cypher": (
            "CREATE CONSTRAINT service_id_unique IF NOT EXISTS "
            "FOR (n:Service) REQUIRE n.service_id IS UNIQUE"
        ),
    },
    {
        "name": "risk_id_unique",
        "cypher": (
            "CREATE CONSTRAINT risk_id_unique IF NOT EXISTS "
            "FOR (n:RiskFactor) REQUIRE n.risk_id IS UNIQUE"
        ),
    },
    {
        "name": "metric_id_unique",
        "cypher": (
            "CREATE CONSTRAINT metric_id_unique IF NOT EXISTS "
            "FOR (n:FinancialMetric) REQUIRE n.metric_id IS UNIQUE"
        ),
    },
    {
        "name": "executive_id_unique",
        "cypher": (
            "CREATE CONSTRAINT executive_id_unique IF NOT EXISTS "
            "FOR (n:Executive) REQUIRE n.executive_id IS UNIQUE"
        ),
    },
    {
        "name": "manager_id_unique",
        "cypher": (
            "CREATE CONSTRAINT manager_id_unique IF NOT EXISTS "
            "FOR (n:AssetManager) REQUIRE n.manager_id IS UNIQUE"
        ),
    },
    {
        "name": "filing_id_unique",
        "cypher": (
            "CREATE CONSTRAINT filing_id_unique IF NOT EXISTS "
            "FOR (n:Document) REQUIRE n.filing_id IS UNIQUE"
        ),
    },
]

# ── Property indexes ────────────────────────────────────────────────────────

INDEXES: list[dict[str, str]] = [
    {
        "name": "company_ticker_idx",
        "cypher": (
            "CREATE INDEX company_ticker_idx IF NOT EXISTS "
            "FOR (n:Company) ON (n.ticker)"
        ),
    },
    {
        "name": "risk_severity_idx",
        "cypher": (
            "CREATE INDEX risk_severity_idx IF NOT EXISTS "
            "FOR (n:RiskFactor) ON (n.severity)"
        ),
    },
    {
        "name": "metric_fiscal_year_idx",
        "cypher": (
            "CREATE INDEX metric_fiscal_year_idx IF NOT EXISTS "
            "FOR (n:FinancialMetric) ON (n.fiscal_year)"
        ),
    },
]
