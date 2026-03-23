"""
Graph-Enriched Search via MCP

This solution demonstrates vector search enriched with graph context
(documents, neighboring chunks, entities) through the Neo4j MCP server.

Run with: uv run python main.py solutions <N>
"""

import asyncio
import json
import os

import boto3
import nest_asyncio
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

nest_asyncio.apply()

# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

# Load configuration from CONFIG.txt at project root
_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "CONFIG.txt")
load_dotenv(_config_path)

MODEL_ID = os.getenv("MODEL_ID")
REGION = os.getenv("REGION", "us-east-1")
MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL")
MCP_ACCESS_TOKEN = os.getenv("MCP_ACCESS_TOKEN")

# Derive BASE_MODEL_ID for cross-region inference profiles
if MODEL_ID and MODEL_ID.startswith("us.anthropic."):
    BASE_MODEL_ID = MODEL_ID.replace("us.anthropic.", "anthropic.")
elif MODEL_ID and MODEL_ID.startswith("global.anthropic."):
    BASE_MODEL_ID = MODEL_ID.replace("global.anthropic.", "anthropic.")
else:
    BASE_MODEL_ID = None

# ---------------------------------------------------------------------------
# 2. Embedding Helper
# ---------------------------------------------------------------------------

NOVA_MODEL_ID = "amazon.nova-2-multimodal-embeddings-v1:0"
EMBEDDING_DIMENSIONS = 1024

bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)


def get_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text using Bedrock Nova."""
    request_body = {
        "taskType": "SINGLE_EMBEDDING",
        "singleEmbeddingParams": {
            "embeddingPurpose": "GENERIC_INDEX",
            "embeddingDimension": EMBEDDING_DIMENSIONS,
            "text": {
                "truncationMode": "END",
                "value": text,
            },
        },
    }
    response = bedrock_runtime.invoke_model(
        modelId=NOVA_MODEL_ID,
        body=json.dumps(request_body),
    )
    result = json.loads(response["body"].read())
    return result["embeddings"][0]["embedding"]


# ---------------------------------------------------------------------------
# 3. System Prompts
# ---------------------------------------------------------------------------

VECTOR_ONLY_PROMPT = """You are a retrieval assistant that performs vector search against a Neo4j database.

When given a query embedding, use this Cypher to find similar chunks:

CALL db.index.vector.queryNodes('chunkEmbeddings', $top_k, $embedding)
YIELD node, score
RETURN node.text AS text, score
ORDER BY score DESC

Return the chunk text and similarity score. Use the exact embedding provided."""

GRAPH_ENRICHED_PROMPT = """You are a retrieval assistant that performs graph-enriched vector search against a Neo4j database containing SEC 10-K filing data.

When given a query embedding, use this Cypher to find similar chunks WITH graph context:

CALL db.index.vector.queryNodes('chunkEmbeddings', $top_k, $embedding)
YIELD node, score
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(node)
WITH node, doc, score,
     CASE WHEN prev IS NOT NULL THEN prev.text ELSE '' END AS prev_text,
     CASE WHEN next IS NOT NULL THEN next.text ELSE '' END AS next_text
RETURN node.text AS text,
       score,
       doc.name AS document,
       prev_text AS previous_chunk,
       next_text AS next_chunk
ORDER BY score DESC

This query:
1. Finds the most similar chunks via vector search
2. Traverses FROM_DOCUMENT to get the source document name
3. Follows NEXT_CHUNK relationships to get neighboring chunk text
4. Returns the enriched context alongside each match

Use the exact embedding provided. For each result, show:
- Similarity score
- Source document name
- The matched chunk text
- Context from neighboring chunks (if available)"""

ENTITY_ENRICHED_PROMPT = """You are a retrieval assistant that performs entity-enriched vector search against a Neo4j database containing SEC 10-K filing data.

When given a query embedding, use this Cypher to find similar chunks WITH entity context:

CALL db.index.vector.queryNodes('chunkEmbeddings', $top_k, $embedding)
YIELD node, score
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (company:Company)-[:FROM_CHUNK]->(node)
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
OPTIONAL MATCH (product:Product)-[:FROM_CHUNK]->(node)
WITH node, doc, score,
     collect(DISTINCT company.name) AS companies,
     collect(DISTINCT risk.name)[0..5] AS risks,
     collect(DISTINCT product.name)[0..5] AS products
RETURN node.text AS text,
       score,
       doc.name AS document,
       companies,
       risks,
       products
ORDER BY score DESC

This query:
1. Finds the most similar chunks via vector search
2. Traverses FROM_DOCUMENT to get the source document
3. Follows FROM_CHUNK to find companies and products mentioned in the chunk
4. Follows FACES_RISK from companies to find their risk factors

Use the exact embedding provided. For each result, show:
- Similarity score
- Source document name
- The matched chunk text
- Companies, products, and risk factors connected to the chunk"""

QA_PROMPT = """You are a financial analysis assistant with access to a Neo4j knowledge graph containing SEC 10-K filing data.

You have MCP tools to execute Cypher queries. Use entity-enriched vector search to answer questions:

CALL db.index.vector.queryNodes('chunkEmbeddings', $top_k, $embedding)
YIELD node, score
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (company:Company)-[:FROM_CHUNK]->(node)
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
OPTIONAL MATCH (product:Product)-[:FROM_CHUNK]->(node)
WITH node, doc, score,
     collect(DISTINCT company.name) AS companies,
     collect(DISTINCT risk.name)[0..5] AS risks,
     collect(DISTINCT product.name)[0..5] AS products
