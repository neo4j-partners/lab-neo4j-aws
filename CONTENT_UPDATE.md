# Content Update Plan

Update the AWS workshop site content based on the Databricks workshop, which provides stronger conceptual explanations of core topics: embeddings, vector search, graph-enriched retrieval, knowledge graph construction, chunking, and entity resolution. This plan focuses on content quality — not diagrams (covered separately in SITE_UPDATE.md).

## Implementation Status

All six phases are complete. Changes were applied directly to .adoc files in `site/modules/ROOT/pages/`.

| Phase | Status | Files Modified |
|-------|--------|---------------|
| Phase 1: Foundational Concepts | DONE | index.adoc, lab1.adoc |
| Phase 2: Embeddings, Vector Search, Chunking | DONE | lab6.adoc |
| Phase 3: Knowledge Graph Construction | DONE | lab6.adoc |
| Phase 4: Agent Concepts and MCP | DONE | lab3.adoc, lab4.adoc, lab7.adoc |
| Phase 5: Tool Reliability | DONE | lab2.adoc |
| Phase 6: Cross-Cutting Polish | DONE | lab1.adoc, lab6.adoc, lab7.adoc |

### What Was Added

**New sections (full == level sections):**
- `index.adoc`: "The SEC 10-K Dataset" section explaining the data domain
- `lab6.adoc`: "Embeddings and Vector Search" section with RAG collapsible
- `lab6.adoc`: "Chunking" section with trade-offs collapsible
- `lab6.adoc`: "From Documents to Knowledge Graph" with entity extraction collapsible
- `lab6.adoc`: "Fulltext Search" section explaining Lucene indexes and operators
- `lab7.adoc`: "Why a Specialized Graph Agent" section
- `lab2.adoc`: "Tool Reliability" section with Text2Cypher cross-checking collapsible

**New collapsible deep-dives:**
- `lab1.adoc`: "Why this schema design" (Company as hub, typed relationships, Document/Chunk layer)
- `lab1.adoc`: "Why constraints matter for data loading" (MERGE idempotency)
- `lab3.adoc`: "A multi-cycle example with SEC data" (NVIDIA risk/exposure walkthrough)
- `lab6.adoc`: "How vector search powers RAG" (embed → search → context → generate)
- `lab6.adoc`: "Chunking trade-offs" (larger vs smaller, FixedSizeSplitter)
- `lab6.adoc`: "The chunk-as-anchor constraint" (traversal depends on search quality)
- `lab6.adoc`: "Entity extraction and resolution" (CSV vs LLM extraction)
- `lab6.adoc`: "How the retrieval_query parameter works" (with Cypher example)
- `lab7.adoc`: "How schema-first prevents query failures" (Corp vs Company example)
- `lab2.adoc`: "Why Text2Cypher needs cross-checking" (case sensitivity failure)

**Enhanced existing content:**
- `lab1.adoc`: Graph-vs-relational collapsible expanded with BlackRock portfolio Cypher example
- `lab2.adoc`: Tool Type Comparison table gained Reliability column (Deterministic/Grounded/Variable)
- `lab4.adoc`: Three Retrieval Strategies section gained contextual overview sentence
- `lab6.adoc`: VectorCypherRetriever description rewritten with explicit anchor-traversal explanation
- `lab7.adoc`: Next Steps updated to remove deleted Lab 8 reference

### What Was NOT Added (Deferred)

- **Sample queries reference page** (Phase 6.2): Deferred as a standalone task. Requires creating a new .adoc file and updating nav.adoc.
- **Additional collapsibles** from Phase 6.1 table: "How MCP tool discovery works" and "How HybridRetriever combines scores" were not added to avoid over-engineering. The existing content in Lab 7 (MCP tool discovery) and Lab 6 (alpha tuning) covers these adequately.

### Collapsible Section Count

Before: ~10 collapsible sections across all labs
After: ~20 collapsible sections, each with substantive educational content

---

## Key Differences: Databricks vs AWS Site

### What the Databricks Site Does Well (Content)

