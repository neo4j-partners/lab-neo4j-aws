"""
Embeddings and Vector Search

This solution generates embeddings for Chunk nodes created by 01_01_data_loading
and creates a vector index for semantic similarity search.

Run with: uv run python main.py solutions 2
"""

from neo4j_graphrag.indexes import create_vector_index

from config import get_neo4j_driver, get_embedder, BedrockConfig

INDEX_NAME = "chunkEmbeddings"


def generate_and_store_embeddings(driver, embedder) -> int:
    """Generate embeddings for all chunks that don't have one yet."""
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Chunk)
            WHERE c.embedding IS NULL
            RETURN elementId(c) AS chunk_id, c.text AS text, c.index AS index
            ORDER BY c.index
        """)
        chunks = list(result)

    if not chunks:
        print("All chunks already have embeddings")
        return 0

    print(f"Found {len(chunks)} chunks without embeddings")

    for chunk in chunks:
        embedding = embedder.embed_query(chunk["text"])
        with driver.session() as session:
            session.run("""
                MATCH (c:Chunk) WHERE elementId(c) = $chunk_id
                SET c.embedding = $embedding
            """, chunk_id=chunk["chunk_id"], embedding=embedding)
        print(f"  Embedded Chunk {chunk['index']} ({len(embedding)} dimensions)")

    return len(chunks)


def create_index(driver) -> None:
    """Create vector index for similarity search."""
    config = BedrockConfig()

    # Drop existing index
    try:
        with driver.session() as session:
            session.run(f"DROP INDEX {INDEX_NAME} IF EXISTS")
    except Exception:
        pass

    create_vector_index(
        driver=driver,
        name=INDEX_NAME,
        label="Chunk",
        embedding_property="embedding",
        dimensions=config.embedding_dimensions,
        similarity_fn="cosine",
    )


def vector_search(driver, embedder, query: str, top_k: int = 3) -> list:
    """Search for chunks similar to the query."""
    query_embedding = embedder.embed_query(query)

    with driver.session() as session:
        result = session.run("""
            CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
            YIELD node, score
            RETURN node.text as text, node.index as idx, score
            ORDER BY score DESC
        """, index_name=INDEX_NAME, top_k=top_k, embedding=query_embedding)
        return list(result)


def demo_search(driver, embedder) -> None:
    """Demo vector similarity search."""
    queries = [
        "What products does Apple make?",
        "What are the key risk factors?",
        "What services does the company offer?",
        "How did Apple perform financially?",
    ]

    for query in queries:
        print(f'\nQuery: "{query}"')
        print("-" * 50)
        results = vector_search(driver, embedder, query, top_k=1)
        if results:
            record = results[0]
            print(f"Best match (score: {record['score']:.4f}, Chunk {record['idx']}):")
            print(f"  {record['text'][:150]}...")


def main():
    """Run embeddings demo."""
    with get_neo4j_driver() as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j successfully!")

        embedder = get_embedder()
        print(f"Embedder: {embedder.model_id}")

        # Generate embeddings for existing chunks
        print("\nGenerating embeddings...")
        count = generate_and_store_embeddings(driver, embedder)
        print(f"Embedded {count} chunks")

        # Create index
        print("\nCreating vector index...")
        create_index(driver)
        print(f"Created vector index: {INDEX_NAME}")

        # Demo search
        print("\n=== Vector Search Demo ===")
        demo_search(driver, embedder)

    print("\n\nConnection closed.")


if __name__ == "__main__":
    main()