RETURN node.text AS text, score, doc.name AS document,
       companies, risks, products
ORDER BY score DESC

After retrieving results, synthesize a clear answer based on the retrieved context.
Include the companies, products, and risk factors found. Cite the source documents.
Use the exact embedding provided."""


# ---------------------------------------------------------------------------
# 4. Compare Search Helper
# ---------------------------------------------------------------------------


async def compare_search(query: str, top_k: int = 3):
    """Run the same query through all three agents and display results."""
    # Initialize LLM
    llm_kwargs = {
        "model": MODEL_ID,
        "region_name": REGION,
        "temperature": 0,
    }
    if BASE_MODEL_ID:
        llm_kwargs["base_model_id"] = BASE_MODEL_ID

    llm = ChatBedrockConverse(**llm_kwargs)

    # Connect to MCP server
    async with MultiServerMCPClient(
        {
            "neo4j": {
                "transport": "streamable_http",
                "url": MCP_GATEWAY_URL,
                "headers": {
                    "Authorization": f"Bearer {MCP_ACCESS_TOKEN}",
                },
            }
        }
    ) as mcp_client:
        tools = await mcp_client.get_tools()
        print(f"MCP tools: {[t.name for t in tools]}")

        # Create all three agents
        vector_agent = create_react_agent(llm, tools, prompt=VECTOR_ONLY_PROMPT)
        graph_agent = create_react_agent(llm, tools, prompt=GRAPH_ENRICHED_PROMPT)
        entity_agent = create_react_agent(llm, tools, prompt=ENTITY_ENRICHED_PROMPT)

        embedding = get_embedding(query)

        message = (
            f"Run a vector search for the following query. Use top_k={top_k}.\n\n"
            f"Query: {query}\n\n"
            f"Embedding (use this exact array in the Cypher query):\n{json.dumps(embedding)}"
        )

        print(f'Query: "{query}"')
        print("=" * 60)

        # Vector-only search
        print("\n--- VECTOR-ONLY RESULTS ---\n")
        vector_result = await vector_agent.ainvoke(
            {"messages": [HumanMessage(content=message)]}
        )
        print(vector_result["messages"][-1].content)

        # Graph-enriched search
        print("\n\n--- GRAPH-ENRICHED RESULTS ---\n")
        graph_result = await graph_agent.ainvoke(
            {"messages": [HumanMessage(content=message)]}
        )
        print(graph_result["messages"][-1].content)

        # Entity-enriched search
        print("\n\n--- ENTITY-ENRICHED RESULTS ---\n")
        entity_result = await entity_agent.ainvoke(
            {"messages": [HumanMessage(content=message)]}
        )
        print(entity_result["messages"][-1].content)

    return vector_result, graph_result, entity_result


# ---------------------------------------------------------------------------
# 5. Q&A Helper
# ---------------------------------------------------------------------------


async def ask(query: str, top_k: int = 5):
    """Ask a question using graph-enriched vector search for context."""
    # Initialize LLM
    llm_kwargs = {
        "model": MODEL_ID,
        "region_name": REGION,
        "temperature": 0,
    }
    if BASE_MODEL_ID:
        llm_kwargs["base_model_id"] = BASE_MODEL_ID

    llm = ChatBedrockConverse(**llm_kwargs)

    # Connect to MCP server
    async with MultiServerMCPClient(
        {
            "neo4j": {
                "transport": "streamable_http",
                "url": MCP_GATEWAY_URL,
                "headers": {
                    "Authorization": f"Bearer {MCP_ACCESS_TOKEN}",
                },
            }
        }
    ) as mcp_client:
        tools = await mcp_client.get_tools()

        qa_agent = create_react_agent(llm, tools, prompt=QA_PROMPT)

        embedding = get_embedding(query)

        message = (
            f"Answer this question using graph-enriched vector search with top_k={top_k}.\n\n"
            f"Question: {query}\n\n"
            f"Embedding:\n{json.dumps(embedding)}"
        )

        print(f'Question: "{query}"')
        print("-" * 60)

        result = await qa_agent.ainvoke(
            {"messages": [HumanMessage(content=message)]}
        )
        print(f"\n{result['messages'][-1].content}")

    return result


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------


async def main():
    """Run graph-enriched search demo."""
    print(f"Model:     {MODEL_ID}")
    print(f"Region:    {REGION}")
    print()

    # Compare: risk factors query
    print("=" * 60)
    print("COMPARISON 1: Risk factors")
    print("=" * 60)
    await compare_search(
        "What are the key risk factors mentioned in Apple's 10-K filing?"
    )

    print("\n")

    # Compare: financial performance query
    print("=" * 60)
    print("COMPARISON 2: Financial performance")
    print("=" * 60)
    await compare_search("What financial metrics indicate company performance?")

    print("\n")

    # Q&A: risk factors
    print("=" * 60)
    print("Q&A 1: Apple risk factors")
    print("=" * 60)
    await ask("What are the key risk factors mentioned in Apple's 10-K filing?")

    print("\n")

    # Q&A: cybersecurity risks
    print("=" * 60)
    print("Q&A 2: Cybersecurity risks")
    print("=" * 60)
    await ask("Which companies face cybersecurity-related risks?")


if __name__ == "__main__":
    asyncio.run(main())