| Topic | Databricks Coverage | AWS Coverage |
|-------|-------------------|-------------|
| **Embeddings fundamentals** | Lab 3: Full explanation — what embeddings are, how they capture meaning, why "engine overheating" ≈ "thermal runaway in turbine" | Mentioned but never explained |
| **Chunking strategies** | Lab 3: Collapsible section on trade-offs — larger (better entity extraction) vs smaller (more precise retrieval), sweet spot guidance | Not mentioned anywhere |
| **Entity extraction & resolution** | Lab 3: LLM reads chunks → extracts entities → deduplicates ("HP Turbine" = "High-pressure Turbine" = "HPT") → cross-links to operational graph | Not covered |
| **Knowledge graph construction pipeline** | Lab 3: Documents → chunks → embeddings → entities → Neo4j, with `SimpleKGPipeline` orchestrating all steps | Data loading shown procedurally (LOAD CSV) with no conceptual grounding |
| **GraphRAG retrieval flow** | Lab 3: Detailed explanation — vector search finds chunks → graph traversal follows entities/relationships → enriched context reaches LLM. "Without extracted entities linked to chunks, there's nothing to traverse" | Mentioned in Lab 4/6 but mechanics not explained |
| **"Chunk as anchor" concept** | Lab 3: Vector search determines relevance, chunk acts as starting point, Cypher traverses from there to gather structured context | Implicit in Lab 6 VectorCypherRetriever but not articulated |
| **When to use which retriever** | Lab 3: Collapsible deep-dive — traversal starts from what vector search found; if question doesn't surface relevant chunks, graph traversal can't compensate | Lab 6 has selection guide table but lacks the reasoning behind it |
| **Vector search powering RAG** | Lab 3: Collapsible explaining embed question → search closest chunks → feed to LLM | Assumed knowledge |
| **Schema design choices** | Lab 3: Three modes (user-provided, extracted, free) with trade-offs for entity extraction | Not discussed |
| **Agent architecture depth** | Lab 4: Four-stage perceive-reason-act-observe loop with worked example showing multi-cycle reasoning | Lab 3 covers ReAct but less thoroughly |
| **Why specialized agents** | Lab 4: "Two schemas, two query languages in one prompt = dilutes focus" — concrete argument for agent-per-platform | Not addressed (Lab 7 just shows MCP agent) |
| **Tool reliability spectrum** | Lab 5: Cypher Templates (deterministic) > Similarity Search (grounded) > Text2Cypher (flexible but variable), with concrete accuracy failure examples | Lab 2 has comparison table but lacks failure analysis |
| **Text2Cypher accuracy risks** | Lab 5: Collapsible with real example — filtering "critical" vs "CRITICAL" silently returns wrong results; agent presents empty result confidently | Not mentioned |
| **Collapsible deep-dives** | 25+ across all labs, each with substantive educational content | ~10, mostly implementation details |
| **SEC/domain data context** | N/A (uses aircraft maintenance domain) | SEC 10-K filings never explained — what they are, why they matter |

### Content the AWS Site Has That Should Be Preserved

- MCP protocol explanation (Lab 7) — good 3-component architecture breakdown
- MCP vs Direct Library comparison table (Lab 4) — unique to AWS site
- Alpha parameter tuning guidance (Lab 6) — practical and well-explained
- Transport options table (Lab 7) — stdio vs streamable HTTP
- Schema-first approach explanation (Lab 7) — retrieve schema before writing Cypher
- AgentCore deployment content (Lab 3) — AWS-specific, not in Databricks
- Lab 1 Explore page (visual graph exploration with GDS) — hands-on and effective
- Clear 3-part workshop structure (no-code → Python → advanced agents)

---

## Phased Update Plan

### Phase 1: Foundational Concepts (index.adoc, lab1.adoc) — COMPLETE

These updates establish the conceptual vocabulary used throughout the workshop.

#### 1.1 — Add SEC 10-K Filing Context (index.adoc) — DONE

Add a section explaining the dataset before diving into architecture:
- What SEC 10-K filings are (annual reports companies file with the SEC)
- Why they're useful for GraphRAG (structured entities + unstructured narrative text)
- What kinds of questions they enable (risk exposure, portfolio analysis, competitive landscape)
- Brief data summary: ~76 companies, 274 products, 203 risk factors, 15 asset managers

**Model**: Databricks index.adoc "Data Intelligence Meets Graph Intelligence" section, which grounds the reader in why the data matters before showing architecture.

#### 1.2 — Strengthen Graph vs Relational Explanation (lab1.adoc) — DONE

Current collapsible "How graphs compare to relational databases" is adequate but could be stronger.

