# Embedding Provider Plan

Make the embedding system modular so it can support OpenAI, Azure, and AWS Bedrock.

---

## What we had before Phase 1

- Two config files that did the same thing: `src/config.py` and `solution_srcs/config.py`
- Both hardcoded `OpenAIEmbeddings` from neo4j-graphrag as the only embedder
- Azure worked because Azure AI Foundry exposes an OpenAI-compatible endpoint (same class, different base_url)
- The vector index dimension was hardcoded to 1536 in `schema.py:103`
- The solution demo `01_02_embeddings.py` also hardcoded 1536 dimensions
- Env vars were OpenAI/Azure-specific: `AZURE_AI_EMBEDDING_NAME`, `OPENAI_API_KEY`, `AZURE_AI_PROJECT_ENDPOINT`
- No provider abstraction — `get_embedder()` just returned `OpenAIEmbeddings` directly

## What needs to change

We need a single `get_embedder()` that picks the right provider based on which env vars are set, and returns a consistent interface that the rest of the code doesn't need to know about. Each provider has different auth, different SDKs, and different output dimensions.

| Provider | SDK | Auth | Model example | Dimensions |
|----------|-----|------|---------------|------------|
| OpenAI | openai (via neo4j-graphrag) | API key | text-embedding-3-small | 1536 |
| Azure | openai (via neo4j-graphrag) | az login token | text-embedding-3-small | 1536 |
| Bedrock | neo4j-graphrag (`BedrockEmbeddings`) | AWS credentials | amazon.titan-embed-text-v2:0 | 1024 |

---

## Phase 1 — Clean up and make embeddings modular [DONE]

The goal was to get the existing code ready so adding a new provider is just adding one new file and one new env var block. No behavior changes — OpenAI and Azure work exactly as they did before.

### What was done

1. **[DONE] Added `EMBEDDING_PROVIDER` (required) and `EMBEDDING_DIMENSIONS` env vars to `.env.sample`**
   - `EMBEDDING_PROVIDER` is required — no auto-detection. Values: `openai`, `azure`, `bedrock`
   - Existing `.env` files must be updated to include `EMBEDDING_PROVIDER=azure` (or `openai`)
   - Added placeholder for Bedrock env vars (`AWS_REGION`, `EMBEDDING_MODEL_ID`)

2. **[DONE] Created `src/embeddings/` package**
   - `src/embeddings/__init__.py` — exports `get_embedder()` and `get_embedding_dimensions()`; validates `EMBEDDING_PROVIDER` is set
   - `src/embeddings/openai.py` — OpenAI embedder using `OPENAI_API_KEY`
   - `src/embeddings/azure.py` — Azure embedder with `get_azure_token()` (moved from `src/config.py`)
   - `src/embeddings/bedrock.py` — stub that raises `NotImplementedError` (Phase 2)

3. **[DONE] Updated `src/config.py`**
   - `embedding_provider` is a required `str` field on `AgentConfig` (not optional)
   - Added optional `embedding_dimensions` field
   - `get_embedder()` now delegates to `src.embeddings`
   - `get_azure_token()` now delegates to `src.embeddings.azure`
   - `get_llm()` and `connect()` unchanged

4. **[DONE] Updated `src/schema.py`**
   - `create_embedding_indexes()` now reads dimensions from config via `get_embedding_dimensions()` instead of defaulting to 1536
   - Still accepts an explicit `dimensions` parameter for callers that need to override

5. **[DONE] Updated `solution_srcs/config.py`**
   - Removed duplicate `AgentConfig` class — now re-exports from `src.config`
   - `get_embedder()` delegates to `src.embeddings`
   - `_get_azure_token()` delegates to `src.embeddings.azure`
   - `get_llm()`, `get_neo4j_driver()`, `get_agent_config()` kept for solution file compatibility

6. **[DONE] Updated `solution_srcs/01_02_embeddings.py`**
   - `create_index()` now reads dimensions from `src.embeddings.get_embedding_dimensions()` instead of hardcoding 1536

7. **[DONE] Updated `src/pipeline.py`**
   - Print output now shows the resolved provider name instead of assuming Azure

8. **[DONE] Updated `.env` to add `EMBEDDING_PROVIDER=azure`**

### Files changed

