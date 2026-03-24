# Lab 6 - Advanced Agents: Text2Cypher with MCP

Build an autonomous agent that discovers the graph schema, writes its own Cypher queries, and executes them — the **Text2Cypher** retrieval pattern. This is the most flexible agent pattern in the workshop, and the natural next step after Lab 4's pre-written query templates.

## How This Differs from Lab 4

Lab 4 used **Cypher Templates** and **Graph-Enhanced Vector Search** — pre-written queries that the agent selected and executed. That approach is reliable and predictable, but limited to the queries you define in advance.

This lab uses the **Text2Cypher** pattern: the agent retrieves the graph schema via MCP, reasons about the user's question, and writes original Cypher from scratch. The agent has full autonomy over how it queries the knowledge graph. The trade-off is that query quality depends on the LLM's ability to reason about graph structures, which is why the schema-first approach is critical.

| Aspect | Lab 4 (Cypher Templates) | Lab 6 (Text2Cypher) |
|--------|--------------------------|---------------------|
| **Cypher source** | Pre-written in `@tool` functions | Agent writes from scratch |
| **Schema discovery** | No — queries are hard-coded | Yes — agent calls `get-neo4j-schema` first |
| **Flexibility** | Limited to defined query patterns | Any question the schema can answer |
| **Reliability** | High — expert-reviewed queries | Depends on LLM reasoning quality |
| **MCP role** | Transport layer for query execution | Discovery interface + execution |

## What You'll Learn

- **Text2Cypher pattern**: How an LLM generates Cypher from a schema and a natural language question
- **Schema-first approach**: Why the agent retrieves the graph schema before writing any query
- **MCP tool discovery**: The agent discovers available tools automatically through the MCP protocol
- **Two frameworks**: LangGraph (full-featured, multi-step workflows) and Strands (lightweight, AWS-native)

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Neo4j Aura instance with SEC financial data loaded)
- Your `CONFIG.txt` file updated with MCP Gateway credentials (`MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`)
- AWS credentials configured for Amazon Bedrock access

## Notebooks

This lab provides two notebook options. Both connect to the same MCP server and produce the same results. Choose the one that fits your interest:

| Notebook | Framework | Description |
|----------|-----------|-------------|
| [neo4j_langgraph_mcp_agent.ipynb](neo4j_langgraph_mcp_agent.ipynb) | LangGraph | Full-featured agent with LangChain MCP adapters. Better for complex, multi-step workflows with fine-grained control over the agent loop. |
| [neo4j_strands_mcp_agent.ipynb](neo4j_strands_mcp_agent.ipynb) | Strands | Lightweight agent using the AWS-native Strands SDK. Fewer lines of code, built-in MCP support, simpler API. |

## Sample Queries

Once your agent is running, try these questions about the SEC financial data:

| Category | Example Question |
|----------|-----------------|
| **Exploration** | "How many companies are in the database?" |
| **Products** | "What products does Apple offer?" |
| **Ownership** | "Which asset managers own stakes in NVIDIA?" |
| **Risk** | "What risk factors does Microsoft face?" |
| **Financials** | "Show me the financial metrics for Tesla." |
| **Executives** | "Who are the executives at Amazon?" |
| **Cross-entity** | "Which companies face risk factors related to cybersecurity?" |

## Next Steps

Congratulations — you have completed all labs in the workshop!
