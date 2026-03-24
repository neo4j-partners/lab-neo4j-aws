# Site Update Plan

Improve the AWS workshop site by adding visual diagrams and tightening content, informed by patterns from the Databricks workshop.

---

## What the Databricks Site Does Well

- **Architecture diagrams as Excalidraw images** instead of ASCII art — supervisor agent routing, MCP connection flow, dual-database architecture
- **Step-by-step transformation visuals** — e.g., three images showing flat tables → Spark mapping → connected graph
- **Conceptual flow diagrams** — knowledge graph structure, GraphRAG retrieval flow (vector search → chunks → graph traversal → enriched context)
- **Collapsible examples** and **comparison tables** throughout (SQL vs Cypher, question routing by platform)
- **Sample queries page** as a standalone reference (lab1-sample-queries.adoc)

## What the AWS Site Is Missing

- Labs 4, 6, and 7 have **zero images** — all code-only with no visual context
- Index page architecture diagram is **ASCII art** — should be an Excalidraw diagram
- No **GraphRAG retrieval flow** diagram showing how vector search, graph traversal, and enrichment work together
- No **knowledge graph schema** visual — the schema is shown as text only
- No **MCP architecture** diagram for Labs 4 and 7

---

## Phase 1: Core Architecture Diagrams (Excalidraw)

Create the foundational visuals that appear on the index page and are referenced across labs.

- [ ] **Workshop architecture diagram** — Replace ASCII art on index.adoc with Excalidraw showing: User Query → AI Agent → Tool Selection (Vector Search / Text2Cypher / Cypher Template) → Neo4j Aura → SEC 10-K Knowledge Graph
- [ ] **Knowledge graph schema diagram** — Visual of the SEC data model: Company, Product, RiskFactor, AssetManager, Document, Chunk with labeled relationships (OFFERS, FACES_RISK, COMPETES_WITH, PARTNERS_WITH, OWNS, FILED, FROM_DOCUMENT)
- [ ] **GraphRAG retrieval flow diagram** — Show the pipeline: query → embedding → vector search → chunk matches → graph traversal to connected entities → enriched context → LLM response

## Phase 2: Lab-Specific Diagrams

Add visuals to the labs that currently have none.

- [ ] **Lab 4 — MCP retrieval architecture** — Show MCP client connecting to Neo4j MCP Server, with the three retrieval strategies (vector, graph-enriched, hybrid) as branches
- [ ] **Lab 4 — Graph-enriched retrieval visual** — Show how a vector match on a Chunk traverses FROM_DOCUMENT → Document → FILED → Company → OFFERS/FACES_RISK to pull connected entities
- [ ] **Lab 6 — Data pipeline diagram** — Show the flow: CSV seed data + 10-K text → chunking + embedding → Neo4j (nodes, relationships, vector index, fulltext index)
- [ ] **Lab 6 — Retriever comparison visual** — Side-by-side of VectorRetriever (pure semantic) vs VectorCypherRetriever (semantic + graph traversal) showing what each returns
- [ ] **Lab 7 — MCP agent architecture** — Show agent loop: LLM reasoning → MCP tool call (get-schema / read-cypher) → Neo4j → results back to LLM → response

## Phase 3: Content Polish

- [ ] Review each concept page (lab*.adoc) for opportunities to add collapsible example sections like Databricks site uses
- [ ] Add a standalone **sample queries** reference page (like Databricks lab1-sample-queries.adoc) consolidating example questions across all labs
- [ ] Update lab cross-references and "Next Steps" sections to reflect final lab structure (Lab 7 is now the final lab)
