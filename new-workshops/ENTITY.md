# Proposal: Migrating Entity Extraction to AWS Bedrock

This document proposes how to migrate the entity extraction solution file to use AWS Bedrock, completing Phase 3 of the migration plan outlined in DATA_LOADING.md.

---

## Executive Summary

With the BedrockLLM implementation now complete in the neo4j-graphrag-python library, the entity extraction solution can be migrated to AWS Bedrock. This migration mirrors the successful pattern established with BedrockEmbeddings in Phase 2, requiring only configuration changes while leaving the core pipeline logic untouched.

---

## Current State

### What the Entity Extraction File Does

The solution file demonstrates building a knowledge graph from SEC 10-K filing text using the SimpleKGPipeline from neo4j-graphrag. It performs:

- Entity extraction identifying Companies, Products, and Services
- Relationship extraction for OFFERS_PRODUCT and OFFERS_SERVICE connections
- Graph population with chunks linked to extracted entities
- Query demonstrations showing the resulting knowledge graph

### Current Dependencies

The file imports an LLM and embedder from the shared config module. While the embedder has been migrated to BedrockEmbeddings, the config module does not yet provide a get_llm function. The solution file expects this function to exist and return an LLM compatible with SimpleKGPipeline.

---

## Proposed Migration

### BedrockLLM Is Now Available

The neo4j-graphrag-python library (local fork) now includes a native BedrockLLM class. This class:

- Implements both LLMInterface and LLMInterfaceV2, ensuring compatibility with all neo4j-graphrag components
- Uses the AWS Converse API for model-agnostic invocation
- Supports tool calling, which SimpleKGPipeline uses for structured entity extraction
- Includes both synchronous and asynchronous methods
- Has built-in rate limit handling with exponential backoff

### Model Selection

The BedrockLLM defaults to Claude Sonnet 4.5, which is the latest Claude model available on Bedrock. However, for cost-effectiveness in entity extraction tasks, Claude 3.5 Sonnet v2 remains a strong choice. The model can be configured via the AWS_BEDROCK_MODEL_ID environment variable.

Claude 3.5 Sonnet v2 offers:
- Direct invocation without requiring inference profiles
- 200K token context window
- Strong structured extraction capabilities
- Lower cost per token compared to newer models

### Integration Pattern

The migration follows the same pattern established for embeddings. The config module needs a new get_llm function that returns a BedrockLLM instance. This function should:

- Use the AWS region from the existing AWSConfig class
- Use the model ID from the existing bedrock_model_id field in AWSConfig
- Allow boto3 to resolve credentials through its standard chain

The entity extraction file already imports get_llm from config, so once the config module provides this function, no changes to the solution file itself are required.

---

## Implementation Steps

### Step One: Update the Config Module

Add a get_llm function to config.py that imports BedrockLLM from neo4j_graphrag.llm and returns an instance configured with the region and model ID from AWSConfig. The import path mirrors the embeddings pattern.

### Step Two: Verify the Import Works

Run a quick test to ensure BedrockLLM imports successfully from the local fork. This confirms the dependency is properly installed.

### Step Three: Test Entity Extraction

Run the entity extraction solution against a Neo4j instance. The expected behavior:

- LLM initializes and reports its model name
- Embedder initializes with Amazon Titan V2
- SimpleKGPipeline creates successfully
- Entity extraction completes (typically thirty to sixty seconds for the sample text)
- Graph shows Company, Product, and Service nodes with relationships

### Step Four: Validate Graph Structure

Query the resulting graph to verify:

- Apple is created as a Company node
- Products like iPhone, Mac, and iPad are extracted
- Services like AppleCare and Apple Pay are extracted
- OFFERS_PRODUCT and OFFERS_SERVICE relationships connect Apple to its products and services
- Chunks are linked to entities via FROM_CHUNK relationships

---

## Technical Considerations

### Converse API Benefits

The BedrockLLM uses the Converse API rather than model-specific invoke methods. This provides:

- Consistent interface across all Bedrock models
- Native tool calling support matching what SimpleKGPipeline expects
- Automatic retry handling built into the SDK
- Future-proofing if models are swapped

### Async Support

The entity extraction solution uses pipeline.run_async, which requires async LLM support. BedrockLLM implements ainvoke and ainvoke_with_tools by running synchronous boto3 calls in an executor, since boto3 does not have native async support. This approach works correctly with asyncio.

### Error Handling

BedrockLLM wraps all API errors in LLMGenerationError, which SimpleKGPipeline handles gracefully when configured with on_error set to IGNORE. This matches the current solution configuration.

---

## What Does Not Change

The migration is designed to be minimally invasive. These elements remain identical:

- Sample text content
- Schema definition (entity types, relationship types, patterns)
- SimpleKGPipeline configuration
- Graph query logic for displaying results
- All Cypher queries

The only changes are in the config module. The solution file itself requires no modifications.

---

## Expected Results

After migration, running the entity extraction should produce output similar to:

Connected to Neo4j successfully, cleared previous nodes, initialized LLM with the configured Bedrock model, initialized embedder with Amazon Titan V2, created pipeline, ran extraction for thirty to sixty seconds, then displayed entity counts showing one Company, several Products, and several Services, along with the extracted relationships connecting Apple to its products and services.

The graph structure will be identical to what the Azure version produces, with the only difference being the embedding dimensions (1024 for Titan V2 versus 1536 for Azure OpenAI).

---

## Dependencies Already in Place

The pyproject.toml already includes:

- The local neo4j-graphrag fork with Bedrock support enabled
- boto3 and botocore for AWS SDK access
- The hatch metadata setting allowing direct references

The AWSConfig class already defines:

- AWS region defaulting to us-east-1
- Bedrock model ID defaulting to Claude 3.5 Sonnet v2
- Bedrock embedding model ID for Titan V2

No new dependencies or configuration fields are required.

---

## Relationship to Other Migration Phases

This migration completes Phase 3 from DATA_LOADING.md. With both BedrockEmbeddings and BedrockLLM available:

- Phase 1 (install dependencies) was completed previously
- Phase 2 (embeddings migration for 01_02) was completed previously
- Phase 3 (BedrockLLM implementation) is now complete
- Phase 4 (update config module) is described in this proposal
- Phase 5 (migrate remaining files) can proceed after this migration

Once the config module is updated, the remaining solution files (02_xx retrievers and 03_xx agents) can also be migrated since they follow the same pattern of importing LLM and embedder from config.

---

## Conclusion

Migrating entity extraction to Bedrock is straightforward because the neo4j-graphrag library now provides native support for both embeddings and LLM via Bedrock. The migration requires only adding a get_llm function to the config module. The SimpleKGPipeline, schema definitions, and graph queries work identically regardless of which LLM provider is used.

This follows the library's intended design pattern where providers are swappable without changing application logic.
