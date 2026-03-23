# Solution Sources Alignment Plan

This document describes how to rewrite `financial_data_load/solution_srcs/` so that each solution file closely replicates the code from the corresponding lab notebook. The goal is to validate that the lab code is correct and runs as expected.

Only Labs 3, 4, and 6 are in scope. All other solution files are left untouched.

---

## Configuration

All solution files load credentials and settings from `financial_data_load/.env` via `solution_srcs/config.py`. The config module needs rewriting: replace the current OpenAI/Azure delegation with Bedrock-native functions matching the patterns used in the lab notebooks. Specifically, config.py should provide:

- **Neo4jConfig** — keep as-is, already loads NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
- **BedrockConfig** — add a settings class for MODEL_ID, REGION (AWS_REGION), EMBEDDING_DIMENSIONS
- **get_neo4j_driver()** — keep the existing context manager
- **get_embedder()** — return a BedrockNovaEmbeddings instance for use with neo4j-graphrag retrievers
- **get_llm()** — return a BedrockLLM instance for use with neo4j-graphrag pipelines
- **get_embedding()** — return a raw float array from Bedrock Nova for use in Cypher vector search queries
- Remove all Azure/OpenAI references, the `src.embeddings` delegation, and the `_get_azure_token` function

---

## Lab 3 — Basic LangGraph Agent

**Source notebook:** `Lab_3_Intro_to_Bedrock_and_Agents/01_basic_langgraph_agent.ipynb`

**New file:** `03_01_basic_langgraph_agent.py`

This solution replicates the local agent portions of the notebook (skipping AgentCore deployment):

- Load MODEL_ID and REGION from config
- Define two simple tools using the @tool decorator: get_current_time (returns formatted datetime) and add_numbers (adds two integers)
- Initialize ChatBedrockConverse with the model config and bind the tools to it
- Build a LangGraph StateGraph with the ReAct pattern: an "agent" node that calls the LLM, a "tools" node using ToolNode, a should_continue conditional edge that routes to tools if the last message has tool_calls or to END otherwise, and an edge from tools back to agent
- Compile the graph and run it with three test queries: asking the current time, adding two numbers, and a combined question that triggers multiple tool calls
- Load sample financial data from the companion text file and run two contextual questions about companies and risk factors

**Replaces:** `03_02_vector_graph_agent.py` and `03_03_text2cypher_agent.py` (old Lab 3 used Microsoft Agent Framework with VectorCypherRetriever — entirely different from the current notebook)

---

## Lab 4 — MCP-Based Retrieval

**Source notebooks:** `Lab_4_MCP_Retrieval/01_vector_search_mcp.ipynb`, `02_graph_enriched_search_mcp.ipynb`, `03_fulltext_hybrid_search_mcp.ipynb`

### 04_01_vector_search_mcp.py

Replicates the first notebook — basic vector search through MCP:

- Load config including MCP_GATEWAY_URL and MCP_ACCESS_TOKEN from the environment
- Handle cross-region inference profile IDs by deriving BASE_MODEL_ID
- Define a get_embedding helper that calls Bedrock Nova to produce a 1024-dimensional embedding
- Set up a MultiServerMCPClient connection to the MCP gateway with Bearer token auth
- Discover MCP tools (get-schema, execute-query)
- Create a LangGraph react agent with a system prompt instructing it to use the chunkEmbeddings vector index via Cypher
- Define a vector_search function that embeds a query, serializes the embedding into the prompt, and invokes the agent
- Run test searches for products, risk factors, and financial metrics

### 04_02_graph_enriched_search_mcp.py

Replicates the second notebook — vector search enriched with graph context:

- Same MCP connection and embedding setup as 04_01
- Create three agent variants, each with a different system prompt containing a different Cypher pattern:
  - Vector-only: returns just chunk text and similarity score
  - Graph-enriched: traverses FROM_DOCUMENT to get document metadata and NEXT_CHUNK to get neighboring chunks for surrounding context
  - Entity-enriched: follows FROM_CHUNK to find connected Company, Product, and RiskFactor nodes
- Define a compare_search function that runs the same query through all three agents and prints results side by side
- Create a dedicated Q&A agent using the entity-enriched prompt and define an ask function for answering questions with full context

### 04_03_fulltext_hybrid_search_mcp.py

Replicates the third notebook — fulltext search and hybrid search with custom tool wrappers:

- Use MCPConnection from lib/mcp_utils.py (project root) to handle MCP boilerplate
- Use get_embedding from lib/data_utils.py (project root) for embeddings
- Create a fulltext search agent with a system prompt for the search_chunks fulltext index, supporting Lucene operators (fuzzy with ~, wildcard with *, boolean AND/NOT)
- Run fulltext search examples demonstrating each operator type
- Create custom @tool-decorated async functions that encapsulate embedding generation and MCP query execution inside the tool:
  - vector_search tool: takes a query string, generates embedding internally, executes vector Cypher via MCP
  - fulltext_search_tool: takes a search term, executes fulltext Cypher via MCP
- Create a hybrid agent that uses only these custom tools (not raw MCP tools) with a system prompt directing it to run both searches and synthesize results
- Include a show_tool_calls helper to inspect what Cypher was sent and what came back

---

## Lab 6 — GraphRAG

**Source notebooks:** `Lab_6_GraphRAG/01_data_loading.ipynb` through `06_hybrid_search.ipynb`

### 06_01_data_loading.py

Replicates the data loading notebook — building the document-chunk graph:

- Connect to Neo4j using config
- Clear existing Document and Chunk nodes
- Create a Document node from sample SEC 10-K text with metadata (path, page number)
- Split the text into overlapping chunks using FixedSizeSplitter (500 chars, 50 char overlap)
- Create Chunk nodes with FROM_DOCUMENT relationships linking each chunk to its document
- Link chunks sequentially with NEXT_CHUNK relationships to preserve reading order
- Print summary counts

### 06_02_embeddings.py

Replicates the embeddings notebook — generating vectors and creating the index:

- Connect to Neo4j and initialize BedrockNovaEmbeddings (1024 dimensions)
- Retrieve all Chunk nodes that lack embeddings
- Generate embeddings for each chunk's text and store as the embedding property on the Chunk node
- Create (or verify) the "chunkEmbeddings" vector index with cosine similarity and 1024 dimensions
- Test with a raw vector search using db.index.vector.queryNodes to confirm the index works

### 06_03_vector_retriever.py

Replicates the vector retriever notebook — semantic search with GraphRAG:

- Connect to Neo4j and get the embedder
- Create a VectorRetriever pointing at the chunkEmbeddings index with the embedder
- Run a semantic search and inspect the returned chunks (text, score)
- Build a GraphRAG pipeline combining the VectorRetriever with a BedrockLLM
- Ask questions and display both the retrieved context and the LLM's synthesized answer

### 06_04_vector_cypher_retriever.py

Replicates the vector cypher retriever notebook — graph-enriched vector search:

- Connect to Neo4j and get the embedder
- Define a custom retrieval_query that, after the vector index returns matching chunks, traverses FROM_CHUNK relationships to find connected Company, Product, and RiskFactor entities
- Create a VectorCypherRetriever with this custom query
- Run searches and show how the enriched context includes entity information beyond the chunk text
- Build a GraphRAG pipeline with the enriched retriever and ask questions that benefit from entity context

### 06_05_fulltext_search.py

Replicates the fulltext search notebook — keyword precision search:

- Connect to Neo4j
- Create (or verify) the "search_chunks" fulltext index on Chunk.text
- Demonstrate basic fulltext search with db.index.fulltext.queryNodes
- Show fuzzy search (term~) for typo tolerance
- Show wildcard search (term*) for prefix matching
- Show boolean operators (AND, NOT) for precise filtering
- Combine fulltext search with graph traversal to enrich results with document metadata via FROM_DOCUMENT

### 06_06_hybrid_search.py

Replicates the hybrid search notebook — combining vector and fulltext retrieval:

- Connect to Neo4j and get the embedder
- Create a HybridRetriever with the chunkEmbeddings vector index and search_chunks fulltext index
- Run the same query with different alpha values (1.0 for pure vector, 0.5 for balanced, 0.0 for pure fulltext) and compare results
- Create a HybridCypherRetriever that adds graph traversal to hybrid results using a custom retrieval_query
- Demonstrate when hybrid search outperforms either individual approach

**Replaces:** `01_01_data_loading.py`, `01_02_embeddings.py`, `02_01_vector_retriever.py`, `02_02_vector_cypher_retriever.py`, `05_01_fulltext_search.py`, `05_02_hybrid_search.py` (old numbering, potentially old patterns)

---

## Files to Remove

These old files are superseded by the new lab-aligned versions listed above:

- `03_02_vector_graph_agent.py` (old Lab 3 — Microsoft Agent Framework)
- `03_03_text2cypher_agent.py` (old Lab 3 — Microsoft Agent Framework)
- `01_01_data_loading.py` (old numbering — now 06_01)
- `01_02_embeddings.py` (old numbering — now 06_02)
- `02_01_vector_retriever.py` (old numbering — now 06_03)
- `02_02_vector_cypher_retriever.py` (old numbering — now 06_04)
- `05_01_fulltext_search.py` (old numbering — now 06_05)
- `05_02_hybrid_search.py` (old numbering — now 06_06)

---

## Files NOT in Scope

These files belong to other labs or shared infrastructure and are left unchanged:

- `config.py` (updated separately as described above)
- `test_connection.py`, `__init__.py`
- `01_03_entity_extraction.py`, `01_04_full_dataset_queries.py`, `01_test_full_data_load.py`
- `02_03_text2cypher_retriever.py`
- `05_01_simple_agent.py`, `05_02_context_provider.py`
- `06_01_fulltext_context_provider.py`, `06_02_vector_context_provider.py`, `06_03_graph_enriched_provider.py`
- `07_01_memory_context_provider.py`, `07_02_entity_extraction.py`, `07_03_memory_tools_agent.py`, `07_04_reasoning_memory.py`

---

## Updates to main.py

The SOLUTIONS list and menu in `financial_data_load/main.py` need updating to:

- Replace old Lab 3 entries (03_02_vector_graph_agent, 03_03_text2cypher_agent) with the new 03_01_basic_langgraph_agent entry
- Add three new Lab 4 entries (04_01, 04_02, 04_03)
- Replace old Lab 6-equivalent entries (01_01, 01_02, 02_01, 02_02, 05_01_fulltext, 05_02_hybrid) with the six new 06_* entries
- Update the printed menu text to reflect the current lab structure and numbering

---

## Verification

After implementation, validate each solution by running it through the solutions menu:

    uv run python main.py solutions <N>

Check that:
- Config loads correctly from .env
- Neo4j connection succeeds
- Bedrock LLM and embedding calls work
- Output matches what the corresponding notebook produces