| File | Change |
|------|--------|
| `.env.sample` | Added `EMBEDDING_PROVIDER`, `EMBEDDING_DIMENSIONS`, Bedrock placeholders |
| `src/embeddings/__init__.py` | New — provider router, `get_embedder()`, `get_embedding_dimensions()` |
| `src/embeddings/openai.py` | New — OpenAI `create_embedder()` |
| `src/embeddings/azure.py` | New — Azure `create_embedder()` + `get_azure_token()` |
| `src/embeddings/bedrock.py` | New — stub for Phase 2 |
| `src/config.py` | Added `embedding_provider`/`embedding_dimensions` fields; `get_embedder()` delegates to embeddings pkg |
| `src/schema.py` | `create_embedding_indexes()` reads dimensions from config |
| `src/pipeline.py` | Provider-aware print output |
| `solution_srcs/config.py` | Removed duplicated `AgentConfig` and embedder logic; delegates to `src` |
| `solution_srcs/01_02_embeddings.py` | Config-driven dimensions |

---

## Phase 2 — Add Bedrock Titan v2 via neo4j-graphrag [DONE]

### Decision: Titan v2, not Nova

The original plan targeted `amazon.nova-embed-v1:0`, but investigation showed:
- Amazon Nova Multimodal Embeddings (`amazon.nova-2-multimodal-embeddings-v1:0`) uses an **async-only API** (`StartAsyncInvoke`) that writes results to S3
- The `SimpleKGPipeline` calls `embed_query()` synchronously per chunk, requiring the standard `invoke_model` API
- Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`) supports synchronous `invoke_model` and is already the default in neo4j-graphrag's `BedrockEmbeddings` class

### Decision: neo4j-graphrag BedrockEmbeddings, not custom boto3

The neo4j-graphrag library already has a fully tested `BedrockEmbeddings` class that:
- Extends the same `Embedder` interface used by the pipeline
- Handles rate limiting with exponential backoff
- Supports cross-region inference profiles
- Defaults to `amazon.titan-embed-text-v2:0`

No reason to duplicate this with a raw boto3 wrapper.

### What was done

1. **[DONE] Implemented `src/embeddings/bedrock.py`**
   - Uses `BedrockEmbeddings` from neo4j-graphrag (not a custom boto3 wrapper)
   - Reads `AWS_REGION` and `EMBEDDING_MODEL_ID` from config
   - `EMBEDDING_MODEL_ID` is optional — omitting it uses the library default (`amazon.titan-embed-text-v2:0`)
   - Auth via standard boto3 credential chain (env vars, `~/.aws/credentials`, IAM role)

2. **[DONE] Added `aws_region` and `embedding_model_id` fields to `AgentConfig`**
   - `AWS_REGION` — passed explicitly to `BedrockEmbeddings(region_name=...)` for consistency with how other providers flow through AgentConfig
   - `EMBEDDING_MODEL_ID` — only passed when explicitly set; otherwise the library default is used

3. **[DONE] Updated `.env.sample`**
   - Fixed model ID from `amazon.nova-embed-v1:0` to `amazon.titan-embed-text-v2:0`
   - Noted that `EMBEDDING_MODEL_ID` is optional
   - Updated dimension comment to reference Titan v2

4. **[DONE] Documented in `README.md`**
   - Added "Embedding Providers" section with provider comparison table
   - Explained Bedrock configuration and why Titan v2 was chosen over Nova
   - Documented dimension compatibility between providers

### Files changed

| File | Change |
|------|--------|
| `src/embeddings/bedrock.py` | Replaced stub with `BedrockEmbeddings` from neo4j-graphrag |
| `src/config.py` | Added `aws_region` and `embedding_model_id` optional fields to `AgentConfig` |
| `.env.sample` | Fixed model ID default, updated comments |
| `README.md` | Added Embedding Providers section |

### Wiring (unchanged from Phase 1)

These were already in place and required no changes:
- `src/embeddings/__init__.py` — routes `bedrock` to `bedrock.create_embedder()`
- `get_embedding_dimensions()` — defaults to 1024 for bedrock provider

### TODO

- **Test end-to-end** with Bedrock config: `uv run python main.py load --clear` → `verify`
- Run solution demos to confirm they work with the Bedrock provider
