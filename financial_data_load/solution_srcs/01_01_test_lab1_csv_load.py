"""
Test script for validating the Lab 1 CSV data load into Neo4j.

Validates the graph produced by the Cypher statements in lab1-load.adoc:
1. Constraints created (Step 1)
2. Node counts match expected values (Step 5)
3. Relationships exist with correct patterns (Step 3)
4. Fulltext index exists (Step 4)
5. Sample queries return expected results (Sample Queries)

Run with:
  cd financial_data_load && uv run python -m solution_srcs.01_01_test_lab1_csv_load

Test against the gold environment:
  cd financial_data_load && ENV_FILE=.env.gold uv run python -m solution_srcs.01_01_test_lab1_csv_load
"""

import sys

from neo4j import GraphDatabase

from .config import Neo4jConfig


# Expected node counts from lab1-load.adoc Step 5.
# Company is approximate (~71) because MERGE in competitor/partner loads
# creates new Company nodes for names not in companies.csv.
EXPECTED_COUNTS = {
    "AssetManager": 15,
    "Company": 71,  # approximate lower bound
    "Document": 7,
    "FinancialMetric": 874,
    "Product": 303,
    "RiskFactor": 883,
}

# Constraints from lab1-load.adoc Step 1.
EXPECTED_CONSTRAINTS = [
    ("companyId", "Company", "companyId"),
    ("companyName", "Company", "name"),
    ("productId", "Product", "productId"),
    ("riskId", "RiskFactor", "riskId"),
    ("managerId", "AssetManager", "managerId"),
    ("documentId", "Document", "documentId"),
    ("metricId", "FinancialMetric", "metricId"),
]