- Add a concrete SEC example: "Finding all risk factors that affect an asset manager's portfolio requires joining through companies — in SQL that's multiple JOINs, in a graph it's one traversal pattern"
- Add a worked comparison: same question in SQL (with JOINs) vs Cypher (with pattern matching)
- Explain why graph structure makes multi-hop questions natural

**Model**: Databricks lab1.adoc "Graphs vs Relational Databases" collapsible — shows the same query in both paradigms.

#### 1.3 — Add "Why This Schema?" Section (lab1.adoc) — DONE

Explain the design decisions behind the knowledge graph schema:
- Why Company is the central node (most relationships radiate from it)
- Why COMPETES_WITH and PARTNERS_WITH are separate relationship types (different traversal semantics)
- Why Document → Chunk → entity structure supports both retrieval and traversal
- Reference Databricks lab2.adoc "Design Decision: Relationship Types vs Properties" pattern

---

### Phase 2: Embeddings, Vector Search, and Chunking (lab6.adoc, lab4.adoc) — COMPLETE

The biggest content gap. These concepts are assumed knowledge in the AWS site but are essential for understanding Labs 4-7.

#### 2.1 — Add "Embeddings and Vector Search Fundamentals" Section (lab6.adoc) — DONE

This should appear before the retriever explanations since Lab 6 is where the pipeline is built.

Content to add:
- **What embeddings are**: Text → numerical vector that captures semantic meaning
- **Why they enable semantic search**: "SEC cybersecurity risk" and "data breach vulnerability" produce similar vectors despite different words
- **How vector search works**: Embed the question → find nearest vectors in index → return matching chunks
- **How vector search powers RAG**: Question → embedding → closest chunks → LLM uses chunks as context → grounded response
- **Embedding model choice**: Bedrock Nova (1024 dimensions) — what dimensions mean, why model choice matters
- **Vector indexes**: What they are (HNSW approximate nearest neighbor), why they're needed for performance

**Model**: Databricks lab3.adoc "Embeddings and Vector Search Fundamentals" + "How Vector Search Powers RAG" collapsible.

#### 2.2 — Add "Chunking Strategies" Section (lab6.adoc) — DONE

Add as collapsible section near the data loading notebook explanation:
- **Why chunk**: Documents too large for embedding models and retrieval precision
- **Trade-offs**: Larger chunks = more context for entity extraction but less precise retrieval; smaller chunks = precise retrieval but may lose context
- **Sweet spot guidance**: 500–1000 characters with boundary considerations
- **How chunks connect in the graph**: `(:Document)<-[:FROM_DOCUMENT]-(:Chunk)-[:NEXT_CHUNK]->(:Chunk)` preserves reading order

**Model**: Databricks lab3.adoc "Chunking Trade-Offs" collapsible section.

#### 2.3 — Add "Fulltext Search Explained" Section (lab6.adoc) — DONE

Currently mentioned multiple times but never explained:
- **What fulltext indexes are**: Lucene-backed keyword indexes on text properties
- **When to use fulltext vs vector**: Fulltext for exact terms, tickers, identifiers; vector for semantic/conceptual queries
- **Query operators**: Fuzzy (~), wildcard (*), boolean (AND/OR/NOT) with examples
- **Why hybrid combines both**: Vector catches meaning, fulltext catches exact terms — alpha parameter balances them

#### 2.4 — Strengthen "Chunk as Anchor" Explanation (lab6.adoc) — DONE

The VectorCypherRetriever section mentions graph traversal but doesn't articulate the core insight clearly enough.

Add explicit explanation:
- Vector search finds the relevant chunks (semantic relevance)
- The chunk is the **anchor point** — the bridge between unstructured and structured
- Cypher traverses FROM_DOCUMENT → Document → FILED → Company → OFFERS/FACES_RISK to gather structured entities
- The LLM receives both the chunk text AND the connected entities
- **Critical insight**: "If the question doesn't surface relevant chunks, graph traversal can't compensate — the anchor determines what's reachable"

**Model**: Databricks lab3.adoc "GraphRAG: Graph-Enriched Retrieval" section and "How GraphRAG Retrieval Works" collapsible.

---

### Phase 3: Knowledge Graph Construction (lab6.adoc) — COMPLETE

#### 3.1 — Add "From Documents to Knowledge Graph" Pipeline Overview (lab6.adoc) — DONE

