"""
Introduction to Strands Agents with MCP (Text2Cypher)

This solution demonstrates the Text2Cypher pattern: a Strands Agent connected
to a Neo4j MCP Server. The agent discovers tools at startup and writes its own
Cypher queries — no custom @tool wrappers needed.

Run with: uv run python main.py solutions <N>
"""

import os
import sys

from botocore.config import Config as BotocoreConfig
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(_env_path)

MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
REGION = os.getenv("AWS_REGION", os.getenv("REGION", "us-east-1"))
MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL")
MCP_ACCESS_TOKEN = os.getenv("MCP_ACCESS_TOKEN")


# ---------------------------------------------------------------------------
# 2. System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a financial analysis assistant with access to a Neo4j knowledge graph containing SEC 10-K filing data (companies, products, risk factors, asset managers, and document chunks).

Rules:
1. Always retrieve the database schema before writing Cypher queries.
2. Only use read-only Cypher (MATCH, RETURN, WITH, WHERE, ORDER BY, LIMIT).
3. Use modern Cypher syntax:
   - Use elementId(n) instead of id(n)
   - Use COUNT{ pattern } instead of size((pattern))
   - Use EXISTS{ pattern } instead of exists((pattern))
   - Always use $parameter syntax for dynamic values
4. Keep results concise — limit to 10 rows unless asked otherwise.
"""


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------


def main():
    """Run Text2Cypher demo via Strands Agent + MCP."""
    print(f"Model:     {MODEL_ID}")
    print(f"Region:    {REGION}")

    bedrock_model = BedrockModel(
        model_id=MODEL_ID,
        region_name=REGION,
        temperature=0,
        boto_client_config=BotocoreConfig(read_timeout=300),
    )

    mcp_client = MCPClient(lambda: streamablehttp_client(
        url=MCP_GATEWAY_URL,
        headers={"Authorization": f"Bearer {MCP_ACCESS_TOKEN}"},
    ))

    with mcp_client:
        # Discover available tools from the MCP server
        mcp_tools = mcp_client.list_tools_sync()
        tool_names = [t.tool_name for t in mcp_tools]
        print(f"MCP tools discovered: {tool_names}")
        print(f"Model: {MODEL_ID}\n")

        agent = Agent(
            model=bedrock_model,
            system_prompt=SYSTEM_PROMPT,
            tools=mcp_tools,
        )

        def query(question: str):
            """Ask the agent a question about the knowledge graph."""
            print(f'Question: "{question}"')
            print("-" * 60)
            response = agent(question)
            print(f"\n{response}")
            return response

        # --- Run queries ---

        # Schema discovery
        print("=" * 60)
        query("What is the database schema? Give me a brief summary.")

        # Single-hop traversal: Company → Product
        print("\n" + "=" * 60)
        query("What products does NVIDIA offer?")

        # Aggregation across the graph
        print("\n" + "=" * 60)
        query(
            "Which risk factors are shared by more than one company? "
            "Show the risk factor and which companies face it."
        )

        # Multi-relationship query: competition and partnership
        print("\n" + "=" * 60)
        query("Who are NVIDIA's competitors? Are any of them also partners?")

        # Portfolio analysis: Asset Manager → Company → Risk
        print("\n" + "=" * 60)
        query(
            "What companies does Berkshire Hathaway own, and what risk factors "
            "do those companies face?"
        )


if __name__ == "__main__":
    main()
