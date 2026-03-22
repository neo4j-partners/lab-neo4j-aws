"""
Typer CLI for loading the SEC financial knowledge graph into Neo4j.

Commands:
    load     Full pipeline (constraints -> indexes -> nodes -> relationships -> verify)
    verify   Print node/relationship counts
    clean    Delete all nodes
    samples  Run sample Cypher queries against the loaded graph
"""

from __future__ import annotations

import typer
from neo4j import GraphDatabase

from .config import Settings
from .formatting import banner, header, val, table
from .loader import load_nodes, load_relationships, verify as run_verify, clear_database
from .schema import CONSTRAINTS, INDEXES

app = typer.Typer(help="Populate Neo4j with SEC financial knowledge graph data.")


def _get_driver(settings: Settings):
    """Create and return a Neo4j driver."""
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )


# ── Commands ────────────────────────────────────────────────────────────────


@app.command()
def load() -> None:
    """Full pipeline: constraints, indexes, nodes, relationships, verify."""
    settings = Settings()
    driver = _get_driver(settings)
    data_dir = settings.resolved_data_dir

    try:
        driver.verify_connectivity()
        banner("Loading SEC Financial Knowledge Graph")
        val("Neo4j URI", settings.neo4j_uri)
        val("Data directory", str(data_dir))

        # 1. Constraints
        header("Creating constraints")
        with driver.session() as session:
            for c in CONSTRAINTS:
                session.run(c["cypher"])
                val("Constraint", c["name"])

        # 2. Indexes
        header("Creating indexes")
        with driver.session() as session:
            for idx in INDEXES:
                session.run(idx["cypher"])
                val("Index", idx["name"])

        # 3. Nodes
        load_nodes(driver, data_dir)

        # 4. Relationships
        load_relationships(driver, data_dir)

        # 5. Verify
        run_verify(driver)

        banner("Load complete")
    finally:
        driver.close()


@app.command()
def verify() -> None:
    """Print node and relationship counts."""
    settings = Settings()
    driver = _get_driver(settings)
    try:
        driver.verify_connectivity()
        banner("Knowledge Graph Summary")
        run_verify(driver)
    finally:
        driver.close()


@app.command()
def clean() -> None:
    """Delete all nodes and relationships."""
    settings = Settings()
    driver = _get_driver(settings)
    try:
        driver.verify_connectivity()
        banner("Cleaning Database")
        total = clear_database(driver)
        val("Total deleted", total)
    finally:
        driver.close()


@app.command()
def samples() -> None:
    """Run sample Cypher queries against the loaded graph."""
    settings = Settings()
    driver = _get_driver(settings)

    queries = [
        (
            "Company Overview",
            "MATCH (c:Company) "
            "RETURN c.name AS company, c.ticker AS ticker, c.sector AS sector "
            "ORDER BY c.name LIMIT 10",
            ["company", "ticker", "sector"],
        ),
        (
            "Risk Analysis",
            "MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor) "
            "RETURN c.name AS company, r.name AS risk, r.severity AS severity "
            "ORDER BY r.severity DESC, c.name LIMIT 10",
            ["company", "risk", "severity"],
        ),
        (
            "Portfolio Overlap",
            "MATCH (a:AssetManager)-[:OWNS]->(c:Company) "
            "WITH a, collect(c.name) AS companies "
            "RETURN a.name AS manager, size(companies) AS holdings, "
            "       companies[0..5] AS sample_companies "
            "ORDER BY holdings DESC LIMIT 10",
            ["manager", "holdings", "sample_companies"],
        ),
        (
            "Filing Summary",
            "MATCH (c:Company)-[:FILED]->(d:Document) "
            "RETURN c.name AS company, d.filing_type AS type, "
            "       d.filing_date AS date, d.fiscal_year AS year "
            "ORDER BY d.filing_date DESC LIMIT 10",
            ["company", "type", "date", "year"],
        ),
        (
            "Executive Listing",
            "MATCH (c:Company)-[:HAS_EXECUTIVE]->(e:Executive) "
            "RETURN c.name AS company, e.name AS executive, e.title AS title "
            "ORDER BY c.name, e.title LIMIT 10",
            ["company", "executive", "title"],
        ),
    ]

    try:
        driver.verify_connectivity()
        banner("Sample Queries")

        with driver.session() as session:
            for title, cypher, columns in queries:
                result = session.run(cypher)
                rows = [[record[c] for c in columns] for record in result]
                if rows:
                    table(title, columns, rows)
                else:
                    header(title)
                    val("Result", "(no data)")
    finally:
        driver.close()


if __name__ == "__main__":
    app()
