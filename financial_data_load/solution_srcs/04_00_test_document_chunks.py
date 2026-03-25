"""
Test script for validating Document-Chunk structure in Neo4j.

Validates the two Document-Chunk structure queries from lab4-sample-queries:
1. Document chunk counts (OPTIONAL MATCH — includes documents with zero chunks)
2. Browse first chunks of a document (ordered by chunk index)

Run with: cd financial_data_load && uv run python -m solution_srcs.04_00_test_document_chunks
"""

import sys
from neo4j import GraphDatabase

from .config import Neo4jConfig


def test_document_chunk_counts(driver):
    """Validate that every Document has chunks linked via FROM_DOCUMENT.

    Runs the OPTIONAL MATCH query from lab4-sample-queries so that documents
    with zero chunks are surfaced rather than silently dropped.
    """
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
            status = "  " if r["chunks"] > 0 else "  ⚠ "
            print(f"  {status}{r['document']}: {r['chunks']} chunk(s)")

        checks = [
            ("At least one Document exists", total_docs > 0),
            ("All Documents have chunks", docs_without_chunks == 0),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_browse_first_chunks(driver):
    """Validate that chunks are ordered, have text, and link to a Document."""
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

        has_index = all(r["chunkIndex"] is not None for r in records)
        has_text = all(r["preview"] is not None and len(r["preview"]) > 0 for r in records)
        has_document = all(r["document"] is not None for r in records)

        checks = [
            ("At least one Chunk returned", len(records) > 0),
            ("All chunks have an index", has_index),
            ("All chunks have text", has_text),
            ("All chunks link to a Document", has_document),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def main():
    """Run all Document-Chunk structure tests."""
    print("=" * 60)
    print("Document-Chunk Structure Tests")
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
        results.append(("Document Chunk Counts", test_document_chunk_counts(driver)))
        results.append(("Browse First Chunks", test_browse_first_chunks(driver)))
    finally:
        driver.close()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
