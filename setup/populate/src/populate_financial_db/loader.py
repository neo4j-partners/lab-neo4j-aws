"""
Core data loading pipeline for the SEC financial knowledge graph.

Reads CSV files from TransformedData/ and loads nodes and relationships
into Neo4j using MERGE to ensure idempotent loads.
"""

from __future__ import annotations

import csv
from pathlib import Path

from neo4j import Driver

from .formatting import header, val

# ── CSV helpers ─────────────────────────────────────────────────────────────


def read_csv(filepath: Path) -> list[dict[str, str]]:
    """Read a CSV file with utf-8/latin-1 fallback and return rows as dicts."""
    for encoding in ("utf-8", "latin-1"):
        try:
            with open(filepath, newline="", encoding=encoding) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode {filepath} with utf-8 or latin-1")


# ── Node loading ────────────────────────────────────────────────────────────

_NODE_SPECS: list[dict] = [
    {
        "label": "Company",
        "file": "companies.csv",
        "id_field": "company_id",
        "cypher": (
            "UNWIND $rows AS row "
            "MERGE (n:Company {company_id: row.company_id}) "
            "SET n.name = row.name, "
            "    n.ticker = row.ticker, "
            "    n.sector = row.sector, "
            "    n.cik = row.cik, "
            "    n.fiscal_year_end = row.fiscal_year_end"
        ),
    },
    {
        "label": "Product",
        "file": "products.csv",
        "id_field": "product_id",
        "cypher": (
            "UNWIND $rows AS row "
            "MERGE (n:Product {product_id: row.product_id}) "
            "SET n.name = row.name, "
            "    n.description = row.description, "
            "    n.category = row.category"
        ),
    },
    {
        "label": "Service",
        "file": "services.csv",
        "id_field": "service_id",
        "cypher": (
            "UNWIND $rows AS row "
            "MERGE (n:Service {service_id: row.service_id}) "
            "SET n.name = row.name, "
            "    n.description = row.description, "
            "    n.category = row.category"
        ),
    },
    {
        "label": "RiskFactor",
        "file": "risk_factors.csv",
        "id_field": "risk_id",
        "cypher": (
            "UNWIND $rows AS row "
            "MERGE (n:RiskFactor {risk_id: row.risk_id}) "
            "SET n.name = row.name, "
            "    n.description = row.description, "
            "    n.category = row.category, "
            "    n.severity = row.severity"
        ),
    },
    {
        "label": "FinancialMetric",
        "file": "financial_metrics.csv",
        "id_field": "metric_id",
        "cypher": (
            "UNWIND $rows AS row "
            "MERGE (n:FinancialMetric {metric_id: row.metric_id}) "
            "SET n.company_id = row.company_id, "
            "    n.metric_name = row.metric_name, "
            "    n.value = row.value, "
            "    n.unit = row.unit, "
            "    n.fiscal_year = row.fiscal_year"
        ),
    },
    {
        "label": "Executive",
        "file": "executives.csv",
        "id_field": "executive_id",
        "cypher": (
            "UNWIND $rows AS row "
            "MERGE (n:Executive {executive_id: row.executive_id}) "
            "SET n.name = row.name, "
            "    n.title = row.title, "
            "    n.company_id = row.company_id"
        ),
    },
    {
        "label": "AssetManager",
        "file": "asset_managers.csv",
        "id_field": "manager_id",
        "cypher": (
            "UNWIND $rows AS row "
            "MERGE (n:AssetManager {manager_id: row.manager_id}) "
            "SET n.name = row.name, "
            "    n.aum_billions = toFloat(row.aum_billions), "
            "    n.type = row.type"
        ),
    },
    {
        "label": "Document",
        "file": "sec_filings.csv",
        "id_field": "filing_id",
        "cypher": (
            "UNWIND $rows AS row "
            "MERGE (n:Document {filing_id: row.filing_id}) "
            "SET n.company_id = row.company_id, "
            "    n.filing_type = row.filing_type, "
            "    n.filing_date = row.filing_date, "
            "    n.fiscal_year = row.fiscal_year, "
            "    n.url = row.url"
        ),
    },
]


def load_nodes(driver: Driver, data_dir: Path) -> None:
    """Load all node types from CSV files into Neo4j."""
    header("Loading nodes")
    for spec in _NODE_SPECS:
        filepath = data_dir / spec["file"]
        if not filepath.exists():
            val(spec["label"], f"SKIPPED (file not found: {filepath.name})")
            continue
        rows = read_csv(filepath)
        with driver.session() as session:
            session.run(spec["cypher"], rows=rows)
        val(spec["label"], f"{len(rows)} rows loaded")


