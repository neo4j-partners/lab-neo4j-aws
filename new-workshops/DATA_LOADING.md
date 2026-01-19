# Proposal: Migrating Data Loading Solutions to AWS Bedrock

This document proposes how the solution files in `new-workshops/solutions/` (specifically `01_01_data_loading.py` through `01_04_full_dataset_queries.py`) could be restructured to run on AWS using Amazon Bedrock.

---

## Executive Summary

The current solution files use Microsoft Azure Foundry for LLM and embedding services. This proposal outlines how to migrate these solutions to use AWS Bedrock, taking advantage of the latest 2025-2026 AWS best practices. The key advantage of AWS Bedrock is that **no model deployment is required**—all foundation models are available on-demand as serverless APIs, eliminating infrastructure management overhead.

---

## Current State Analysis

### What the Solution Files Do Today

| File | Purpose | AI Dependencies |
|------|---------|-----------------|
| `01_01_data_loading.py` | Basic document and chunk loading into Neo4j | None (pure Cypher) |
| `01_02_embeddings.py` | Text chunking and embedding generation with vector search | Embeddings model |
| `01_03_entity_extraction.py` | Entity and relationship extraction using LLM | LLM + Embeddings |
| `01_04_full_dataset_queries.py` | Exploration queries on populated graph | Embeddings (for search) |

### Current Azure Configuration

The solutions currently rely on Azure AI Foundry endpoints configured via environment variables, using OpenAI-compatible APIs for both embeddings and LLM calls. Authentication uses Azure CLI credentials.

---

## Proposed AWS Architecture

### Why AWS Bedrock Is Ideal

**Serverless, On-Demand Foundation Models**

As of late 2025, Amazon Bedrock provides immediate access to all serverless foundation models by default. Users no longer need to manually enable model access through a dashboard—models are available out of the box with standard IAM permissions. This dramatically simplifies setup and reduces time-to-first-call.

**Key Benefits:**
- No model deployment, provisioning, or infrastructure management required
- Pay only for tokens processed (on-demand pricing)
- Consistent APIs across all supported models
- Automatic scaling and high availability built in

### Recommended Model Selections

**For Embeddings: Amazon Titan Text Embeddings V2**

Amazon Titan Text Embeddings V2 is purpose-built for retrieval applications and knowledge graph construction. Key capabilities:

- Flexible output dimensions: 1024 (default), 512 (balanced), or 256 (storage efficient)
- Supports up to 8,192 tokens per request
- Maintains 97-99% retrieval accuracy even at smaller dimensions
- Multilingual support for over 100 languages
- Built-in normalization for cosine similarity searches

Best practice: Use 1024 dimensions during development for maximum accuracy, then consider reducing to 512 for production if storage or latency becomes a concern.

**For Entity Extraction: Claude 3.5 Sonnet v2**

Claude 3.5 Sonnet v2 is recommended as the default model for entity extraction. It provides an excellent balance of capability and cost, and can be invoked directly without requiring inference profiles.

- Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Access: Direct on-demand invocation (no inference profile required)
- Context window: 200K tokens

Note: While Anthropic models are enabled by default on Bedrock, a one-time usage form submission is required before first use.

### The Converse API Advantage

AWS recommends using the Converse API for all LLM interactions. The Converse API provides a unified interface that works consistently across all Bedrock models, meaning code written once will work with different models without modification.

Key features:
- Consistent message format across all providers
- Built-in tool/function calling support
- Automatic retry handling (up to 5 retries)
- Support for streaming responses via ConverseStream
- Document processing support (up to 10MB per document)

---

## Integration Pattern: Native Library Support

### BedrockEmbeddings — Native Support in neo4j-graphrag

The neo4j-graphrag-python library has been extended with native AWS Bedrock support for embeddings. This means **no custom wrapper class is needed for embeddings**.

**Installation (Development — Local Fork):**

The Bedrock support is currently in a local fork. The project uses `uv` for dependency management.

1. Update `pyproject.toml`:
   ```toml
   # Using local fork with Bedrock support
   "neo4j-graphrag[bedrock] @ file:///Users/ryanknight/projects/neo4j-graphrag-python",
   ```

