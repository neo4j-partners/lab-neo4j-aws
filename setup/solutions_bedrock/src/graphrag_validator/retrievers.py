"""
Retriever builders for GraphRAG validation.

Constructs VectorRetriever, VectorCypherRetriever, Text2CypherRetriever,
and HybridCypherRetriever instances against the SEC financial graph.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from neo4j import Driver
from neo4j_graphrag.embeddings import BedrockEmbeddings
from neo4j_graphrag.llm import BedrockLLM
from neo4j_graphrag.retrievers import (
    HybridCypherRetriever,
    VectorCypherRetriever,
    VectorRetriever,
)

# ── Expected node counts (used for quick sanity checks) ─────────────────────

EXPECTED_NODE_COUNTS: dict[str, int] = {
    "Company": 10,
    "Product": 30,
    "Service": 20,
    "RiskFactor": 30,
    "FinancialMetric": 50,
    "Executive": 30,
    "AssetManager": 10,
    "Document": 10,
    "Chunk": 10,
}

# ── Retrieval query for VectorCypherRetriever ───────────────────────────────

CONTEXT_QUERY: Final[str] = """
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)<-[:FILED]-(company:Company)
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
OPTIONAL MATCH (company)-[:OFFERS_PRODUCT]->(product:Product)
WITH node, score, company, doc,
     collect(DISTINCT risk.name)[0..5] AS risks,
     collect(DISTINCT product.name)[0..5] AS products
RETURN node.text AS text,
       score,
       company.name AS company,
       company.ticker AS ticker,
       risks,
       products
"""

# ── Retrieval query for HybridCypherRetriever ───────────────────────────────

HYBRID_CONTEXT_QUERY: Final[str] = """
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)<-[:FILED]-(company:Company)
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
OPTIONAL MATCH (company)-[:OFFERS_PRODUCT]->(product:Product)
OPTIONAL MATCH (company)-[:OFFERS_SERVICE]->(service:Service)
WITH node, score, company, doc,
     collect(DISTINCT risk.name)[0..5] AS risks,
     collect(DISTINCT product.name)[0..5] AS products,
     collect(DISTINCT service.name)[0..5] AS services
RETURN node.text AS text,
       score,
       company.name AS company,
       company.ticker AS ticker,
       doc.filing_type AS filing_type,
       risks,
       products,
       services
"""

# ── Retrievers dataclass ────────────────────────────────────────────────────


@dataclass
class Retrievers:
    """Holds the Neo4j driver, AI services, and pre-built retriever instances."""

    driver: Driver
    embedder: BedrockEmbeddings
    llm: BedrockLLM
    vector: VectorRetriever
    vector_cypher: VectorCypherRetriever
    hybrid_cypher: HybridCypherRetriever


def build_retrievers(
    driver: Driver,
    embedder: BedrockEmbeddings,
    llm: BedrockLLM,
) -> Retrievers:
    """Construct all four retriever instances against the loaded graph.

    Args:
        driver: An open Neo4j driver.
        embedder: BedrockEmbeddings (Titan V2, 1024 dims).
        llm: BedrockLLM (Claude).

    Returns:
        A Retrievers dataclass with all instances populated.
    """
    vector = VectorRetriever(
        driver=driver,
        index_name="chunkEmbeddings",
        embedder=embedder,
        return_properties=["text"],
    )

    vector_cypher = VectorCypherRetriever(
        driver=driver,
        index_name="chunkEmbeddings",
        embedder=embedder,
        retrieval_query=CONTEXT_QUERY,
    )

    hybrid_cypher = HybridCypherRetriever(
        driver=driver,
        vector_index_name="chunkEmbeddings",
        fulltext_index_name="search_chunks",
        embedder=embedder,
        retrieval_query=HYBRID_CONTEXT_QUERY,
    )

    return Retrievers(
        driver=driver,
        embedder=embedder,
        llm=llm,
        vector=vector,
        vector_cypher=vector_cypher,
        hybrid_cypher=hybrid_cypher,
    )