Add a section before the notebook table explaining the full pipeline:
- **Stage 1**: Load SEC filing text as Document nodes
- **Stage 2**: Split documents into Chunk nodes linked via FROM_DOCUMENT and NEXT_CHUNK
- **Stage 3**: Generate embeddings for each chunk, create vector index
- **Stage 4**: (If applicable) Extract entities from chunks, link via FROM_CHUNK
- Show how notebooks 01–02 implement stages 1–3

**Model**: Databricks lab3.adoc "From Documents to Knowledge Graph" pipeline overview.

#### 3.2 — Add Entity Extraction and Resolution Explanation (lab6.adoc) — DONE

Decision: Added as collapsible explaining that the workshop uses CSV-loaded entities rather than LLM extraction, while explaining the concept for production pipelines.
- **What entity extraction does**: LLM reads chunks → identifies entities (companies, products, risk factors)
- **Entity resolution**: Same entity mentioned differently across chunks gets deduplicated
  - Example: "NVIDIA Corporation", "Nvidia", "NVDA" → one Company node with multiple chunk connections
- **Cross-linking**: Extracted entities connect to existing graph structure (Company nodes from CSV loading)
- **Why it matters**: Without entity links, graph traversal from chunks has nothing to reach

If entity extraction is NOT part of the current pipeline, add a collapsible section explaining the concept and noting that the structured CSV data serves this role in the workshop (pre-built entity nodes linked to chunks via the Document→Company path).

**Model**: Databricks lab3.adoc "Chunks to Graph Structure" and "Schema Design and Entity Resolution" sections.

---

### Phase 4: Agent Concepts and MCP (lab3.adoc, lab7.adoc, lab4.adoc) — COMPLETE

#### 4.1 — Strengthen Agent Architecture Explanation (lab3.adoc) — DONE

The ReAct section is adequate but could be more concrete:
- Add a worked example showing multi-cycle reasoning with SEC data:
  1. User asks "What risks does NVIDIA face and which asset managers are exposed?"
  2. Agent reasons: need NVIDIA's risk factors first
  3. Calls tool, observes risk factors
  4. Reasons: now need asset managers who own NVIDIA
  5. Calls tool, observes owners
  6. Synthesizes: "NVIDIA faces X risks, and asset managers A, B, C hold positions"
- This makes the abstract loop concrete

**Model**: Databricks lab4.adoc "What Are Agents" section with the worked multi-cycle example.

#### 4.2 — Add "Why Specialized Agents" Discussion (lab7.adoc) — DONE

Currently the AWS site doesn't explain why you'd use an MCP agent vs direct queries:
- **The problem with one agent, many tools**: Two query languages in one prompt dilutes focus; agent mixes SQL idioms (rows, filters, aggregations) with Cypher idioms (paths, patterns, traversals)
- **Specialized agents**: Each agent focuses on one data shape and one query language
- **Orchestration**: Supervisor or user routes questions to the right specialist
- Tie back to Lab 2 (Aura Agents as no-code specialist) and Lab 7 (MCP agent as code specialist)

**Model**: Databricks lab4.adoc "Specialized Agents for Different Data Structures" section.

#### 4.3 — Add MCP Retrieval Context to Lab 4 (lab4.adoc) — DONE

Lab 4 is sparse on conceptual content. Add:
- Brief explanation of how the three notebooks build on each other (01 → 02 → 03 is a progression of retrieval sophistication)
- What each retrieval strategy returns and why it matters:
  - Vector: just chunk text (fast, good for conceptual questions)
  - Graph-enriched: chunk text + connected entities (answers "who/what is this about?")
  - Hybrid: vector + fulltext (catches both meaning and exact terms)

---

### Phase 5: Retrieval Tool Reliability and Accuracy (lab2.adoc) — COMPLETE

#### 5.1 — Strengthen Tool Reliability Discussion (lab2.adoc) — DONE

The current comparison table lists tool types but doesn't discuss reliability trade-offs:
- Add the **reliability spectrum**: Cypher Templates (deterministic, always correct for covered patterns) > Similarity Search (grounded in vector similarity scores) > Text2Cypher (most flexible, highest risk)
- Add a collapsible section on **Text2Cypher accuracy risks**:
  - Generated query varies with each invocation
  - Case sensitivity: filtering on "cybersecurity" vs "Cybersecurity" may silently return wrong results
  - Agent may present empty results confidently without flagging the query issue
  - **Practical check**: Run same question twice, compare results to spot variability