# ── Relationship loading ────────────────────────────────────────────────────

_REL_SPECS: list[dict] = [
    {
        "type": "OFFERS_PRODUCT",
        "file": "company_products.csv",
        "cypher": (
            "UNWIND $rows AS row "
            "MATCH (c:Company {company_id: row.company_id}) "
            "MATCH (p:Product {product_id: row.product_id}) "
            "MERGE (c)-[:OFFERS_PRODUCT]->(p)"
        ),
    },
    {
        "type": "OFFERS_SERVICE",
        "file": "company_services.csv",
        "cypher": (
            "UNWIND $rows AS row "
            "MATCH (c:Company {company_id: row.company_id}) "
            "MATCH (s:Service {service_id: row.service_id}) "
            "MERGE (c)-[:OFFERS_SERVICE]->(s)"
        ),
    },
    {
        "type": "FACES_RISK",
        "file": "company_risk_factors.csv",
        "cypher": (
            "UNWIND $rows AS row "
            "MATCH (c:Company {company_id: row.company_id}) "
            "MATCH (r:RiskFactor {risk_id: row.risk_id}) "
            "MERGE (c)-[:FACES_RISK]->(r)"
        ),
    },
    {
        "type": "HAS_METRIC",
        "file": "financial_metrics.csv",
        "cypher": (
            "UNWIND $rows AS row "
            "MATCH (c:Company {company_id: row.company_id}) "
            "MATCH (m:FinancialMetric {metric_id: row.metric_id}) "
            "MERGE (c)-[:HAS_METRIC]->(m)"
        ),
    },
    {
        "type": "HAS_EXECUTIVE",
        "file": "executives.csv",
        "cypher": (
            "UNWIND $rows AS row "
            "MATCH (c:Company {company_id: row.company_id}) "
            "MATCH (e:Executive {executive_id: row.executive_id}) "
            "MERGE (c)-[:HAS_EXECUTIVE]->(e)"
        ),
    },
    {
        "type": "OWNS",
        "file": "asset_manager_companies.csv",
        "cypher": (
            "UNWIND $rows AS row "
            "MATCH (a:AssetManager {manager_id: row.manager_id}) "
            "MATCH (c:Company {company_id: row.company_id}) "
            "MERGE (a)-[r:OWNS]->(c) "
            "SET r.ownership_percentage = toFloat(row.ownership_percentage)"
        ),
    },
    {
        "type": "FILED",
        "file": "sec_filings.csv",
        "cypher": (
            "UNWIND $rows AS row "
            "MATCH (c:Company {company_id: row.company_id}) "
            "MATCH (d:Document {filing_id: row.filing_id}) "
            "MERGE (c)-[:FILED]->(d)"
        ),
    },
]


def load_relationships(driver: Driver, data_dir: Path) -> None:
    """Load all relationship types from junction CSVs into Neo4j."""
    header("Loading relationships")
    for spec in _REL_SPECS:
        filepath = data_dir / spec["file"]
        if not filepath.exists():
            val(spec["type"], f"SKIPPED (file not found: {filepath.name})")
            continue
        rows = read_csv(filepath)
        with driver.session() as session:
            session.run(spec["cypher"], rows=rows)
        val(spec["type"], f"{len(rows)} rows processed")


# ── Verification ────────────────────────────────────────────────────────────


def verify(driver: Driver) -> None:
    """Print node and relationship counts by type."""
    header("Node counts")
    with driver.session() as session:
        result = session.run(
            "MATCH (n) "
            "WITH labels(n) AS lbls, count(n) AS cnt "
            "UNWIND lbls AS label "
            "RETURN label, sum(cnt) AS count "
            "ORDER BY count DESC"
        )
        for record in result:
            val(record["label"], record["count"])

    header("Relationship counts")
    with driver.session() as session:
        result = session.run(
            "MATCH ()-[r]->() "
            "RETURN type(r) AS type, count(r) AS count "
            "ORDER BY count DESC"
        )
        for record in result:
            val(record["type"], record["count"])


# ── Cleanup ─────────────────────────────────────────────────────────────────

_BATCH_SIZE = 10_000


def clear_database(driver: Driver) -> int:
    """Delete all nodes in batches to avoid transaction-size limits.

    Returns the total number of deleted nodes.
    """
    header("Clearing database")
    total = 0
    while True:
        with driver.session() as session:
            result = session.run(
                "MATCH (n) "
                "WITH n LIMIT $batch "
                "DETACH DELETE n "
                "RETURN count(*) AS deleted",
                batch=_BATCH_SIZE,
            )
            deleted = result.single()["deleted"]
            total += deleted
            if deleted == 0:
                break
    val("Nodes deleted", total)
    return total
