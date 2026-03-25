"""
Test script that runs all sample queries from the workshop documentation.

Covers every query from sample-queries.adoc (structured graph) and
lab4-sample-queries.adoc (document-chunk, vector, fulltext).

Run with: cd financial_data_load && uv run python -m solution_srcs.04_00_test_all_sample_queries
"""

import sys
import time

from neo4j import GraphDatabase

from .config import Neo4jConfig


# ---------------------------------------------------------------------------
# Section 1: Structured Graph Queries (sample-queries.adoc)
# ---------------------------------------------------------------------------


def test_company_products(driver):
    """What products does NVIDIA offer?"""
    print("\n=== Test: Company Products (NVDA) ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company {ticker: 'NVDA'})-[:OFFERS]->(p:Product)
            RETURN p.name
            ORDER BY p.name
        """)
        records = list(result)

        print(f"  Products: {len(records)}")
        for r in records:
            print(f"    {r['p.name']}")

        checks = [
            ("At least one product returned", len(records) > 0),
            ("All products have a name", all(r["p.name"] is not None for r in records)),
        ]

        return _report(checks)


def test_shared_risk_factors(driver):
    """Which risk factors are shared across multiple companies?"""
    print("\n=== Test: Shared Risk Factors ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
            WITH r, collect(c.ticker) AS companies, count(c) AS cnt
            WHERE cnt > 1
            RETURN r.name, companies, cnt
            ORDER BY cnt DESC
            LIMIT 10
        """)
        records = list(result)

        print(f"  Shared risk factors: {len(records)}")
        for r in records:
            print(f"    {r['r.name']} ({r['cnt']} companies: {r['companies']})")

        checks = [
            ("At least one shared risk factor", len(records) > 0),
            ("All rows have cnt > 1", all(r["cnt"] > 1 for r in records)),
            ("All rows have companies list", all(len(r["companies"]) > 0 for r in records)),
        ]

        return _report(checks)


def test_portfolio_exposure(driver):
    """Which risk factors expose Berkshire Hathaway's portfolio?"""
    print("\n=== Test: Portfolio Exposure (Berkshire Hathaway) ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (am:AssetManager {name: 'Berkshire Hathaway Inc.'})-[:OWNS]->(c:Company)-[:FACES_RISK]->(r:RiskFactor)
            WITH am, r, collect(DISTINCT c.name) AS exposedCompanies, count(DISTINCT c) AS cnt
            RETURN r.name AS riskFactor, exposedCompanies, cnt
            ORDER BY cnt DESC
            LIMIT 10
        """)
        records = list(result)

        print(f"  Risk factors: {len(records)}")
        for r in records:
            print(f"    {r['riskFactor']} ({r['cnt']} companies)")

        checks = [
            ("At least one result", len(records) > 0),
            ("All rows have a riskFactor", all(r["riskFactor"] is not None for r in records)),
            ("All rows have exposedCompanies", all(len(r["exposedCompanies"]) > 0 for r in records)),
        ]

        return _report(checks)


def test_top_asset_managers(driver):
    """Who are the top asset managers by number of holdings?"""
    print("\n=== Test: Top Asset Managers ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (am:AssetManager)-[o:OWNS]->(c:Company)
            WITH am, count(c) AS holdings, sum(o.shares) AS totalShares
            RETURN am.name, holdings, totalShares
            ORDER BY holdings DESC
        """)
        records = list(result)

        print(f"  Asset managers: {len(records)}")
        for r in records[:5]:
            print(f"    {r['am.name']}: {r['holdings']} holdings, {r['totalShares']} shares")

        checks = [
            ("At least one asset manager", len(records) > 0),
            ("All have holdings > 0", all(r["holdings"] > 0 for r in records)),
            ("All have a name", all(r["am.name"] is not None for r in records)),
        ]

        return _report(checks)


