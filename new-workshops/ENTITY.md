# Entity Extraction Migration to AWS Bedrock

This document describes the completed migration of the entity extraction solution file to use AWS Bedrock with Claude Sonnet 4.5.

---

## Summary

The entity extraction solution now uses AWS Bedrock with Claude Sonnet 4.5 via cross-region inference profiles. The migration required only configuration changes while leaving the core pipeline logic untouched.

---

## Implementation Details

### BedrockLLM Integration

The neo4j-graphrag-python library (local fork) includes a native BedrockLLM class that:

- Implements both LLMInterface and LLMInterfaceV2, ensuring compatibility with all neo4j-graphrag components
- Uses the AWS Converse API for model-agnostic invocation
- Supports tool calling, which SimpleKGPipeline uses for structured entity extraction
- Includes both synchronous and asynchronous methods
- Has built-in rate limit handling with exponential backoff

### Inference Profiles Required

As of 2025, Anthropic Claude models on Bedrock require inference profiles for the Converse API. Direct model ID invocation is no longer supported for on-demand throughput. The implementation uses the US cross-region inference profile.

The inference profile ID format follows the pattern: region-prefix.provider.model-version

For Claude Sonnet 4.5, the US inference profile is: us.anthropic.claude-sonnet-4-5-20250929-v1:0

Cross-region inference profiles provide automatic request routing across multiple AWS regions, enabling applications to handle traffic bursts seamlessly and achieve higher throughput.

### Configuration

The AWSConfig class now uses bedrock_inference_profile_id instead of bedrock_model_id. This can be overridden via the AWS_BEDROCK_INFERENCE_PROFILE_ID environment variable.

The get_llm function returns a BedrockLLM instance configured with the inference profile and region from AWSConfig.

---

## Changes Made

### config.py

Added import for BedrockLLM from neo4j_graphrag.llm.

Updated AWSConfig to use bedrock_inference_profile_id field with default value of us.anthropic.claude-sonnet-4-5-20250929-v1:0.

Added get_llm function that returns a BedrockLLM instance configured with the inference profile.

### 01_03_entity_extraction.py

Changed embedder.model to embedder.model_id to match the BedrockEmbeddings attribute name.

---

## Test Results

The migration was tested successfully. Running the entity extraction script produced:

### Entities Extracted

Company: Apple Inc.

Products: iPhone, iPhone 14 Pro, iPhone 14, iPhone 13, iPhone SE, Mac, iPad, smartphones, personal computers, tablets, wearables, accessories

Services: Advertising, AppleCare, Cloud Services, Digital Content, Payment Services, Apple Card, Apple Pay

### Relationships Extracted

Twelve OFFERS_PRODUCT relationships connecting Apple Inc. to its products.

Seven OFFERS_SERVICE relationships connecting Apple Inc. to its services.

Twenty FROM_CHUNK relationships linking entities to their source text.

### Graph Statistics

Total nodes: 22 entities plus 1 Document and 1 Chunk node.

The extraction completed in under sixty seconds using Claude Sonnet 4.5.

---

## Available Inference Profiles

For reference, these are the Anthropic Claude inference profile IDs available on Bedrock:

Claude Sonnet 4.5: us.anthropic.claude-sonnet-4-5-20250929-v1:0, eu.anthropic.claude-sonnet-4-5-20250929-v1:0, global.anthropic.claude-sonnet-4-5-20250929-v1:0

Claude Sonnet 4: us.anthropic.claude-sonnet-4-20250514-v1:0, apac.anthropic.claude-sonnet-4-20250514-v1:0, eu.anthropic.claude-sonnet-4-20250514-v1:0

Claude 3.5 Sonnet v2: us.anthropic.claude-3-5-sonnet-20241022-v2:0, apac.anthropic.claude-3-5-sonnet-20241022-v2:0

Claude Haiku 4.5: us.anthropic.claude-haiku-4-5-20251001-v1:0, eu.anthropic.claude-haiku-4-5-20251001-v1:0

---

## Next Steps

The remaining solution files can now be migrated since they follow the same pattern of importing LLM and embedder from config:

- 02_01_vector_retriever.py through 02_03_text2cypher_retriever.py
- 03_01_simple_agent.py through 03_03_text2cypher_agent.py

These files will work without modification once they import get_llm and get_embedder from the updated config module.

---

## References

- [AWS Bedrock Inference Profiles Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html)
- [Introducing Claude Sonnet 4.5 in Amazon Bedrock](https://aws.amazon.com/blogs/aws/introducing-claude-sonnet-4-5-in-amazon-bedrock-anthropics-most-intelligent-model-best-for-coding-and-complex-agents/)
- [Cross-Region Inference on Amazon Bedrock](https://aws.amazon.com/blogs/machine-learning/unlock-global-ai-inference-scalability-using-new-global-cross-region-inference-on-amazon-bedrock-with-anthropics-claude-sonnet-4-5/)
