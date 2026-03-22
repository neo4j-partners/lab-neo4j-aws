"""
Data loading and index creation for GraphRAG validation.

Functions for loading CSV data into Document/Chunk nodes,
generating Titan V2 embeddings, and creating vector + fulltext indexes.
"""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path

import nest_asyncio
from neo4j import Driver
from neo4j_graphrag.embeddings import BedrockEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)
from neo4j_graphrag.indexes import create_vector_index, create_fulltext_index

from .config import Settings

# ── CSV helpers ─────────────────────────────────────────────────────────────


def load_csv(filepath: Path) -> list[dict[str, str]]:
    """Read a CSV file with utf-8/latin-1 fallback."""
    for encoding in ("utf-8", "latin-1"):
        try:
            with open(filepath, newline="", encoding=encoding) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode {filepath}")


# ── Text splitting ──────────────────────────────────────────────────────────


def split_text(
    text: str, chunk_size: int = 500, chunk_overlap: int = 50
) -> list[str]:
    """Split text into chunks using FixedSizeSplitter.

    Handles both running-event-loop (Jupyter) and standalone Python contexts.
    """
    splitter = FixedSizeSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, approximate=True
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        nest_asyncio.apply()
        result = asyncio.run(splitter.run(text))
    else:
        result = asyncio.run(splitter.run(text))

    return [chunk.text for chunk in result.chunks]


# ── Document / Chunk creation ───────────────────────────────────────────────


def create_documents_and_chunks(driver: Driver, data_dir: Path) -> int:
    """Create Document and Chunk nodes from sec_filings.csv text data.

    For each filing document the filing metadata is stored on the Document
    node and dummy body text (from the filing description) is chunked and
    linked via FROM_DOCUMENT and NEXT_CHUNK relationships.

    Returns the number of Chunk nodes created.
    """
    filings_path = data_dir / "sec_filings.csv"
    if not filings_path.exists():
        raise FileNotFoundError(f"sec_filings.csv not found in {data_dir}")

    rows = load_csv(filings_path)
    total_chunks = 0

    with driver.session() as session:
        for row in rows:
            filing_id = row["filing_id"]
            company_id = row.get("company_id", "")

            # Build a descriptive text block from available fields
            text_parts = [
                f"SEC Filing {row.get('filing_type', '10-K')} for company {company_id}.",
                f"Filed on {row.get('filing_date', 'N/A')} for fiscal year {row.get('fiscal_year', 'N/A')}.",
            ]
            if row.get("url"):
                text_parts.append(f"Source: {row['url']}")
            body = " ".join(text_parts)

            chunks = split_text(body, chunk_size=500, chunk_overlap=50)

            # Ensure Document node exists (may already exist from populate)
            session.run(
                "MERGE (d:Document {filing_id: $filing_id})",
                filing_id=filing_id,
            )

            for idx, chunk_text in enumerate(chunks):
                session.run(
                    "MATCH (d:Document {filing_id: $filing_id}) "
                    "CREATE (c:Chunk {text: $text, index: $index}) "
                    "CREATE (c)-[:FROM_DOCUMENT]->(d)",
                    filing_id=filing_id,
                    text=chunk_text,
                    index=idx,
                )
                total_chunks += 1

            # Link sequential chunks with NEXT_CHUNK
            if len(chunks) > 1:
                session.run(
                    "MATCH (d:Document {filing_id: $filing_id})<-[:FROM_DOCUMENT]-(c:Chunk) "
                    "WITH c ORDER BY c.index "
                    "WITH collect(c) AS ordered "
                    "UNWIND range(0, size(ordered)-2) AS i "
                    "WITH ordered[i] AS c1, ordered[i+1] AS c2 "
                    "CREATE (c1)-[:NEXT_CHUNK]->(c2)",
                    filing_id=filing_id,
                )

    return total_chunks


# ── Embeddings ──────────────────────────────────────────────────────────────


def generate_embeddings(driver: Driver, embedder: BedrockEmbeddings) -> int:
    """Generate Titan V2 embeddings for all Chunk nodes without an embedding.

    Returns the number of chunks updated.
    """
    updated = 0
    with driver.session() as session:
        result = session.run(
            "MATCH (c:Chunk) WHERE c.embedding IS NULL RETURN elementId(c) AS id, c.text AS text"
        )
        records = list(result)

    for record in records:
        embedding = embedder.embed_query(record["text"])
        with driver.session() as session:
            session.run(
                "MATCH (c:Chunk) WHERE elementId(c) = $id SET c.embedding = $embedding",
                id=record["id"],
                embedding=embedding,
            )
            updated += 1

    return updated


# ── Index creation ──────────────────────────────────────────────────────────


def create_vector_idx(driver: Driver) -> None:
    """Create the chunkEmbeddings vector index (1024 dims, cosine)."""
    # Drop if exists
    try:
        with driver.session() as session:
            session.run("DROP INDEX chunkEmbeddings IF EXISTS")
    except Exception:
        pass

    create_vector_index(
        driver=driver,
        name="chunkEmbeddings",
        label="Chunk",
        embedding_property="embedding",
        dimensions=1024,
        similarity_fn="cosine",
    )


def create_fulltext_indexes(driver: Driver) -> None:
    """Create fulltext indexes for chunk text and entity names."""
    with driver.session() as session:
        # search_chunks -- fulltext on Chunk.text
        try:
            session.run("DROP INDEX search_chunks IF EXISTS")
        except Exception:
            pass

        # search_entities -- fulltext on Company/Product/RiskFactor names
        try:
            session.run("DROP INDEX search_entities IF EXISTS")
        except Exception:
            pass

    create_fulltext_index(
        driver=driver,
        name="search_chunks",
        label="Chunk",
        node_properties=["text"],
    )

    create_fulltext_index(
        driver=driver,
        name="search_entities",
        label="Company",
        node_properties=["name"],
    )

    # Add Product and RiskFactor to search_entities
    # The create_fulltext_index helper only supports a single label, so we
    # recreate with raw Cypher for the multi-label version.
    with driver.session() as session:
        session.run("DROP INDEX search_entities IF EXISTS")
        session.run(
            "CREATE FULLTEXT INDEX search_entities IF NOT EXISTS "
            "FOR (n:Company|Product|RiskFactor) ON EACH [n.name]"
        )
