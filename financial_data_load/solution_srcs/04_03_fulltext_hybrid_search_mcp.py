"""
Fulltext and Hybrid Search via MCP

This solution demonstrates fulltext keyword search and agent-driven hybrid
search with custom @tool wrappers through the Neo4j MCP server.

Run with: uv run python main.py solutions <N>
"""

import asyncio
import json
import os
import sys

import nest_asyncio
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

nest_asyncio.apply()

# Add project root to sys.path so lib imports work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from lib.data_utils import get_embedding, BedrockConfig  # noqa: E402
from lib.mcp_utils import MCPConnection  # noqa: E402


# =============================================================================
# Fulltext Search Agent
# =============================================================================

FULLTEXT_PROMPT = """You are a retrieval assistant that performs fulltext keyword search against a Neo4j database containing SEC 10-K filing data.

You have MCP tools to execute Cypher queries. Use the fulltext index on Chunk text:

CALL db.index.fulltext.queryNodes('search_chunks', $search_term)
YIELD node, score
RETURN node.text AS text, score
ORDER BY score DESC
LIMIT $limit

SEARCH OPERATORS (use these in the search term string):
- Fuzzy: append ~ to handle typos (e.g., 'revnue~' matches 'revenue')
- Wildcard: append * for prefix matching (e.g., 'risk*' matches 'risks', 'risky')
- Boolean AND: both terms required (e.g., 'revenue AND growth')
- Boolean NOT: exclude terms (e.g., 'revenue NOT decline')

For each result, show the Lucene relevance score and a preview of the chunk text."""

# =============================================================================
# Fulltext + Graph Traversal Agent
# =============================================================================

FULLTEXT_GRAPH_PROMPT = """You are a retrieval assistant that performs fulltext search with graph context against a Neo4j database containing SEC 10-K filing data.

When given a search term, use this Cypher to find keyword matches WITH entity context:

CALL db.index.fulltext.queryNodes('search_chunks', $search_term)
YIELD node, score
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (company:Company)-[:FROM_CHUNK]->(node)
OPTIONAL MATCH (product:Product)-[:FROM_CHUNK]->(node)
WITH node, doc, score,
     collect(DISTINCT company.name) AS companies,
     collect(DISTINCT product.name) AS products
RETURN node.text AS text, score, doc.name AS document, companies, products
ORDER BY score DESC
LIMIT $limit

For each result, show the score, document name, matched text, and any connected companies or products."""

# =============================================================================
# Hybrid Agent Prompt
# =============================================================================

HYBRID_PROMPT = """You are a financial analysis assistant that combines vector (semantic) and fulltext (keyword) search to answer questions about SEC 10-K filings.

You have two search tools:
1. vector_search: Finds semantically similar content (good for conceptual questions)
2. fulltext_search_tool: Finds exact keyword matches (good for specific names, terms, tickers)

HYBRID SEARCH STRATEGY:
For comprehensive results, run BOTH search tools with the same query, then synthesize an answer from the combined results. This gives you the benefits of both semantic understanding and keyword precision.

When the query contains specific names or terms (like "Apple", "AAPL"), fulltext search may find more precise matches. When the query is conceptual ("supply chain risks"), vector search captures semantic meaning.

For the best results, always run both searches and compare what each found."""


# =============================================================================
# Helper Functions
# =============================================================================

def show_tool_calls(result):
    """Display raw tool call inputs and outputs from an agent run."""
    for msg in result['messages']:
        # Tool call requests (from the agent)
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for call in msg.tool_calls:
                print(f"\n{'=' * 60}")
                print(f"TOOL CALL: {call['name']}")
                args = call.get('args', {})
                for key, value in args.items():
                    val_str = str(value)
                    if len(val_str) > 200:
                        print(f"  {key}: {val_str[:200]}... [{len(val_str)} chars]")
                    else:
                        print(f"  {key}: {val_str}")

        # Tool responses (from Neo4j via MCP)
        if hasattr(msg, 'name') and msg.name:
            content = str(msg.content)
            print(f"\nRESPONSE ({msg.name}):")
            print(f"  {content[:500]}{'...' if len(content) > 500 else ''}")


# =============================================================================
# Main
# =============================================================================