def test_competitive_landscape(driver):
    """Who does NVIDIA compete with, and are any also partners?"""
    print("\n=== Test: Competitive Landscape (NVDA) ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company {ticker: 'NVDA'})-[:COMPETES_WITH]->(comp)
            RETURN comp.name,
                   EXISTS { (c)-[:PARTNERS_WITH]->(comp) } AS alsoPartner
            ORDER BY comp.name
        """)
        records = list(result)

        print(f"  Competitors: {len(records)}")
        for r in records:
            partner_flag = " (also partner)" if r["alsoPartner"] else ""
            print(f"    {r['comp.name']}{partner_flag}")

        checks = [
            ("At least one competitor", len(records) > 0),
            ("All have a name", all(r["comp.name"] is not None for r in records)),
            ("alsoPartner is boolean", all(isinstance(r["alsoPartner"], bool) for r in records)),
        ]

        return _report(checks)


def test_filed_documents(driver):
    """Which companies have filed SEC documents?"""
    print("\n=== Test: Filed Documents ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company)-[:FILED]->(d:Document)
            RETURN c.name, c.ticker, d.accessionNumber, d.filingType
            ORDER BY c.name
        """)
        records = list(result)

        print(f"  Filings: {len(records)}")
        for r in records:
            print(f"    {r['c.name']} ({r['c.ticker']}): {r['d.accessionNumber']}")

        checks = [
            ("At least one filing", len(records) > 0),
            ("All have company name", all(r["c.name"] is not None for r in records)),
            ("All have accession number", all(r["d.accessionNumber"] is not None for r in records)),
        ]

        return _report(checks)


def test_cross_entity_analysis(driver):
    """Which companies face cybersecurity risks and who owns them?"""
    print("\n=== Test: Cross-Entity Analysis (Cybersecurity) ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor), (am:AssetManager)-[:OWNS]->(c)
            WHERE r.name CONTAINS 'Cybersecurity'
            WITH c, r, collect(am.name) AS owners
            RETURN c.name, c.ticker, r.name AS risk, owners
            ORDER BY c.name
        """)
        records = list(result)

        print(f"  Companies with cybersecurity risk: {len(records)}")
        for r in records:
            print(f"    {r['c.name']}: {len(r['owners'])} owner(s)")

        checks = [
            ("At least one result", len(records) > 0),
            ("All risks contain 'Cybersecurity'", all("Cybersecurity" in r["risk"] for r in records)),
            ("All have owners list", all(len(r["owners"]) > 0 for r in records)),
        ]

        return _report(checks)


# ---------------------------------------------------------------------------
# Section 2: Document-Chunk Structure (lab4-sample-queries.adoc)
# ---------------------------------------------------------------------------


def test_document_chunk_counts(driver):
    """View all documents and their chunk counts."""
    print("\n=== Test: Document Chunk Counts ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (d:Document)
            OPTIONAL MATCH (d)<-[:FROM_DOCUMENT]-(c:Chunk)
            RETURN d.source AS document, count(c) AS chunks
            ORDER BY chunks DESC
        """)
        records = list(result)

        total_docs = len(records)
        docs_with_chunks = sum(1 for r in records if r["chunks"] > 0)
        docs_without_chunks = sum(1 for r in records if r["chunks"] == 0)

        print(f"  Documents: {total_docs}")
        print(f"  With chunks: {docs_with_chunks}")
        print(f"  Without chunks: {docs_without_chunks}")

        for r in records:
            status = "  " if r["chunks"] > 0 else "  \u26a0 "
            print(f"  {status}{r['document']}: {r['chunks']} chunk(s)")

        checks = [
            ("At least one Document exists", total_docs > 0),
            ("All Documents have chunks", docs_without_chunks == 0),
        ]

        return _report(checks)