2. Add to `pyproject.toml` (required for direct references):
   ```toml
   [tool.hatch.metadata]
   allow-direct-references = true
   ```

3. Install:
   ```bash
   uv sync
   ```

> **Note:** After full testing, the dependency can be changed to install from Git:
> ```toml
> "neo4j-graphrag[bedrock] @ git+https://github.com/OWNER/neo4j-graphrag-python.git@bedrock-support"
> ```

**Bedrock Integration Verified:**
- AWS CLI is configured and working
- Bedrock API access tested successfully in `/tmp/bedrock-test/`
- BedrockEmbeddings generates 1024-dimension vectors correctly

**Usage:**
```python
from neo4j_graphrag.embeddings import BedrockEmbeddings

# Basic usage - boto3 reads credentials from environment
embedder = BedrockEmbeddings(region_name="us-east-1")

# With custom model (default is amazon.titan-embed-text-v2:0)
embedder = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v2:0",
    region_name="us-east-1"
)

# Generate embedding
embedding = embedder.embed_query("What products does Apple make?")
```

**Key Features:**
- Default model: `amazon.titan-embed-text-v2:0`
- Automatic AWS credential resolution via boto3
- Support for inference profiles via `inference_profile_id` parameter
- Built-in rate limit handling with exponential backoff
- Follows the same pattern as other providers (OpenAI, Cohere, VertexAI)

### BedrockLLM — Proposed Extension to neo4j-graphrag

The neo4j-graphrag library does **not** currently include a native Bedrock LLM provider. A proposal has been written to add this capability.

**Proposal Document:** See `BEDROCK_LLM.md` in the neo4j-graphrag-python repository for the full proposal.

**Summary:**

The proposed `BedrockLLM` class would:
- Implement `LLMInterfaceV2` (the current, non-deprecated interface)
- Use the Converse API for model-agnostic invocation across all Bedrock models
- Support tool/function calling (Converse API has native support)
- Default to Claude 3.5 Sonnet v2 for entity extraction
- Handle message formatting and response parsing
- Support configurable temperature and max tokens

**Why Converse API:**
- Unified interface across Claude, Titan, Llama, Mistral, and other Bedrock models
- Native tool calling support for structured extraction
- Automatic retry handling (up to 5 retries)
- No need for model-specific request formatting

This follows the library's existing provider pattern and ensures compatibility with `SimpleKGPipeline`, `Text2CypherRetriever`, and other components.

---

## Migration Plan by Solution File

### 01_01_data_loading.py — No Changes Required

This file performs pure Neo4j operations (creating Document and Chunk nodes, establishing relationships) without any AI service calls. It will work identically with no modifications needed.

### 01_02_embeddings.py — Use Native BedrockEmbeddings

**Current approach:** Uses Azure OpenAI Embeddings via OpenAI-compatible endpoint

**Proposed approach:** Use the native `BedrockEmbeddings` class from neo4j-graphrag

The migration involves:
1. Update `pyproject.toml` with local fork and run `uv sync`
2. Replace the Azure embedder import with `from neo4j_graphrag.embeddings import BedrockEmbeddings`
3. Update instantiation to use `BedrockEmbeddings(region_name="us-east-1")`
4. Change vector index dimensions from 1536 to 1024 (Titan V2)
5. The vector index creation and similarity search logic remains unchanged

**Status:** ✅ Migration complete. See Phase 2 in Implementation Recommendations.

**Best practice considerations:**
- Segment documents into logical paragraphs before embedding (current chunking approach is correct)
- Titan V2 returns normalized embeddings by default, ideal for cosine similarity
- Consider batch inference for large datasets to reduce costs by 50%

**This file is the first migration target** — it validates the Bedrock embeddings integration before tackling LLM-dependent files.

### 01_03_entity_extraction.py — Replace LLM and Embedder

**Current approach:** Uses Azure OpenAI via OpenAI-compatible endpoint for both LLM and embeddings

**Proposed approach:** Use Claude 3.5 Sonnet v2 via custom BedrockLLM + native BedrockEmbeddings

The migration involves:
1. Use native `BedrockEmbeddings` for embeddings
2. Create a custom `BedrockLLM` class implementing `LLMInterface`
3. The SimpleKGPipeline and schema definitions remain unchanged
4. Entity types, relationship types, and patterns work identically

