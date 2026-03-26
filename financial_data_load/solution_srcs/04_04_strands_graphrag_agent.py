"""
Strands GraphRAG Agent

Combines neo4j-graphrag retrievers (VectorRetriever, VectorCypherRetriever)
with a Strands agent. The agent chooses which retrieval strategy to use
based on the question — bridging Lab 3 (agents) and Lab 4 (retrievers).

Run with: uv run python main.py solutions <N>
"""

import neo4j
from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
from neo4j_graphrag.types import RetrieverResultItem
from strands import Agent, tool
from strands.models import BedrockModel

from config import BedrockConfig, get_embedder, get_neo4j_driver

# Retrieval query traverses from matched chunk to document, company, and
# uses COLLECT subqueries to gather products and risk factors linked to
# the specific chunk via FROM_CHUNK.
RETRIEVAL_QUERY = """
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)<-[:FILED]-(company:Company)
WITH node, doc, score, company
RETURN node.text AS text,
       score,
       {document: doc.accessionNumber,
        filingType: doc.filingType,
        company: company.name,
        products: collect { MATCH (p:Product)-[:FROM_CHUNK]->(node) RETURN p.name },
        risks: collect { MATCH (r:RiskFactor)-[:FROM_CHUNK]->(node) RETURN r.name }
       } AS metadata
"""


def format_record(record: neo4j.Record) -> RetrieverResultItem:
    """Separate chunk text (content for LLM) from structured graph metadata."""
    metadata = record.get("metadata") or {}
    metadata["score"] = record.get("score")
    return RetrieverResultItem(
        content=record.get("text", ""),
        metadata=metadata,
    )


def main():
    """Run Strands GraphRAG agent demo."""
    config = BedrockConfig()

    with get_neo4j_driver() as driver:
        driver.verify_connectivity()
        embedder = get_embedder()

        print("Connected to Neo4j!")
        print(f"Model: {config.model_id}")
        print(f"Embedder: {embedder.model_id}")

        # -----------------------------------------------------------------
        # 1. Initialize both retrievers (from notebooks 02 and 03)
        # -----------------------------------------------------------------

        vector_retriever = VectorRetriever(
            driver=driver,
            index_name="chunkEmbeddings",
            embedder=embedder,
            return_properties=["text"],
        )

        vector_cypher_retriever = VectorCypherRetriever(
            driver=driver,
            index_name="chunkEmbeddings",
            embedder=embedder,
            retrieval_query=RETRIEVAL_QUERY,
            result_formatter=format_record,
        )
        print("Both retrievers initialized!")

        # -----------------------------------------------------------------
        # 2. Define tools that wrap the retrievers
        # -----------------------------------------------------------------

        @tool
        def semantic_search(query: str, top_k: int = 5) -> str:
            """Search SEC 10-K filing chunks by semantic similarity.

            Use this for broad or thematic questions where the text content
            of the filing chunks is sufficient to answer — for example,
            summarizing key themes, finding specific passages, or answering
            questions that don't require knowing which company or product
            is involved.

            Args:
                query: The search query.
                top_k: Number of chunks to return (default 5).

            Returns:
                The matching chunks with similarity scores.
            """
            result = vector_retriever.search(query_text=query, top_k=top_k)
            chunks = []
            for item in result.items:
                score = item.metadata.get("score", 0.0)
                chunks.append(f"[Score: {score:.4f}] {item.content}")
            return "\n\n".join(chunks)

        @tool
        def graph_enriched_search(query: str, top_k: int = 5) -> str:
            """Search SEC 10-K filing chunks with graph-enriched context.

            Use this when the question involves specific companies, products,
            or risk factors. The graph traversal adds structured entity
            information to each chunk — company names, products they offer,
            and risk factors they face — so you can answer entity-specific
            questions with precision.

            Args:
                query: The search query.
                top_k: Number of chunks to return (default 5).

            Returns:
                The matching chunks with similarity scores and entity metadata.
            """
            result = vector_cypher_retriever.search(query_text=query, top_k=top_k)
            chunks = []
            for item in result.items:
                meta = item.metadata or {}
                header = (
                    f"[Score: {meta.get('score', 0):.4f}] "
                    f"Company: {meta.get('company', 'N/A')} | "
                    f"Products: {meta.get('products', [])} | "
                    f"Risks: {meta.get('risks', [])}"
                )
                chunks.append(f"{header}\n{item.content}")
            return "\n\n".join(chunks)

        tools = [semantic_search, graph_enriched_search]
        print(f"Defined {len(tools)} tools: semantic_search, graph_enriched_search")

        # -----------------------------------------------------------------
        # 3. Create the agent
        # -----------------------------------------------------------------

        bedrock_model = BedrockModel(
            model_id=config.model_id,
            region_name=config.region,
            temperature=0,
        )

        agent = Agent(
            model=bedrock_model,
            system_prompt=(
                "You are a financial research assistant with access to SEC 10-K filings "
                "stored in a Neo4j knowledge graph.\n\n"
                "You have two search tools:\n"
                "- semantic_search: finds relevant text chunks by meaning — use for broad "
                "or thematic questions\n"
                "- graph_enriched_search: finds chunks AND returns connected entities "
                "(companies, products, risk factors) — use when the question involves "
                "specific companies or relationships\n\n"
                "Choose the tool that best fits each question. Always ground your answers "
                "in the retrieved data."
            ),
            tools=tools,
        )
        print("Agent created!\n")

        # -----------------------------------------------------------------
        # 4. Test queries — each should trigger a different tool
        # -----------------------------------------------------------------

        queries = [
            ("General / thematic (expect semantic_search)",
             "Summarize the key themes across the 10-K filings."),
            ("Entity-specific (expect graph_enriched_search)",
             "What products does Apple offer and what risks do they face?"),
            ("Multi-entity comparison",
             "Compare the risk factors between Apple and Microsoft. "
             "Which company faces more technology-related risks?"),
        ]

        for label, query in queries:
            print(f"\n{'=' * 60}")
            print(f"Test: {label}")
            print(f"Query: {query}")
            print("=" * 60)
            response = agent(query)
            print()

        # -----------------------------------------------------------------
        # 5. Inspect tool usage from message history
        # -----------------------------------------------------------------

        print("\n" + "=" * 60)
        print("Tool Usage Summary (from message history)")
        print("=" * 60)

        for msg in agent.messages:
            role = msg["role"]
            for content in msg.get("content", []):
                if "toolUse" in content:
                    tool_use = content["toolUse"]
                    print(f"\n[{role}] Called tool: {tool_use['name']}")
                    print(f"         Input: {tool_use['input']}")
                elif "toolResult" in content:
                    tool_result = content["toolResult"]
                    status = tool_result.get("status", "unknown")
                    result_text = ""
                    for block in tool_result.get("content", []):
                        if "text" in block:
                            result_text = block["text"][:200]
                            break
                    print(f"[{role}] Tool result ({status}): {result_text}...")

    print("\n\nConnection closed.")


if __name__ == "__main__":
    main()