- Explain **why all three tool types exist**: Templates cover known patterns deterministically; similarity search bridges semantic gaps; Text2Cypher handles the long tail of ad-hoc questions

**Model**: Databricks lab5.adoc "Accuracy Challenges with Text2Cypher" collapsible and "Tool Type Reliability Spectrum" sections.

---

### Phase 6: Cross-Cutting Content Polish — COMPLETE

#### 6.1 — Add Collapsible Deep-Dives Throughout — DONE (partial)

Target: increase from ~10 to ~20 collapsible sections. Priority additions (items marked with status):

| Location | Topic | Content |
|----------|-------|---------|
| lab1.adoc | "Why constraints before loading data" | Uniqueness constraints ensure MERGE operations are idempotent |
| lab1.adoc | "How LOAD CSV and MERGE work" | Explain MERGE semantics — create if new, match if existing |
| lab4.adoc | "How graph-enriched retrieval works step by step" | Walk through: embed query → vector search → match chunks → traverse FROM_DOCUMENT → Document → FILED → Company → OFFERS → Product |
| lab6.adoc | "How embeddings are generated with Bedrock Nova" | Model receives text, returns 1024-dim float array, stored as node property, indexed for approximate nearest neighbor search |
| lab6.adoc | "How HybridRetriever combines scores" | Two independent searches, scores normalized, alpha-weighted combination, re-ranked |
| lab6.adoc | "Why the retrieval_query parameter matters" | This Cypher runs per result — traverses from anchor chunk to gather context |
| lab7.adoc | "How schema-first prevents query failures" | Without schema: LLM might generate `MATCH (c:Corp)` when label is `Company`. With schema: LLM sees exact labels and properties |
| lab7.adoc | "How MCP tool discovery works" | Agent connects → server advertises available tools → agent binds them for use in reasoning loop |

#### 6.2 — Add Sample Questions Reference — DEFERRED

Create a standalone page (like Databricks lab1-sample-queries.adoc) consolidating example questions across all labs, organized by retrieval strategy:

- **Direct Cypher** (Lab 1): "What products does NVIDIA offer?", "Which risk factors are shared across companies?"
- **Vector Search** (Lab 4/6): "What are the main risks in the AI industry?", "Tell me about cybersecurity concerns"
- **Graph-Enriched** (Lab 4/6): "What risks does Apple face and which filing discusses them?"
- **Hybrid** (Lab 6): "What does NVDA's 10-K say about supply chain risk?"
- **Agent-Driven** (Lab 7): "Which asset managers are most exposed to cybersecurity risk across their portfolios?"

#### 6.3 — Update Cross-References and Next Steps — DONE (Lab 8 reference fixed)

- Lab 7 Next Steps updated to remove broken Lab 8 xref and reflect workshop completion
- Other lab cross-references verified as correct

---

## Priority Order

| Priority | Phase | Impact | Effort |
|----------|-------|--------|--------|
| **P0** | Phase 2 (Embeddings, Vector Search, Chunking) | Fills the largest conceptual gap — these are prerequisites for understanding Labs 4–7 | Medium |
| **P1** | Phase 3 (Knowledge Graph Construction) | Explains the pipeline that produces the data everyone queries | Medium |
| **P1** | Phase 5 (Tool Reliability) | Directly improves Lab 2 which is early in the workshop | Low |
| **P2** | Phase 1 (Foundational Concepts) | Improves first impressions and data context | Low |
| **P2** | Phase 4 (Agent Concepts) | Strengthens understanding but existing content is functional | Medium |
| **P3** | Phase 6 (Cross-Cutting Polish) | Improves overall quality but not blocking | Medium |

---

## Success Criteria

After updates, a reader should be able to answer these questions from the site content alone (without looking at notebook code):

1. What are embeddings and why do they enable semantic search?
2. What is chunking and what are the trade-offs in chunk size?
3. How does GraphRAG differ from standard RAG? (chunk as anchor → graph traversal)
4. Why does the VectorCypherRetriever exist when VectorRetriever already works?
5. What is the reliability spectrum of Cypher Templates vs Similarity Search vs Text2Cypher?
6. Why use a specialized MCP agent instead of putting all tools in one agent?
7. What are SEC 10-K filings and why is this data useful for GraphRAG?