The neo4j-graphrag library's `SimpleKGPipeline` accepts any LLM and embedder that implements the required interfaces, making this swap straightforward.

### 01_04_full_dataset_queries.py — Use Native BedrockEmbeddings

**Current approach:** Uses Azure embeddings for vector similarity search

**Proposed approach:** Use native `BedrockEmbeddings` from neo4j-graphrag

This file is primarily Cypher queries with one AI dependency: generating query embeddings for vector search. The migration simply requires swapping to the native embedder, with all query logic remaining identical.

---

## Configuration Strategy

### Environment Variables

The AWS version should use these environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `AWS_REGION` | Bedrock service region | `us-east-1` |
| `AWS_BEDROCK_MODEL_ID` | LLM model for entity extraction | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `NEO4J_URI` | Neo4j connection string | (required) |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | (required) |

Note: The embedding model ID does not need configuration as `BedrockEmbeddings` defaults to `amazon.titan-embed-text-v2:0`.

### Authentication

AWS credentials are resolved automatically by boto3 through any standard method:
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- AWS credentials file (`~/.aws/credentials`)
- IAM roles (when running in AWS infrastructure)
- AWS SSO / Identity Center
- Named profiles via `AWS_PROFILE`

For development environments like GitHub Codespaces, environment variables or AWS SSO are typically most practical.

---

## AWS Bedrock Best Practices to Incorporate

### 2025 Serverless Model Access

Since September 2025, Bedrock has simplified model access by automatically enabling all serverless foundation models:
- No model enablement step required in the console
- Standard IAM permissions are sufficient
- Anthropic models require one-time usage form (can be completed via console or API)

### Claude 3.5 Sonnet v2 — Direct Invocation

Claude 3.5 Sonnet v2 can be invoked directly using its model ID without requiring inference profiles. This simplifies configuration compared to newer models like Claude Sonnet 4.5 which require inference profiles.

### Cost Optimization Strategies

1. Use on-demand pricing (no commitment, pay per token)
2. Claude 3.5 Sonnet v2 is more cost-effective than Claude Sonnet 4.5 for most entity extraction tasks
3. Use 512-dimension embeddings if retrieval accuracy at 99% is acceptable
4. Implement batch inference for processing large document sets (50% cost reduction)

### Error Handling

The Converse API includes automatic retry logic:
- The SDK retries up to 5 times automatically
- Model not ready errors are handled transparently
- Rate limiting is managed by the service

The native `BedrockEmbeddings` class includes built-in rate limit detection and retry with exponential backoff.

---

## Implementation Recommendations

### Phase 1: Install Dependencies ✅ COMPLETE

1. Update `pyproject.toml` to use local neo4j-graphrag fork with Bedrock support:
   ```toml
   # Using local fork with Bedrock support
   "neo4j-graphrag[bedrock] @ file:///Users/ryanknight/projects/neo4j-graphrag-python",
   ```
2. Add hatch metadata setting for direct references:
   ```toml
   [tool.hatch.metadata]
   allow-direct-references = true
   ```
3. Run `uv sync` to install dependencies

**Status:** Completed. BedrockEmbeddings imports successfully.

> **Note:** After full testing, the dependency can be changed to install from Git:
> ```toml
> "neo4j-graphrag[bedrock] @ git+https://github.com/OWNER/neo4j-graphrag-python.git@bedrock-support"
> ```

### Phase 2: Update and Test 01_02_embeddings.py ✅ COMPLETE

**First migration target** — validates Bedrock embeddings before tackling LLM-dependent files.

1. Update `new-workshops/solutions/config.py`:
   - Replace Azure imports with `from neo4j_graphrag.embeddings import BedrockEmbeddings`
   - Replace `AgentConfig` with `AWSConfig` for Bedrock settings
   - Update `get_embedder()` to return `BedrockEmbeddings(region_name=config.region)`
   - Remove Azure authentication code
2. Update `new-workshops/solutions/01_02_embeddings.py`:
   - Update docstring to reference AWS Bedrock
   - Change vector index dimensions from 1536 to 1024 (Titan V2)