def test_browse_first_chunks(driver):
    """Browse the first chunks of a document."""
    print("\n=== Test: Browse First Chunks ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
            WITH c, d ORDER BY c.index LIMIT 10
            RETURN c.index AS chunkIndex,
                   substring(c.text, 0, 120) AS preview,
                   d.source AS document
        """)
        records = list(result)

        print(f"  Chunks returned: {len(records)}")
        for r in records:
            print(f"    [{r['chunkIndex']}] {r['document']}: {r['preview'][:80]}...")

        checks = [
            ("At least one Chunk returned", len(records) > 0),
            ("All chunks have an index", all(r["chunkIndex"] is not None for r in records)),
            ("All chunks have text", all(r["preview"] is not None and len(r["preview"]) > 0 for r in records)),
            ("All chunks link to a Document", all(r["document"] is not None for r in records)),
        ]

        return _report(checks)


def test_walk_chunk_chain(driver):
    """Walk the NEXT_CHUNK chain."""
    print("\n=== Test: Walk Chunk Chain ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
            OPTIONAL MATCH (c)-[:NEXT_CHUNK]->(next:Chunk)
            WITH c, next, d ORDER BY c.index LIMIT 10
            RETURN c.index AS chunkIndex,
                   substring(c.text, 0, 80) AS preview,
                   next.index AS nextChunkIndex,
                   d.source AS document
        """)
        records = list(result)

        print(f"  Chunks returned: {len(records)}")
        for r in records:
            next_str = f" -> [{r['nextChunkIndex']}]" if r["nextChunkIndex"] is not None else " (end)"
            print(f"    [{r['chunkIndex']}]{next_str} {r['document']}")

        has_next = any(r["nextChunkIndex"] is not None for r in records)

        checks = [
            ("At least one Chunk returned", len(records) > 0),
            ("All chunks have an index", all(r["chunkIndex"] is not None for r in records)),
            ("At least one NEXT_CHUNK link exists", has_next),
        ]

        return _report(checks)


# ---------------------------------------------------------------------------
# Section 3: Vector Similarity Search (lab4-sample-queries.adoc)
# ---------------------------------------------------------------------------


