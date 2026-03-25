"""
Hybrid Search and GraphRAG

Demonstrates hybrid search — combining vector similarity and fulltext keyword
search in a single retriever. Uses HybridRetriever to blend both search methods,
then adds graph traversal with HybridCypherRetriever to build the most capable
retrieval pipeline in the lab.

Key concepts:
- HybridRetriever runs both vector and fulltext indexes simultaneously
- Alpha parameter: 1.0=pure vector, 0.0=pure fulltext, 0.5=balanced
- HybridCypherRetriever adds Cypher-based graph traversal on top of hybrid search
- GraphRAG orchestrates retrieval + LLM answer generation

Usage:
    uv run python main.py solutions 10
"""

from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.retrievers import HybridRetriever, HybridCypherRetriever

from config import get_neo4j_driver, get_embedder, get_llm

# Index names
VECTOR_INDEX = "chunkEmbeddings"
FULLTEXT_INDEX = "search_chunks"

# Retrieval query for HybridCypherRetriever
# This runs AFTER hybrid search finds matching Chunk nodes
# 'node' = matched Chunk, 'score' = combined hybrid score
RETRIEVAL_QUERY = """
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)<-[:FILED]-(company:Company)
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
OPTIONAL MATCH (product:Product)-[:FROM_CHUNK]->(node)
WITH node, doc, score,
     collect(DISTINCT company.name) AS companies,
     collect(DISTINCT risk.name)[0..5] AS risks,
     collect(DISTINCT product.name)[0..5] AS products
RETURN node.text AS text,
       score,
       {document: doc.name, companies: companies, products: products, risks: risks} AS metadata
"""


def check_indexes(driver) -> bool:
    """Verify both vector and fulltext indexes exist."""
    with driver.session() as session:
        result = session.run(
            "SHOW FULLTEXT INDEXES YIELD name WHERE name = $name RETURN name",
            name=FULLTEXT_INDEX,
        )
        if not result.single():
            print(f"\nError: Fulltext index '{FULLTEXT_INDEX}' not found.")
            print("Run notebook 01 first.")
            return False

        result = session.run(
            "SHOW VECTOR INDEXES YIELD name WHERE name = $name RETURN name",
            name=VECTOR_INDEX,
        )
        if not result.single():
            print(f"\nError: Vector index '{VECTOR_INDEX}' not found.")
            print("Run notebook 02 first.")
            return False

    print(f"Vector index: {VECTOR_INDEX} ✓")
    print(f"Fulltext index: {FULLTEXT_INDEX} ✓")
    return True


def compare_alpha_values(retriever: HybridRetriever, query: str) -> None:
    """Compare different alpha values for the same query."""
    print(f"\n=== Compare Alpha Values ===")
    print(f"Query: '{query}'")

    for alpha in [1.0, 0.5, 0.0]:
        label = {1.0: "Pure Vector", 0.5: "Balanced", 0.0: "Pure Fulltext"}[alpha]

        results = retriever.search(query_text=query, top_k=3, ranker="linear", alpha=alpha)

        print(f"\n--- Alpha={alpha} ({label}) ---")
        for i, item in enumerate(results.items, 1):
            score = item.metadata.get("score", 0.0) if item.metadata else 0.0
            text = str(item.content)[:120]
            print(f"{i}. Score: {score:.4f} | {text}...")


def graphrag_pipeline(llm, retriever: HybridCypherRetriever, query: str) -> None:
    """Full GraphRAG pipeline with hybrid retrieval and graph context."""
    print(f"\n=== Full GraphRAG Pipeline ===")

    rag = GraphRAG(llm=llm, retriever=retriever)
    response = rag.search(query, retriever_config={"top_k": 5}, return_context=True)

    print(f'Query: "{query}"\n')
    print("Answer:")
    print(response.answer)

    print("\n\n=== Retrieved Context ===")
    for i, item in enumerate(response.retriever_result.items, 1):
        content_str = str(item.content)
        preview = content_str[:250] + "..." if len(content_str) > 250 else content_str
        print(f"\n[{i}] {preview}")


def main() -> None:
    """Run hybrid RAG examples matching notebook 05_hybrid_rag."""
    with get_neo4j_driver() as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j")

        embedder = get_embedder()
        llm = get_llm()
        print(f"Embedder: {embedder.model_id}")
        print(f"LLM: {llm.model_id}")

        # Check indexes exist
        if not check_indexes(driver):
            return

        # HybridRetriever — basic hybrid search
        hybrid_retriever = HybridRetriever(
            driver=driver,
            vector_index_name=VECTOR_INDEX,
            fulltext_index_name=FULLTEXT_INDEX,
            embedder=embedder,
            return_properties=["text"],
        )
        print("\nHybridRetriever initialized!")

        # Compare alpha values
        compare_alpha_values(hybrid_retriever, "Apple revenue growth")

        # HybridCypherRetriever — hybrid search with graph traversal
        hybrid_cypher_retriever = HybridCypherRetriever(
            driver=driver,
            vector_index_name=VECTOR_INDEX,
            fulltext_index_name=FULLTEXT_INDEX,
            embedder=embedder,
            retrieval_query=RETRIEVAL_QUERY,
        )
        print("\nHybridCypherRetriever initialized!")

        # Full GraphRAG pipeline
        graphrag_pipeline(
            llm,
            hybrid_cypher_retriever,
            "What are the key financial performance indicators and risk factors in Apple's filing?",
        )

    print("\nConnection closed")


if __name__ == "__main__":
    main()