3. Test Bedrock embeddings generation

**Status:** Completed. Test results:
```
Creating Bedrock embedder...
Embedder created: amazon.titan-embed-text-v2:0
Generating test embedding...
Embedding dimensions: 1024
First 5 values: [-0.0796, 0.0103, 0.0271, 0.0053, 0.0006]
SUCCESS!
```

**Pending:** Full script test requires Neo4j configuration (`.env` file with `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`).

### Phase 3: Create BedrockLLM Implementation

**Proposal:** See `/Users/ryanknight/projects/neo4j-graphrag-python/BEDROCK_LLM.md` for the full proposal to add BedrockLLM to neo4j-graphrag-python.

1. Create `BedrockLLM` class implementing the neo4j-graphrag `LLMInterfaceV2`
2. Use the Converse API for LLM calls (model-agnostic, recommended by AWS)
3. Implement tool calling support (Converse API supports this natively)
4. Support configurable model ID, temperature, and max tokens
5. Default to Claude 3.5 Sonnet v2: `anthropic.claude-3-5-sonnet-20241022-v2:0`

**Status:** Proposal written. Pending implementation in neo4j-graphrag-python.

### Phase 4: Update Configuration Module

1. Create a `config.py` that provides factory functions (`get_llm()`, `get_embedder()`)
2. Use `BedrockEmbeddings` from neo4j-graphrag directly for embeddings
3. Use custom `BedrockLLM` for LLM calls
4. Handle AWS credential resolution via boto3's default chain

### Phase 5: Migrate Remaining Solution Files

1. Update `01_03_entity_extraction.py` with BedrockLLM + BedrockEmbeddings
2. Update `01_04_full_dataset_queries.py` with BedrockEmbeddings
3. Maintain identical Neo4j operations and graph structures
4. Test with the same sample SEC 10-K text
5. Verify entity extraction and search results match expected behavior

### Phase 6: Documentation

Update documentation to reflect:
1. AWS credential setup requirements
2. One-time Anthropic usage form for Claude access
3. Expected costs for running the solutions
4. Troubleshooting common Bedrock errors

---

## Conclusion

Migrating the data loading solutions from Azure to AWS Bedrock is straightforward because:

1. **Native embeddings support** — The neo4j-graphrag library now includes `BedrockEmbeddings`, eliminating the need for custom embedding wrapper code.

2. **The core logic is model-agnostic** — Neo4j operations, chunking strategies, and graph schemas remain identical.

3. **Only LLM wrapper needed** — A custom `BedrockLLM` class implementing `LLMInterface` is the only custom code required. This follows the library's intended extension pattern.

4. **No deployment complexity** — Bedrock's serverless models eliminate infrastructure setup. Models are available immediately with just IAM permissions.

5. **Simpler model selection** — Claude 3.5 Sonnet v2 can be invoked directly without inference profiles, reducing configuration complexity.

The implementation follows a phased approach, starting with `01_02_embeddings.py` to validate the Bedrock embeddings integration before tackling LLM-dependent files.

---

## References

- [Amazon Bedrock Automatic Model Enablement (Oct 2025)](https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-bedrock-automatic-enablement-serverless-foundation-models/)
- [AWS Security Blog: Simplified Amazon Bedrock Model Access](https://aws.amazon.com/blogs/security/simplified-amazon-bedrock-model-access/)
- [Amazon Bedrock Converse API Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)
- [Amazon Titan Text Embeddings V2 Guide](https://aws.amazon.com/blogs/machine-learning/get-started-with-amazon-titan-text-embeddings-v2-a-new-state-of-the-art-embeddings-model-on-amazon-bedrock/)
- [neo4j-graphrag Python Package Documentation](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html)
- [neo4j-graphrag LLMInterface API](https://neo4j.com/docs/neo4j-graphrag-python/current/api.html)
- neo4j-graphrag BedrockEmbeddings: Local fork at `/Users/ryanknight/projects/neo4j-graphrag-python`
- [Amazon Bedrock Model Choice](https://aws.amazon.com/bedrock/model-choice/)
- [Amazon Bedrock Pricing Guide](https://www.nops.io/blog/amazon-bedrock-pricing/)