def test_vector_similar_chunks(driver):
    """Find chunks similar to a random seed chunk."""
    print("\n=== Test: Vector Similar Chunks ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (seed:Chunk)
            WHERE seed.embedding IS NOT NULL
            WITH seed, rand() AS r ORDER BY r LIMIT 1
            CALL db.index.vector.queryNodes(
                'chunkEmbeddings', 6, seed.embedding
            ) YIELD node, score
            WHERE node <> seed
            WITH seed, node, score ORDER BY score DESC LIMIT 5
            RETURN substring(seed.text, 0, 100) AS seedText,
                   score AS similarity,
                   substring(node.text, 0, 100) AS matchText
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        if records:
            print(f"  Seed: {records[0]['seedText'][:80]}...")
        for r in records:
            print(f"    [{r['similarity']:.4f}] {r['matchText'][:80]}...")

        checks = [
            ("At least one match", len(records) > 0),
            ("All have similarity > 0", all(r["similarity"] > 0 for r in records)),
            ("All have matchText", all(r["matchText"] is not None for r in records)),
        ]

        return _report(checks)


def test_vector_search_with_document_context(driver):
    """Vector search enriched with document context."""
    print("\n=== Test: Vector Search with Document Context ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (seed:Chunk)
            WHERE seed.embedding IS NOT NULL
            WITH seed, rand() AS r ORDER BY r LIMIT 1
            CALL db.index.vector.queryNodes(
                'chunkEmbeddings', 6, seed.embedding
            ) YIELD node, score
            WHERE node <> seed
            WITH seed, node, score ORDER BY score DESC LIMIT 5
            MATCH (node)-[:FROM_DOCUMENT]->(d:Document)
            RETURN substring(seed.text, 0, 80) AS seedText,
                   score AS similarity,
                   d.source AS document,
                   substring(node.text, 0, 80) AS matchText
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        for r in records:
            print(f"    [{r['similarity']:.4f}] {r['document']}: {r['matchText'][:60]}...")

        checks = [
            ("At least one match", len(records) > 0),
            ("All have similarity > 0", all(r["similarity"] > 0 for r in records)),
            ("All have a document", all(r["document"] is not None for r in records)),
        ]

        return _report(checks)


def test_chunk_to_company(driver):
    """From a vector match, traverse to the filing company (GraphRAG)."""
    print("\n=== Test: Chunk to Company (GraphRAG) ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (seed:Chunk)
            WHERE seed.embedding IS NOT NULL
            WITH seed, rand() AS r ORDER BY r LIMIT 1
            CALL db.index.vector.queryNodes(
                'chunkEmbeddings', 6, seed.embedding
            ) YIELD node, score
            WHERE node <> seed
            WITH seed, node, score ORDER BY score DESC LIMIT 5
            MATCH (node)-[:FROM_DOCUMENT]->(d:Document)<-[:FILED]-(c:Company)
            RETURN substring(seed.text, 0, 80) AS seedText,
                   score AS similarity,
                   c.name AS company,
                   c.ticker AS ticker,
                   d.source AS document,
                   substring(node.text, 0, 80) AS matchText
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        for r in records:
            print(f"    [{r['similarity']:.4f}] {r['company']} ({r['ticker']}): {r['matchText'][:50]}...")

        checks = [
            ("At least one match", len(records) > 0),
            ("All have a company", all(r["company"] is not None for r in records)),
            ("All have a ticker", all(r["ticker"] is not None for r in records)),
        ]

        return _report(checks)


def test_chunk_to_company_risk_factors(driver):
    """Extend the GraphRAG traversal to include risk factors."""
    print("\n=== Test: Chunk to Company to Risk Factors ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (seed:Chunk)
            WHERE seed.embedding IS NOT NULL
            WITH seed, rand() AS r ORDER BY r LIMIT 1
            CALL db.index.vector.queryNodes(
                'chunkEmbeddings', 6, seed.embedding
            ) YIELD node, score
            WHERE node <> seed
            WITH seed, node, score ORDER BY score DESC LIMIT 3
            MATCH (node)-[:FROM_DOCUMENT]->(d:Document)<-[:FILED]-(c:Company)
            OPTIONAL MATCH (c)-[:FACES_RISK]->(r:RiskFactor)
            RETURN c.name AS company,
                   substring(node.text, 0, 100) AS matchText,
                   score AS similarity,
                   collect(r.name) AS riskFactors
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        for r in records:
            print(f"    {r['company']}: {len(r['riskFactors'])} risk factor(s)")

        checks = [
            ("At least one match", len(records) > 0),
            ("All have a company", all(r["company"] is not None for r in records)),
            ("riskFactors is a list", all(isinstance(r["riskFactors"], list) for r in records)),
        ]

        return _report(checks)


def test_adjacent_chunk_retrieval(driver):
    """Retrieve surrounding chunks for broader context."""
    print("\n=== Test: Adjacent Chunk Retrieval ===")

    with driver.session() as session:
        result = session.run("""
            MATCH (seed:Chunk)
            WHERE seed.embedding IS NOT NULL
            WITH seed, rand() AS r ORDER BY r LIMIT 1
            CALL db.index.vector.queryNodes(
                'chunkEmbeddings', 6, seed.embedding
            ) YIELD node, score
            WHERE node <> seed
            WITH seed, node, score ORDER BY score DESC LIMIT 3
            OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(node)
            OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
            RETURN substring(node.text, 0, 80) AS matchText,
                   score AS similarity,
                   node.index AS chunkIndex,
                   prev.index AS prevIndex,
                   next.index AS nextIndex,
                   substring(COALESCE(prev.text, '') , 0, 60) AS prevPreview,
                   substring(COALESCE(next.text, ''), 0, 60) AS nextPreview
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        for r in records:
            prev_str = f"[{r['prevIndex']}]" if r["prevIndex"] is not None else "---"
            next_str = f"[{r['nextIndex']}]" if r["nextIndex"] is not None else "---"
            print(f"    {prev_str} <- [{r['chunkIndex']}] -> {next_str}")

        has_neighbor = any(
            r["prevIndex"] is not None or r["nextIndex"] is not None
            for r in records
        )

        checks = [
            ("At least one match", len(records) > 0),
            ("All have a chunkIndex", all(r["chunkIndex"] is not None for r in records)),
            ("At least one has a neighbor", has_neighbor),
        ]

        return _report(checks)


# ---------------------------------------------------------------------------
# Section 4: Fulltext Keyword Search (lab4-sample-queries.adoc)
# ---------------------------------------------------------------------------


def setup_fulltext_index(driver):
    """Create the search_chunks fulltext index if it does not exist."""
    print("\n--- Setup: Creating fulltext index (IF NOT EXISTS) ---")

    with driver.session() as session:
        session.run("""
            CREATE FULLTEXT INDEX search_chunks IF NOT EXISTS
            FOR (c:Chunk) ON EACH [c.text]
        """)

    print("  Index created/verified. Waiting for indexing...")
    time.sleep(2)
    print("  Ready.")


def test_fulltext_keyword_search(driver):
    """Search chunks for 'cybersecurity'."""
    print("\n=== Test: Keyword Search (cybersecurity) ===")

    with driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('search_chunks', 'cybersecurity')
            YIELD node, score
            RETURN score,
                   substring(node.text, 0, 200) AS content
            ORDER BY score DESC
            LIMIT 5
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        for r in records:
            print(f"    [{r['score']:.4f}] {r['content'][:80]}...")

        checks = [
            ("At least one match", len(records) > 0),
            ("All have score > 0", all(r["score"] > 0 for r in records)),
            ("All have content", all(r["content"] is not None for r in records)),
        ]

        return _report(checks)


def test_fulltext_fuzzy_search(driver):
    """Fuzzy search catches misspellings (regulatry~)."""
    print("\n=== Test: Fuzzy Search (regulatry~) ===")

    with driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('search_chunks', 'regulatry~')
            YIELD node, score
            RETURN score,
                   substring(node.text, 0, 200) AS content
            ORDER BY score DESC
            LIMIT 5
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        for r in records:
            print(f"    [{r['score']:.4f}] {r['content'][:80]}...")

        checks = [
            ("At least one match (fuzzy worked)", len(records) > 0),
            ("All have score > 0", all(r["score"] > 0 for r in records)),
        ]

        return _report(checks)


def test_fulltext_boolean_search(driver):
    """Boolean keyword search: supply AND chain AND disruption."""
    print("\n=== Test: Boolean Search (supply AND chain AND disruption) ===")

    with driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('search_chunks', 'supply AND chain AND disruption')
            YIELD node, score
            RETURN score,
                   substring(node.text, 0, 200) AS content
            ORDER BY score DESC
            LIMIT 5
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        for r in records:
            print(f"    [{r['score']:.4f}] {r['content'][:80]}...")

        checks = [
            ("At least one match", len(records) > 0),
            ("All have score > 0", all(r["score"] > 0 for r in records)),
        ]

        return _report(checks)


def test_fulltext_entity_names(driver):
    """Search entity names for 'NVIDIA'."""
    print("\n=== Test: Entity Name Search (NVIDIA) ===")

    with driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('search_entities', 'NVIDIA')
            YIELD node, score
            RETURN labels(node)[0] AS type, node.name AS name, score
            ORDER BY score DESC
            LIMIT 10
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        for r in records:
            print(f"    [{r['score']:.4f}] {r['type']}: {r['name']}")

        has_company = any(r["type"] == "Company" for r in records)

        checks = [
            ("At least one match", len(records) > 0),
            ("All have a name", all(r["name"] is not None for r in records)),
            ("At least one Company result", has_company),
        ]

        return _report(checks)


def test_fulltext_entity_enrichment(driver):
    """Fulltext search for 'artificial intelligence' with entity traversal."""
    print("\n=== Test: Fulltext with Entity Enrichment ===")

    with driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('search_chunks', 'artificial intelligence')
            YIELD node, score
            WITH node, score ORDER BY score DESC LIMIT 5
            MATCH (node)-[:FROM_DOCUMENT]->(d:Document)<-[:FILED]-(c:Company)
            OPTIONAL MATCH (c)-[:OFFERS]->(p:Product)
            RETURN c.name AS company,
                   score AS relevance,
                   collect(DISTINCT p.name) AS products,
                   substring(node.text, 0, 120) AS excerpt
        """)
        records = list(result)

        print(f"  Matches: {len(records)}")
        for r in records:
            print(f"    {r['company']}: {len(r['products'])} product(s)")

        checks = [
            ("At least one match", len(records) > 0),
            ("All have a company", all(r["company"] is not None for r in records)),
            ("products is a list", all(isinstance(r["products"], list) for r in records)),
        ]

        return _report(checks)


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
    """Run all sample query tests."""
    print("=" * 60)
    print("Sample Query Tests - Structured, Vector, and Fulltext")
    print("=" * 60)

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
        # --- Section 1: Structured Graph Queries ---
        print("\n" + "-" * 60)
        print("SECTION 1: Structured Graph Queries")
        print("-" * 60)
        results.append(("Company Products (NVDA)", test_company_products(driver)))
        results.append(("Shared Risk Factors", test_shared_risk_factors(driver)))
        results.append(("Portfolio Exposure (Berkshire Hathaway)", test_portfolio_exposure(driver)))
        results.append(("Top Asset Managers", test_top_asset_managers(driver)))
        results.append(("Competitive Landscape (NVDA)", test_competitive_landscape(driver)))
        results.append(("Filed Documents", test_filed_documents(driver)))
        results.append(("Cross-Entity Analysis (Cybersecurity)", test_cross_entity_analysis(driver)))

        # --- Section 2: Document-Chunk Structure ---
        print("\n" + "-" * 60)
        print("SECTION 2: Document-Chunk Structure")
        print("-" * 60)
        results.append(("Document Chunk Counts", test_document_chunk_counts(driver)))
        results.append(("Browse First Chunks", test_browse_first_chunks(driver)))
        results.append(("Walk Chunk Chain", test_walk_chunk_chain(driver)))

        # --- Section 3: Vector Similarity Search ---
        print("\n" + "-" * 60)
        print("SECTION 3: Vector Similarity Search")
        print("-" * 60)
        results.append(("Vector Similar Chunks", test_vector_similar_chunks(driver)))
        results.append(("Vector Search with Document Context", test_vector_search_with_document_context(driver)))
        results.append(("Chunk to Company (GraphRAG)", test_chunk_to_company(driver)))
        results.append(("Chunk to Company to Risk Factors", test_chunk_to_company_risk_factors(driver)))
        results.append(("Adjacent Chunk Retrieval", test_adjacent_chunk_retrieval(driver)))

        # --- Section 4: Fulltext Keyword Search ---
        print("\n" + "-" * 60)
        print("SECTION 4: Fulltext Keyword Search")
        print("-" * 60)
        setup_fulltext_index(driver)
        results.append(("Keyword Search (cybersecurity)", test_fulltext_keyword_search(driver)))
        results.append(("Fuzzy Search (regulatry~)", test_fulltext_fuzzy_search(driver)))
        results.append(("Boolean Search (supply AND chain AND disruption)", test_fulltext_boolean_search(driver)))
        results.append(("Entity Name Search (NVIDIA)", test_fulltext_entity_names(driver)))
        results.append(("Fulltext with Entity Enrichment", test_fulltext_entity_enrichment(driver)))

    finally:
        driver.close()

    # --- Summary ---
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    sections = [
        ("Structured Graph Queries", 0, 7),
        ("Document-Chunk Structure", 7, 10),
        ("Vector Similarity Search", 10, 15),
        ("Fulltext Keyword Search", 15, 20),
    ]

    for section_name, start, end in sections:
        section_results = results[start:end]
        if not section_results:
            continue
        print(f"\n  {section_name}:")
        for name, result in section_results:
            status = "PASS" if result else "FAIL"
            print(f"    {status}: {name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n  Total: {passed}/{total} passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
