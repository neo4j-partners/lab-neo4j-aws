# Site Documentation Review

Review of `site/modules/ROOT/pages/` — flow, content accuracy, and internal consistency.

All issues below have been **resolved** unless marked otherwise.

---

## Critical: Lab 3 LangGraph vs Strands Mismatch — FIXED

Rewrote lab3.adoc entirely for Strands: replaced LangGraph Agent Architecture section with Strands Agent Architecture, updated all code examples to use `strands.Agent`, `BedrockModel`, and `@tool`. Updated lab3-instructions.adoc notebook filename to `01_basic_strands_agent.ipynb`. Updated index.adoc Lab 3 description and Agent Orchestration section. Updated aws-services.adoc code example. Updated lab2-instructions.adoc next steps.

---

## Critical: Data Loading Dependency / Lab Ordering — FIXED

Added notes to both lab4.adoc and lab4-instructions.adoc explaining that the MCP Server connects to a database pre-loaded by the workshop admin with Document/Chunk nodes, embeddings, and fulltext indexes. Removed the misleading prerequisite that implied participants need to load this data.

---

## Critical: Lab 2 Similarity Search Requires Data — NOT FIXED

Lab 2 Similarity Search still references querying the `chunkEmbeddings` vector index, which won't have data unless the admin pre-loaded it. This may work if the admin's database has embeddings, but the participant's own Aura instance (from Lab 1) will not. Needs clarification on whether Lab 2 queries the admin's pre-loaded database or the participant's own instance.

---

## High: Missing Lab 5 — FIXED

Renumbered: Lab 6 → Lab 5 (GraphRAG), Lab 7 → Lab 6 (MCP Agent). Updated all cross-references across all pages, nav.adoc, and the index table. File renames: lab6.adoc → lab5.adoc, lab6-instructions.adoc → lab5-instructions.adoc, lab7.adoc → lab6.adoc, lab7-instructions.adoc → lab6-instructions.adoc.

Note: Actual directory names on disk (`Lab_6_GraphRAG/`, `Lab_7_Neo4j_MCP_Agent/`) were NOT renamed. Directory path references in docs still point to the real filesystem paths.

---

## High: Lab 8 Referenced but Not in Navigation — FIXED

Removed all Lab 8 references from configuration.adoc (three config fields and example block) and lab1-instructions.adoc ("Labs 3-8" → "Labs 3-6").

---

## Medium: Lab 2 Embedding Provider Mismatch — FIXED

Added a NOTE to lab2-instructions.adoc explaining that Aura Agents uses OpenAI for its built-in embeddings, which is separate from the Bedrock Nova embeddings used in later labs.

---

## Medium: Admin Setup Incomplete for MCP Server Deployment — NOT FIXED

admin-setup.adoc still does not explain how to deploy the Neo4j MCP Server. This requires information about the deployment process that isn't in the codebase.

---

## Medium: aws-services.adoc Next Steps Skip Essential Labs — FIXED

Reworded to: "Labs 1 and 2 set up the Neo4j database that all subsequent labs depend on."

---

## Low: sample-queries.adoc Undirected Relationship — FIXED

Changed `(r:RiskFactor)-[:FACES_RISK]-(c:Company)<-[:OWNS]-(am:AssetManager)` to use directed relationships matching the schema: `(c:Company)-[:FACES_RISK]->(r:RiskFactor), (am:AssetManager)-[:OWNS]->(c)`.

---

## Low: Lab 6 LangGraph Option Without Prior LangGraph Exposure — FIXED

Updated lab6.adoc (formerly lab7) to recommend Strands as the primary option and note that LangGraph is "included for participants with prior LangGraph experience who want to compare the two approaches."

---

## Low: "How the Notebooks Connect" Duplication in Lab 4 — FIXED

Removed the duplicate section from lab4.adoc.

---

## Still Open

1. **Lab 2 Similarity Search data dependency** — needs clarification on whether Lab 2 queries the admin's pre-loaded database or the participant's own instance
2. **Admin Setup MCP Server deployment** — needs deployment steps or external documentation link
3. **Lab 1 "9 filing companies" note** — minor clarity issue, low priority
4. **Part 3 has only one lab** — structural, low priority
5. **No overall workshop duration** — informational, low priority
