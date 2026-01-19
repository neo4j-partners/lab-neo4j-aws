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
```

The workshop uses sensible defaults for AWS Bedrock models. You can optionally override them:

```
AWS_BEDROCK_INFERENCE_PROFILE_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
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

Build the knowledge graph using SimpleKGPipeline:

```bash
uv run python -m solutions.01_03_entity_extraction
```

This is the core of the GraphRAG pipeline. It uses Claude Sonnet 4.5 on AWS Bedrock to read text and identify entities and relationships, then stores them in Neo4j as a knowledge graph.

#### What It Does

The entity extraction pipeline takes unstructured text and transforms it into structured graph data. For example, given SEC 10-K filing text about Apple, it identifies:

**Entities** are the things mentioned in the text. The pipeline extracts three types:
- Companies such as Apple Inc.
- Products such as iPhone, Mac, iPad, and their variants
- Services such as AppleCare, Apple Pay, and Cloud Services

**Relationships** describe how entities connect to each other:
- OFFERS_PRODUCT links a company to the products it sells
- OFFERS_SERVICE links a company to the services it provides

**Provenance** tracks where information came from. Each entity links back to the text chunk it was extracted from via FROM_CHUNK relationships. This enables you to trace any fact in the graph back to its source document.

#### How It Works

The SimpleKGPipeline orchestrates the extraction process:

1. The text is split into manageable chunks
2. Each chunk is sent to Claude Sonnet 4.5 with a schema describing what entities and relationships to look for
3. Claude reads the text and returns structured JSON with the entities and relationships it found
4. The pipeline creates nodes and relationships in Neo4j for each extracted item
5. Embeddings are generated for each entity using Amazon Titan, enabling semantic search

#### Schema-Driven Extraction

The extraction is guided by a schema you define. The schema tells the LLM what types of entities to look for, what relationships are valid, and which entity types can connect to which. This keeps the extraction focused and consistent.

For the SEC 10-K example, the schema specifies that Companies can offer Products and Services, but Products cannot offer other Products. This prevents the LLM from creating nonsensical relationships.

#### Expected Results

Running the extraction on the sample Apple 10-K text produces:
- One Company node for Apple Inc.
- Twelve Product nodes including iPhone models, Mac, iPad, and general categories
- Seven Service nodes including AppleCare, Apple Pay, and Cloud Services
- Nineteen relationships connecting Apple to its products and services
- Twenty provenance links connecting entities to their source chunk

The extraction typically completes in under sixty seconds.

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

- **AWS Bedrock** - LLM (Claude 4.5 Sonnet via inference profile) and embeddings (Titan V2)
- **neo4j-graphrag-python** - GraphRAG retrievers and pipelines (local fork)
- **Neo4j** - Graph database with vector search

## AWS Bedrock Configuration

### Inference Profiles vs Direct Model Access

AWS Bedrock offers two ways to invoke models:

| Approach | Description | Use Case |
|----------|-------------|----------|
| **Direct Model Access** | Invoke models directly in a single Region | Simple single-Region inference |
| **Inference Profiles** | Define model + Regions for routing requests | Cost tracking, metrics, cross-Region |

**Why Claude 4.5 Sonnet requires an inference profile:**

Newer models like Claude 4.5 Sonnet only support inference profile access (not direct on-demand). This provides:

- **Usage Metrics**: CloudWatch logs for model invocation metrics
- **Cost Tracking**: Attach tags for billing analysis with AWS cost allocation
- **Cross-Region Inference**: Distribute requests across multiple AWS Regions for increased throughput
- **Resilience**: Failover capabilities across Regions

### Regional Inference Profile IDs

| Region | Inference Profile ID |
|--------|---------------------|
| US | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| EU | `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| APAC | `apac.anthropic.claude-sonnet-4-5-20250929-v1:0` |

### Model Configuration Example

```python
from neo4j_graphrag.llm import BedrockLLM

llm = BedrockLLM(
    model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    inference_profile_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="us-east-1",
    model_params={
        "maxTokens": 4096,
        "temperature": 0,  # Use 0 for deterministic entity extraction
    },
)
```

### Best Practices

1. **Use the Converse API**: Write code once and switch between models easily. The `BedrockLLM` class uses Converse internally.

2. **Temperature Settings**:
   - Use `temperature: 0` for entity extraction and structured outputs
   - Use `temperature: 0.7-1.0` for creative/conversational tasks
   - Note: Claude 4.5 only supports `temperature` OR `top_p`, not both

3. **Extended Thinking** (for complex reasoning):
   ```python
   model_params={
       "maxTokens": 20000,
       "thinking": {"type": "enabled", "budget_tokens": 16000},
   }
   ```
   Do not set `temperature`, `topP`, or `topK` when using extended thinking.

4. **Pricing**: Costs are calculated based on the price in the Region from which you call the inference profile.

### Sources

- [AWS Bedrock Inference Profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
- [Supported Regions and Models](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html)
- [Claude Model Parameters](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)
- [Introducing Claude Sonnet 4.5 in Amazon Bedrock](https://aws.amazon.com/blogs/aws/introducing-claude-sonnet-4-5-in-amazon-bedrock-anthropics-most-intelligent-model-best-for-coding-and-complex-agents/)
- [Optimizing Claude Models on Bedrock](https://repost.aws/articles/ARRfe9jE4dQmK8Y2oMYMqbfQ/how-to-optimize-workload-performance-when-using-anthropic-claude-models-on-bedrock)

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
