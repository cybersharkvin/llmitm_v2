# Neo4j Onboarding Guide: Research & Best Practices

This document serves as the primary onboarding guide for any developer joining the LLMitM v2 project. It provides a high-level map of the official Neo4j documentation, followed by a curated set of deep-dive research reports that are essential for understanding our architecture, design patterns, and implementation choices. Each report is summarized to explain its relevance and provide context for why it is required reading.

---

## Neo4j Documentation Map

This section provides a comprehensive, hierarchically structured map of the Neo4j documentation, based on the exhaustive research conducted. It is designed to serve as a top-level exploration guide with heavy cross-linking to the official documentation for every feature.

- **[Cypher Manual (Entry Point)](https://neo4j.com/docs/cypher-manual/current/)**
  - **Core Concepts**
    - [Introduction to Cypher](https://neo4j.com/docs/cypher-manual/current/introduction/)
    - [Graph patterns](https://neo4j.com/docs/cypher-manual/current/patterns/)
    - [Values and types](https://neo4j.com/docs/cypher-manual/current/values-and-types/)
  - **Clauses**
    - [Reading Data: `MATCH`, `WHERE`, `RETURN`](https://neo4j.com/docs/cypher-manual/current/clauses/match/)
    - [Writing Data: `CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`](https://neo4j.com/docs/cypher-manual/current/clauses/create/)
    - [Chaining & Transforming: `WITH`, `UNWIND`](https://neo4j.com/docs/cypher-manual/current/clauses/with/)
    - [Combining Queries: `UNION`](https://neo4j.com/docs/cypher-manual/current/clauses/union/)
    - [Procedures & Subqueries: `CALL`](https://neo4j.com/docs/cypher-manual/current/clauses/call-subquery/)
  - **Advanced Patterns & Expressions**
    - [Subqueries (`EXIST`, `COUNT`, `COLLECT`)](https://neo4j.com/docs/cypher-manual/current/subqueries/)
    - [Quantified Path Patterns](https://neo4j.com/docs/cypher-manual/current/patterns/quantified-path-patterns/)
    - [List Comprehensions](https://neo4j.com/docs/cypher-manual/current/syntax/lists/#syntax-list-comprehension)
    - [Pattern Comprehensions](https://neo4j.com/docs/cypher-manual/current/syntax/pattern-comprehension/)
    - [CASE Expressions](https://neo4j.com/docs/cypher-manual/current/syntax/expressions/#syntax-case-expressions)
  - **Functions**
    - [Complete Function Reference](https://neo4j.com/docs/cypher-manual/current/functions/)
    - [Vector Functions](https://neo4j.com/docs/cypher-manual/current/functions/vector/)
  - **Performance & Administration**
    - [Query Tuning (`EXPLAIN`, `PROFILE`)](https://neo4j.com/docs/cypher-manual/current/query-tuning/)
    - [Indexes for Search Performance](https://neo4j.com/docs/cypher-manual/current/indexes/)
    - [Constraints for Data Integrity](https://neo4j.com/docs/cypher-manual/current/constraints/)

- **[Create Applications (Entry Point)](https://neo4j.com/docs/create-applications/)**
  - **[Python Driver Manual (v6)](https://neo4j.com/docs/python-manual/current/)**
    - [Quickstart](https://neo4j.com/docs/python-manual/current/getting-started/)
    - [Connecting to the Database](https://neo4j.com/docs/python-manual/current/driver-connections/)
    - [Querying the Database (`execute_query`)](https://neo4j.com/docs/python-manual/current/query-simple/)
    - [Managed Transactions (`session.execute_read/write`)](https://neo4j.com/docs/python-manual/current/transactions/)
    - [Performance Recommendations](https://neo4j.com/docs/python-manual/current/performance/)
    - [Data Types & Mapping](https://neo4j.com/docs/python-manual/current/cypher-values/)
  - **[GraphQL Library](https://neo4j.com/docs/graphql/)**
    - [Type Definitions](https://neo4j.com/docs/graphql/current/type-definitions/)
    - [Directives (`@cypher`, `@vector`, `@authentication`)](https://neo4j.com/docs/graphql/current/directives/)
    - [Queries & Mutations](https://neo4j.com/docs/graphql/current/queries/)
  - **[Change Data Capture (CDC)](https://neo4j.com/docs/cdc/current/)**
    - [Querying Changes (`db.cdc.query`)](https://neo4j.com/docs/cdc/current/procedures/query/)
    - [Modes (`DIFF` vs `FULL`)](https://neo4j.com/docs/cdc/current/configuration/#cdc-mode)

- **[GenAI (Entry Point)](https://neo4j.com/docs/genai/)**
  - **[Vector Indexes](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/)**
    - [Creating a Vector Index](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/#indexes-vector-create)
    - [Querying (`db.index.vector.queryNodes`)](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/#indexes-vector-query-procedure)
    - [Configuration Options (HNSW, quantization)](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/#indexes-vector-configuration)
    - [The `VECTOR` Type](https://neo4j.com/docs/cypher-manual/current/values-and-types/vector/)
  - **[GenAI Plugin](https://neo4j.com/docs/genai/plugin/current/)**
    - [Embedding Generation (`ai.text.embed`)](https://neo4j.com/docs/genai/plugin/current/create-embeddings/)
    - [Text Generation (`ai.text.completion`, `ai.text.chat`)](https://neo4j.com/docs/genai/plugin/current/generate-text/)
    - [Configuration](https://neo4j.com/docs/genai/plugin/current/configuration/)
  - **[GraphRAG Python Package](https://neo4j.com/docs/neo4j-graphrag-python/current/)**
    - [Retrievers (`VectorCypherRetriever`)](https://neo4j.com/docs/neo4j-graphrag-python/current/user-guide/rag/retrievers/)
    - [Knowledge Graph Builder](https://neo4j.com/docs/neo4j-graphrag-python/current/user-guide/kg-builder/)
  - **[GenAI Ecosystem & Blog](https://neo4j.com/labs/genai-ecosystem/)**
    - [GenAI Blog Tag](https://neo4j.com/blog/tag/genai/)
    - [GraphRAG Pattern Catalogue](https://neo4j.com/labs/genai-ecosystem/graphrag-pattern-catalogue)

- **[Tools & Ecosystem (Entry Point)](https://neo4j.com/docs/tools/)**
  - [Neo4j Workspace (Bloom & Explore)](https://neo4j.com/docs/workspace/current/)
  - [Neo4j Browser](https://neo4j.com/docs/browser-manual/current/)
  - [Neo4j Data Importer](https://neo4j.com/docs/data-importer/current/)
  - [Neo4j Desktop](https://neo4j.com/docs/desktop-manual/current/)
  - **Libraries & Protocols**
    - **[APOC Library](https://neo4j.com/docs/apoc/current/)**
      - [Data Integration (`apoc.load.json`)](https://neo4j.com/docs/apoc/current/import/)
      - [Graph Algorithms (`apoc.algo.dijkstra`)](https://neo4j.com/docs/apoc/current/graph-algorithms/)
      - [Periodic Execution (`apoc.periodic.iterate`)](https://neo4j.com/docs/apoc/current/background-operations/periodic-execution/)
    - **[Model Context Protocol (MCP) Server](https://neo4j.com/docs/mcp/current/)**
      - [Exposed Tools (`read-cypher`, `get-schema`)](https://neo4j.com/docs/mcp/current/usage/#mcp-tools)
      - [Configuration](https://neo4j.com/docs/mcp/current/configuration/)

---

## Curated Research Reports

### 1. Cypher Language Deep Dive

#### [Cypher Clauses and Query Patterns](./neo4j_docs/cypher_clauses_and_query_patterns.md)
This report provides a foundational understanding of all major Cypher clauses, from basic reads and writes to advanced transformations. It is essential reading for any developer to understand how the agent interacts with the graph at a fundamental level. The document covers pattern matching, filtering, data manipulation, and query chaining, providing the core vocabulary for all graph operations.

#### [Cypher Subqueries and Advanced Patterns](./neo4j_docs/cypher_subqueries_and_advanced_patterns.md)
Building on the basics, this document explores the advanced patterns required for complex agentic reasoning. It details the four types of subqueries (`CALL`, `EXIST`, `COUNT`, `COLLECT`) and how they enable conditional logic and inline data aggregation. It also covers Quantified Path Patterns (QPP) for traversing variable-length chains, which is critical for walking our `ActionGraph` step sequences.

#### [Cypher Functions and Expressions](./neo4j_docs/cypher_functions_and_expressions.md)
This report catalogs the extensive library of over 100 built-in Cypher functions, including list, string, mathematical, and vector operations. It also covers the use of `CASE` statements and list/pattern comprehensions for inline data transformation. A developer must understand these tools to write efficient and expressive queries for the `GraphRepository`.

#### [Cypher Indexes, Constraints, and Tuning](./neo4j_docs/cypher_indexes_constraints_and_tuning.md)
This document covers the critical administrative aspects of managing a Neo4j database. It details all index types (range, text, vector) and constraint types (unique, existence, key) that ensure data integrity and query performance. It also explains how to use `EXPLAIN` and `PROFILE` to debug and optimize query performance, a mandatory skill for maintaining a healthy production system.

### 2. GenAI & Vector Search

#### [Vector Indexes Deep Dive](./neo4j_docs/vector_indexes_deep_dive.md)
This is one of the most critical documents for understanding the core of our agent's long-term memory and fuzzy lookup capabilities. It provides a deep dive into Neo4j's HNSW-based vector indexes, covering their creation, configuration, and the two methods for querying (procedure vs. `SEARCH` clause). Understanding this is essential for working on the context assembly and fingerprint matching components of the orchestrator.

#### [GenAI Plugin: Embeddings and Text Generation](./neo4j_docs/genai_plugin_embeddings_and_text_generation.md)
This report details the `genai` plugin, which allows for embedding generation and LLM text completion directly within Cypher queries. This capability is used in our self-repair classification logic as a fallback for ambiguous errors. A developer should understand how to call these procedures and configure the supported LLM providers.

#### [GraphRAG Retrievers](./neo4j_docs/graphrag_retrievers.md)
This document explores the `neo4j-graphrag-python` package, focusing on its powerful retriever classes. It specifically highlights the `VectorCypherRetriever`, which implements the four-layer retrieval pipeline (vector search -> graph traversal -> business logic -> rerank) that is central to our context assembly strategy. This pattern is the foundation of how our agent gathers relevant knowledge from the graph before invoking the LLM.

#### [GraphRAG Knowledge Graph Builder and Pipeline](./neo4j_docs/graphrag_knowledge_graph_builder_and_pipeline.md)
While not used in the core runtime of LLMitM v2, this report is important for understanding how we can build and enrich our knowledge graph from unstructured data sources (e.g., threat intelligence reports). It covers the `SimpleKGPipeline` for entity/relationship extraction, which is a key part of our data ingestion and graph maintenance strategy.

#### [GenAI Blog Articles and Best Practices](./neo4j_docs/genai_blog_articles_and_best_practices.md)
This report synthesizes key insights and architectural patterns from Neo4j's official GenAI blog. It covers topics like Text2Cypher best practices, the RAG vs. Fine-Tuning debate, and real-world case studies. This provides valuable context and reinforces the design decisions made in our project.

#### [GenAI Ecosystem Overview](./neo4j_docs/genai_ecosystem_overview.md)
This document provides a high-level overview of the entire Neo4j GenAI ecosystem, including partner integrations and related labs projects. It helps a developer understand where our project fits within the broader landscape of graph-based AI. It also introduces the concept of the `neo4j-agent-memory` library, which informs our own memory and state management design.

### 3. Application Development & Integration

#### [Python Driver v6 Comprehensive Guide](./neo4j_docs/python_driver_v6_comprehensive_guide.md)
This is the definitive guide to the official Neo4j Python driver, which is the exclusive interface between our Python application and the database. It covers everything from basic connection and querying to advanced transaction management and performance tuning. Every developer must be proficient with the patterns in this document, as they are used throughout the `GraphRepository`.

#### [Python Driver Advanced Patterns](./neo4j_docs/python_driver_advanced_patterns.md)
This report builds on the comprehensive guide, focusing on advanced topics like causal consistency with bookmarks, concurrency management, and the `@unit_of_work` decorator. These patterns are critical for ensuring data integrity and building a scalable, resilient system. Understanding these concepts is mandatory for anyone modifying the core orchestrator or repository logic.

#### [GraphQL Library and Change Data Capture (CDC)](./neo4j_docs/graphql_library_and_change_data_capture.md)
This document covers two key integration technologies. The GraphQL Library section explains how we can auto-generate a flexible API for our graph, which is used for external monitoring and data exploration tools. The Change Data Capture (CDC) section details how we can build a reactive architecture, allowing the agent to respond to real-time changes in the graph, which is a key part of our future roadmap for proactive self-repair.

### 4. Tools & Ecosystem

#### [APOC Library](./neo4j_docs/apoc_library.md)
This report provides an overview of the APOC (Awesome Procedures on Cypher) library, which provides over 130 useful procedures and functions that extend Cypher. It covers data import/export, pathfinding algorithms, and periodic execution for batch operations. We use `apoc.periodic.iterate` for large-scale data migrations and updates.

#### [MCP Server Deep Dive](./neo4j_docs/mcp_server_deep_dive.md)
This document details the Model Context Protocol (MCP) server, a standardized bridge for LLMs to interact with Neo4j. While our production system uses the deterministic `GraphRepository`, the MCP server is a valuable tool for debugging and interactive exploration. A developer should understand how to configure and use it to query the graph conversationally during development.
