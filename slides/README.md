# Workshop Slides

Presentation-ready slides formatted for [Marp](https://marp.app/).

## Quick Start

Requires Node.js 22 LTS (`brew install node@22`) and a one-time `npm install` in this directory.

```bash
/opt/homebrew/opt/node@22/bin/node ./node_modules/.bin/marp overview-aws-neo4j --server
```

Opens at http://localhost:8080/. Replace `overview-aws-neo4j` with any slide deck directory name.

## Export All Presentations

```bash
cd slides
for dir in overview-*/; do
  /opt/homebrew/opt/node@22/bin/node ./node_modules/.bin/marp "$dir" --pdf --allow-local-files
done
```

## Troubleshooting

**`require is not defined in ES module scope` error?**
- Marp CLI is incompatible with Node.js 25+. Install Node 22 LTS: `brew install node@22`

**Images not showing?**
- Use `--allow-local-files` flag with Marp CLI

---

## Slide Decks

### `overview-aws-neo4j/`
Workshop introduction — the AWS + Neo4j partnership, workshop architecture, SEC 10-K financial data domain, and the lab roadmap from visual exploration through GraphRAG agents.

### `overview-knowledge-graph/`
Knowledge graph foundations — graph databases vs relational, Cypher query language, the SEC financial knowledge graph schema, Neo4j Aura, and visual exploration tools.

### `overview-graphrag/`
GenAI limitations and the GraphRAG solution — hallucination, context rot, embeddings, vector search, RAG, and how graph context transforms retrieval quality.

### `overview-retrievers/`
GraphRAG retriever patterns — VectorRetriever, VectorCypherRetriever, the two-layer graph, retrieval query design, and choosing the right retriever for your question type.

### `overview-agents-mcp/`
Agents and MCP — the ReAct pattern, Strands Agents SDK, Model Context Protocol architecture, Cypher Templates vs Text2Cypher, schema-first approach, and agent deployment with AgentCore.

---

## Slide Format

All slides use Marp markdown format with pagination, syntax-highlighted code blocks, tables, and two-column layouts. See any slide file for the frontmatter template.

## Additional Resources

- [Marp Documentation](https://marpit.marp.app/)
- [Marp CLI Usage](https://github.com/marp-team/marp-cli)
- [Marp Themes](https://github.com/marp-team/marp-core/tree/main/themes)
- [Creating Custom Themes](https://marpit.marp.app/theme-css)