async def main():
    # -------------------------------------------------------------------------
    # 1. Configuration and Setup
    # -------------------------------------------------------------------------
    config_path = os.path.join(PROJECT_ROOT, 'CONFIG.txt')
    load_dotenv(config_path)
    MODEL_ID = os.getenv('MODEL_ID')
    REGION = os.getenv('REGION', 'us-east-1')

    if MODEL_ID and MODEL_ID.startswith('us.anthropic.'):
        BASE_MODEL_ID = MODEL_ID.replace('us.anthropic.', 'anthropic.')
    elif MODEL_ID and MODEL_ID.startswith('global.anthropic.'):
        BASE_MODEL_ID = MODEL_ID.replace('global.anthropic.', 'anthropic.')
    else:
        BASE_MODEL_ID = None

    # Initialize LLM
    llm_kwargs = {'model': MODEL_ID, 'region_name': REGION, 'temperature': 0}
    if BASE_MODEL_ID:
        llm_kwargs['base_model_id'] = BASE_MODEL_ID
    llm = ChatBedrockConverse(**llm_kwargs)

    # Connect to MCP server
    mcp = await MCPConnection.create(config_path)

    # Test embedding function
    test_emb = get_embedding('test')
    print(f'Model:     {MODEL_ID}')
    print(f'Embedding: {len(test_emb)} dimensions')
    print('Setup complete!')

    # -------------------------------------------------------------------------
    # 2. Fulltext Search Agent
    # -------------------------------------------------------------------------
    fulltext_agent = create_react_agent(llm, mcp.get_tools(), prompt=FULLTEXT_PROMPT)
    print('Fulltext agent ready!')

    # -------------------------------------------------------------------------
    # 3. Basic Fulltext Search
    # -------------------------------------------------------------------------
    async def fulltext_search(term: str, limit: int = 5):
        """Run a fulltext keyword search through the MCP agent."""
        print(f'Search term: "{term}"')
        print('-' * 60)

        message = f"Search for chunks containing '{term}'. Use limit={limit}."
        result = await fulltext_agent.ainvoke({'messages': [HumanMessage(content=message)]})
        print(result['messages'][-1].content)
        return result

    result = await fulltext_search('revenue')

    # -------------------------------------------------------------------------
    # 4. Search Operators
    # -------------------------------------------------------------------------
    # Fuzzy search — handles typos
    result = await fulltext_search('revnue~', limit=3)

    # Wildcard search — prefix matching
    result = await fulltext_search('risk*', limit=3)

    # Boolean AND — both terms must appear
    result = await fulltext_search('revenue AND growth', limit=3)

    # -------------------------------------------------------------------------
    # 5. Fulltext + Graph Traversal
    # -------------------------------------------------------------------------
    fulltext_graph_agent = create_react_agent(llm, mcp.get_tools(), prompt=FULLTEXT_GRAPH_PROMPT)
    print('Fulltext + graph agent ready!')

    async def fulltext_graph_search(term: str, limit: int = 5):
        """Run fulltext search with graph traversal."""
        print(f'Search term: "{term}" (with graph context)')
        print('-' * 60)

        message = f"Search for chunks containing '{term}' with graph context. Use limit={limit}."
        result = await fulltext_graph_agent.ainvoke({'messages': [HumanMessage(content=message)]})
        print(result['messages'][-1].content)
        return result

    result = await fulltext_graph_search('iPhone')

    # -------------------------------------------------------------------------
    # 7. Agent-Driven Hybrid Search with @tool Wrappers
    # -------------------------------------------------------------------------
    @tool
    async def vector_search(query: str, top_k: int = 5) -> str:
        """Search for semantically similar chunks using vector embeddings.
        Use this for conceptual or semantic queries where exact words may differ."""
        # Step 1: Embed the query
        embedding = get_embedding(query)

        # Step 2: Vector search via MCP
        return await mcp.execute_query(f"""
            CALL db.index.vector.queryNodes('chunkEmbeddings', {top_k}, {json.dumps(embedding)})
            YIELD node, score
            MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
            RETURN node.text AS text, score, doc.name AS document
            ORDER BY score DESC
        """)

    @tool
    async def fulltext_search_tool(term: str, limit: int = 5) -> str:
        """Search for chunks containing specific keywords.
        Use this for exact terms, company names, tickers, or partial matches.
        Supports operators: fuzzy (term~), wildcard (term*), AND, NOT."""
        return await mcp.execute_query(f"""
            CALL db.index.fulltext.queryNodes('search_chunks', '{term}')
            YIELD node, score
            MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
            RETURN node.text AS text, score, doc.name AS document
            ORDER BY score DESC
            LIMIT {limit}
        """)

    print(f'Custom tools created:')
    print(f'  - vector_search: {vector_search.description}')
    print(f'  - fulltext_search_tool: {fulltext_search_tool.description}')

    # Agent gets ONLY the custom tools — never sees raw embeddings or MCP tools
    hybrid_agent = create_react_agent(llm, [vector_search, fulltext_search_tool], prompt=HYBRID_PROMPT)
    print('Hybrid agent ready!')

    # -------------------------------------------------------------------------
    # Hybrid Search
    # -------------------------------------------------------------------------
    async def hybrid_search(query: str):
        """Run hybrid search using both vector and fulltext tools."""
        print(f'Question: "{query}"')
        print('=' * 60)

        message = f"Answer this question using BOTH vector search and fulltext search: {query}"
        result = await hybrid_agent.ainvoke({'messages': [HumanMessage(content=message)]})
        print(f'\n{result["messages"][-1].content}')
        return result

    result = await hybrid_search("What are Apple's key risk factors?")

    result = await hybrid_search('Which companies face cybersecurity-related risks?')

    # -------------------------------------------------------------------------
    # 9. Inspecting Tool Calls
    # -------------------------------------------------------------------------
    result = await hybrid_search('What products does Apple offer?')
    print('\n\n=== RAW TOOL CALLS ===')
    show_tool_calls(result)


if __name__ == '__main__':
    asyncio.run(main())