# Relationship patterns from lab1-load.adoc Step 3.
EXPECTED_RELATIONSHIPS = [
    ("Company", "OFFERS", "Product"),
    ("Company", "FACES_RISK", "RiskFactor"),
    ("AssetManager", "OWNS", "Company"),
    ("Company", "COMPETES_WITH", "Company"),
    ("Company", "PARTNERS_WITH", "Company"),
    ("Company", "FILED", "Document"),
    ("Company", "REPORTS", "FinancialMetric"),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_constraints(driver):
    """Validate that all Lab 1 constraints exist."""
    print("\n=== Test: Constraints (Step 1) ===")

    with driver.session() as session:
        result = session.run("SHOW CONSTRAINTS")
        constraints = {
            record["name"]: {
                "label": record["labelsOrTypes"][0] if record["labelsOrTypes"] else None,
                "property": record["properties"][0] if record["properties"] else None,
            }
            for record in result
        }

    print(f"  Found {len(constraints)} constraint(s):")
    for name, info in sorted(constraints.items()):
        print(f"    {name}: {info['label']}.{info['property']}")

    checks = []
    for name, label, prop in EXPECTED_CONSTRAINTS:
        found = name in constraints
        if found:
            match = constraints[name]["label"] == label and constraints[name]["property"] == prop
            checks.append((f"Constraint '{name}' on {label}.{prop}", match))
        else:
            checks.append((f"Constraint '{name}' exists", False))

    return _report(checks)


def test_node_counts(driver):
    """Validate node counts match lab1-load.adoc Step 5."""
    print("\n=== Test: Node Counts (Step 5) ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            WITH labels(n)[0] AS label, count(n) AS count
            RETURN label, count ORDER BY label
        """)
        counts = {record["label"]: record["count"] for record in result}

    print("  Actual counts:")
    for label in sorted(EXPECTED_COUNTS):
        actual = counts.get(label, 0)
        expected = EXPECTED_COUNTS[label]
        marker = " OK" if actual >= expected else " LOW"
        print(f"    {label}: {actual} (expected >= {expected}){marker}")

    # Report any extra labels
    extra = set(counts) - set(EXPECTED_COUNTS)
    if extra:
        print(f"  Extra labels: {sorted(extra)}")

    checks = []
    for label, expected in EXPECTED_COUNTS.items():
        actual = counts.get(label, 0)
        if label == "Company":
            # Company count is approximate due to MERGE creating extra nodes
            checks.append((f"{label} >= {expected}", actual >= expected))
        else:
            checks.append((f"{label} == {expected}", actual == expected))

    return _report(checks)


def test_relationships(driver):
    """Validate relationship types and patterns from Step 3."""
    print("\n=== Test: Relationships (Step 3) ===")

    with driver.session() as session:
        # Get relationship type counts
        result = session.run("""
            MATCH ()-[r]->()
            WITH type(r) AS type, count(r) AS count
            RETURN type, count ORDER BY type
        """)
        rel_counts = {record["type"]: record["count"] for record in result}

    print("  Relationship counts:")
    for rel_type, count in sorted(rel_counts.items()):
        print(f"    {rel_type}: {count}")

    checks = []
    for start, rel_type, end in EXPECTED_RELATIONSHIPS:
        count = rel_counts.get(rel_type, 0)
        checks.append((f"{start}-[{rel_type}]->{end} exists ({count})", count > 0))

    # Verify OWNS has shares property
    with driver.session() as session:
        result = session.run("""
            MATCH (:AssetManager)-[r:OWNS]->(:Company)
            WHERE r.shares IS NOT NULL
            RETURN count(r) AS count
        """)
        owns_with_shares = result.single()["count"]
        total_owns = rel_counts.get("OWNS", 0)
        checks.append((f"OWNS relationships have 'shares' ({owns_with_shares}/{total_owns})",
                        owns_with_shares == total_owns and total_owns > 0))

    return _report(checks)


def test_fulltext_index(driver):
    """Validate the search_entities fulltext index from Step 4."""
    print("\n=== Test: Fulltext Index (Step 4) ===")

    with driver.session() as session:
        result = session.run("SHOW FULLTEXT INDEXES")
        indexes = {
            record["name"]: {
                "labels": record.get("labelsOrTypes", []),
                "properties": record.get("properties", []),
                "state": record.get("state", "unknown"),
            }
            for record in result
        }

    print(f"  Found {len(indexes)} fulltext index(es):")
    for name, info in sorted(indexes.items()):
        print(f"    {name}: {info['labels']} on {info['properties']} [{info['state']}]")

    checks = [
        ("search_entities index exists", "search_entities" in indexes),
    ]
    if "search_entities" in indexes:
        idx = indexes["search_entities"]
        checks.append(("Covers Company|Product|RiskFactor",
                        set(idx["labels"]) == {"Company", "Product", "RiskFactor"}))
        checks.append(("Indexes name and description",
                        set(idx["properties"]) == {"name", "description"}))
        checks.append(("Index is ONLINE", idx["state"] == "ONLINE"))

    return _report(checks)


# ---------------------------------------------------------------------------
# Sample Query Tests (from lab1-load.adoc)
# ---------------------------------------------------------------------------


def test_query_nvidia_products(driver):
    """What products does NVIDIA offer?"""
    print("\n=== Sample Query: NVIDIA Products ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company {ticker: 'NVDA'})-[:OFFERS]->(p:Product)
            RETURN p.name ORDER BY p.name LIMIT 10
        """)
        products = [r["p.name"] for r in result]

    print(f"  Products: {len(products)}")
    for p in products:
        print(f"    {p}")

    return _report([
        ("Returns at least one product", len(products) > 0),
    ])


def test_query_shared_risks(driver):
    """Which risk factors are shared across multiple companies?"""
    print("\n=== Sample Query: Shared Risk Factors ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
            WITH r, collect(c.ticker) AS companies, count(c) AS cnt
            WHERE cnt > 1
            RETURN r.name, companies, cnt
            ORDER BY cnt DESC LIMIT 5
        """)
        records = list(result)

    print(f"  Shared risks: {len(records)}")
    for r in records:
        print(f"    {r['r.name']} ({r['cnt']} companies)")

    return _report([
        ("Returns at least one shared risk", len(records) > 0),
        ("All have cnt > 1", all(r["cnt"] > 1 for r in records)),
    ])


def test_query_top_asset_managers(driver):
    """Who are the top asset managers by number of holdings?"""
    print("\n=== Sample Query: Top Asset Managers ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (am:AssetManager)-[o:OWNS]->(c:Company)
            WITH am, count(c) AS holdings, sum(o.shares) AS total_shares
            RETURN am.name, holdings, total_shares
            ORDER BY holdings DESC LIMIT 5
        """)
        records = list(result)

    print(f"  Asset managers: {len(records)}")
    for r in records:
        print(f"    {r['am.name']}: {r['holdings']} holdings, {r['total_shares']} shares")

    return _report([
        ("Returns at least one manager", len(records) > 0),
        ("All have holdings > 0", all(r["holdings"] > 0 for r in records)),
    ])


def test_query_msft_competitors(driver):
    """Who does Microsoft compete with?"""
    print("\n=== Sample Query: Microsoft Competitors ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company {ticker: 'MSFT'})-[:COMPETES_WITH]->(comp)
            RETURN comp.name ORDER BY comp.name
        """)
        competitors = [r["comp.name"] for r in result]

    print(f"  Competitors: {len(competitors)}")
    for c in competitors:
        print(f"    {c}")

    return _report([
        ("Returns at least one competitor", len(competitors) > 0),
    ])


def test_query_portfolio_risk_exposure(driver):
    """Which risk factors expose a portfolio across multiple companies?"""
    print("\n=== Sample Query: Portfolio Risk Exposure ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (am:AssetManager)-[:OWNS]->(c:Company)-[:FACES_RISK]->(r:RiskFactor)
            WITH am, r, count(DISTINCT c) AS exposed
            WHERE exposed > 1
            RETURN am.name, r.name, exposed
            ORDER BY exposed DESC, am.name LIMIT 5
        """)
        records = list(result)

    print(f"  Exposures: {len(records)}")
    for r in records:
        print(f"    {r['am.name']}: {r['r.name']} ({r['exposed']} companies)")

    return _report([
        ("Returns at least one result", len(records) > 0),
        ("All have exposed > 1", all(r["exposed"] > 1 for r in records)),
    ])


def test_query_fulltext_search(driver):
    """Fulltext search for 'artificial intelligence'."""
    print("\n=== Sample Query: Fulltext Entity Search ===")

    with driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('search_entities', 'artificial intelligence')
            YIELD node, score
            RETURN labels(node)[0] AS label, node.name AS name, score
            ORDER BY score DESC LIMIT 10
        """)
        records = list(result)

    print(f"  Matches: {len(records)}")
    for r in records:
        print(f"    [{r['score']:.4f}] {r['label']}: {r['name']}")

    return _report([
        ("Returns at least one match", len(records) > 0),
        ("All have score > 0", all(r["score"] > 0 for r in records)),
    ])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _report(checks):
    """Print check results and return True if all passed."""
    passed = 0
    for name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")
        if result:
            passed += 1

    print(f"\n  Result: {passed}/{len(checks)} checks passed")
    return passed == len(checks)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    """Run all Lab 1 load validation tests."""
    print("=" * 60)
    print("Lab 1 CSV Load Validation")
    print("=" * 60)
    print("\nValidates the graph produced by lab1-load.adoc Cypher statements.")

    config = Neo4jConfig()
    driver = GraphDatabase.driver(config.uri, auth=(config.username, config.password))

    try:
        driver.verify_connectivity()
        print(f"\nConnected to Neo4j: {config.uri}")
    except Exception as e:
        print(f"\nFailed to connect to Neo4j: {e}")
        sys.exit(1)

    results = []

    try:
        # --- Load Validation ---
        print("\n" + "-" * 60)
        print("PART 1: Load Validation (Steps 1-5)")
        print("-" * 60)
        results.append(("Constraints", test_constraints(driver)))
        results.append(("Node Counts", test_node_counts(driver)))
        results.append(("Relationships", test_relationships(driver)))
        results.append(("Fulltext Index", test_fulltext_index(driver)))

        # --- Sample Queries ---
        print("\n" + "-" * 60)
        print("PART 2: Sample Queries")
        print("-" * 60)
        results.append(("NVIDIA Products", test_query_nvidia_products(driver)))
        results.append(("Shared Risk Factors", test_query_shared_risks(driver)))
        results.append(("Top Asset Managers", test_query_top_asset_managers(driver)))
        results.append(("Microsoft Competitors", test_query_msft_competitors(driver)))
        results.append(("Portfolio Risk Exposure", test_query_portfolio_risk_exposure(driver)))
        results.append(("Fulltext Entity Search", test_query_fulltext_search(driver)))

    finally:
        driver.close()

    # --- Summary ---
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    print("\n  Load Validation:")
    for name, result in results[:4]:
        status = "PASS" if result else "FAIL"
        print(f"    {status}: {name}")

    print("\n  Sample Queries:")
    for name, result in results[4:]:
        status = "PASS" if result else "FAIL"
        print(f"    {status}: {name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n  Total: {passed}/{total} passed")

    if passed == total:
        print("\nLab 1 data load is valid.")
        sys.exit(0)
    else:
        print("\nSome tests failed. Check output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
