# Neo4j GraphRAG Workshop with AWS Bedrock

**Early Prototype** - This workshop demonstrates an early prototype of using AWS Bedrock for creating data sources for a GraphRAG knowledge graph. It uses a fork of the [neo4j-graphrag-python](https://github.com/neo4j/neo4j-graphrag-python) project that includes Bedrock integration.

## Prerequisites

### 1. Clone the neo4j-graphrag-python Fork

This workshop requires a local fork of the neo4j-graphrag-python library with Bedrock support. Clone it to your machine:

```bash
# Clone the fork (replace with your fork URL)
git clone https://github.com/YOUR_USERNAME/neo4j-graphrag-python.git ~/projects/neo4j-graphrag-python
```

### 2. Update pyproject.toml to Point to Your Local Clone

After cloning, update the `pyproject.toml` in this directory to point to your local copy. Open `new-workshops/pyproject.toml` and find this line:

```toml
"neo4j-graphrag[bedrock] @ file:///Users/ryanknight/projects/neo4j-graphrag-python",
```

Replace it with the path to your local clone:

```toml
"neo4j-graphrag[bedrock] @ file:///YOUR/PATH/TO/neo4j-graphrag-python",
```

For example:
- macOS/Linux: `file:///home/username/projects/neo4j-graphrag-python`
- Windows: `file:///C:/Users/username/projects/neo4j-graphrag-python`

### 3. Environment Configuration

Create a `.env` file in this directory with the following variables:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
```

### 4. AWS Credentials

AWS credentials must be configured via one of:
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- `~/.aws/credentials` file
- IAM role (if running on AWS infrastructure)

## Quick Start

All commands should be run from the `new-workshops/` directory:

```bash
cd new-workshops

# Install dependencies
uv sync

# Test connections
uv run python -m solutions.test_connection
```

## Lab 01: Data Pipeline (Updated)

Labs 01_xx build the foundation for GraphRAG: loading data, generating embeddings, and extracting entities to create a knowledge graph.

### Step 1: Basic Data Loading

Create Document and Chunk nodes in Neo4j:

```bash
uv run python -m solutions.01_01_data_loading
```

This demonstrates basic data ingestion patterns.

### Step 2: Generate Embeddings

Generate vector embeddings using AWS Bedrock Titan:

```bash
uv run python -m solutions.01_02_embeddings
```

This creates embeddings for semantic search capabilities.

### Step 3: Entity Extraction

Build the knowledge graph using `SimpleKGPipeline`:

```bash
uv run python -m solutions.01_03_entity_extraction
```

This extracts entities and relationships from your documents.

### Step 4: Query the Full Dataset

Run queries against the populated knowledge graph:

```bash
uv run python -m solutions.01_04_full_dataset_queries
```

### Full Data Load (Optional)

Process all SEC 10-K PDFs with `SimpleKGPipeline` + Bedrock:

```bash
# Test with just 1 PDF first
uv run python -m solutions.01_full_data_load --limit 1

# Process all PDFs
uv run python -m solutions.01_full_data_load
```

> **Note:** This requires SEC 10-K PDFs in `~/projects/workshops/workshop-financial-data/form10k-sample/`. Uses `SimpleKGPipeline` with `BedrockLLM` (Claude) and `BedrockEmbeddings` (Titan V2).

## Additional Labs (Reference)

### Retrievers (02_xx)

Explore different retrieval strategies for GraphRAG.

```bash
# 02_01: Vector retriever - semantic search with VectorRetriever
uv run python -m solutions.02_01_vector_retriever

# 02_02: Vector + Cypher - enrich results with graph traversal
uv run python -m solutions.02_02_vector_cypher_retriever

# 02_03: Text2Cypher - natural language to Cypher queries
uv run python -m solutions.02_03_text2cypher_retriever
```

### Agents (03_xx)

Build AI agents with Neo4j tools.

```bash
# 03_01: Simple agent - schema retrieval tool
uv run python -m solutions.03_01_simple_agent

# 03_02: Vector + graph agent - semantic search with graph context
uv run python -m solutions.03_02_vector_graph_agent

# 03_03: Multi-tool agent - schema, vector, and Text2Cypher tools
uv run python -m solutions.03_03_text2cypher_agent
```

### Advanced Search (05_xx)

Fulltext and hybrid search patterns.

```bash
# 05_01: Fulltext search - keyword-based entity search
uv run python -m solutions.05_01_fulltext_search

# 05_02: Hybrid search - combine vector and fulltext
uv run python -m solutions.05_02_hybrid_search
```

## Architecture

- **AWS Bedrock** - LLM and embeddings (Claude, Titan)
- **neo4j-graphrag-python** - GraphRAG retrievers and pipelines (local fork)
- **Neo4j** - Graph database with vector search

## File Structure

```
new-workshops/
├── pyproject.toml              # Dependencies (uses local neo4j-graphrag fork)
├── .env                        # Configuration (not committed)
├── README.md
└── solutions/
    ├── __init__.py
    ├── config.py               # Shared configuration
    ├── test_connection.py      # Connection test
    ├── 01_01_data_loading.py   # Demo: basic data loading
    ├── 01_02_embeddings.py
    ├── 01_03_entity_extraction.py
    ├── 01_04_full_dataset_queries.py
    ├── 01_full_data_load.py    # Full PDF processing with SimpleKGPipeline
    ├── 02_01_vector_retriever.py
    ├── 02_02_vector_cypher_retriever.py
    ├── 02_03_text2cypher_retriever.py
    ├── 03_01_simple_agent.py
    ├── 03_02_vector_graph_agent.py
    ├── 03_03_text2cypher_agent.py
    ├── 05_01_fulltext_search.py
    └── 05_02_hybrid_search.py
```
