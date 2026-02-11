# Neo4j Vector Indexes Deep Dive: A Comprehensive Research Report

**Author:** Manus AI

**Date:** February 10, 2026

## 1. Overview and Purpose

Neo4j, a leading graph database, has embraced the world of artificial intelligence and machine learning by integrating vector search capabilities directly into its platform. This report provides a deep dive into Neo4j's vector indexes, a powerful feature that enables semantic search and similarity-based queries on large-scale graph data. By representing data as high-dimensional vectors, or embeddings, Neo4j allows developers to unlock new insights and build sophisticated AI-powered applications that leverage the rich relationships inherent in graph data.

The purpose of this research is to provide a comprehensive and technically detailed understanding of Neo4j's vector indexes. We will explore the underlying technology, the syntax for creating and querying indexes, configuration options, performance considerations, and best practices. This report will also delve into the practical applications of vector indexes in the context of building AI agent applications with Neo4j, and discuss the limitations and known issues of the current implementation. The information presented here is synthesized from the official Neo4j documentation, developer guides, community discussions, and expert articles, providing a holistic view of this critical feature.

## 2. Features, Functions, and Capabilities

Neo4j's vector index functionality is built upon the robust and widely-used Apache Lucene library, specifically leveraging its implementation of the Hierarchical Navigable Small World (HNSW) algorithm for approximate nearest neighbor (ANN) search. This provides a solid foundation for efficient and scalable similarity search.

### 2.1. Core Capabilities

*   **Vector Index Creation:** Neo4j provides a straightforward Cypher command, `CREATE VECTOR INDEX`, to create vector indexes on node or relationship properties. This allows you to specify the node label, property key, vector dimensions, and similarity function.

*   **Similarity Functions:** The two primary similarity functions supported are `cosine` and `euclidean`. Cosine similarity is generally recommended for text-based embeddings, while Euclidean distance is suitable for other types of vector data.

*   **Querying:** Vector indexes can be queried using two primary methods:
    *   The `SEARCH` clause: This is the modern and preferred method for querying vector indexes, offering a more expressive and integrated syntax within Cypher.
    *   The `db.index.vector.queryNodes()` and `db.index.vector.queryRelationships()` procedures: These were the original methods for querying vector indexes and are still supported.

*   **The `VECTOR` Type:** With the introduction of Cypher 25, Neo4j now includes a native `VECTOR` data type. This allows for more efficient storage and manipulation of vector data compared to the previous method of storing vectors as lists of numbers.

### 2.2. Integration with the GenAI Plugin

The Neo4j GenAI Plugin significantly enhances the usability of vector indexes by providing tools to generate and manage embeddings directly within the database.

*   **Embedding Generation:** The plugin offers functions like `ai.text.embed()` for generating a single embedding and `ai.text.embedBatch()` for generating embeddings for a batch of text data. This is highly efficient as it reduces the number of API calls to external embedding providers.

*   **Supported Providers:** The GenAI plugin supports a variety of popular embedding providers, including OpenAI, Azure OpenAI, Google Vertex AI, and Amazon Bedrock Titan Models.

### 2.3. Performance and Scalability

*   **HNSW Algorithm:** The use of the HNSW algorithm provides a good balance between search accuracy and performance, making it suitable for large-scale applications.

*   **Java Vector API:** For optimal performance, Neo4j can leverage the incubated Java Vector API, which can provide significant speed improvements. This requires a compatible Java version (Java 20 or later for Neo4j 5.x, and Java 21 for Neo4j 2025.01 or later).

*   **Quantization:** Neo4j supports quantization, a technique that reduces the memory footprint of vector embeddings by compressing them. This can be particularly useful when dealing with very large datasets.

## 3. Code Examples

This section provides a collection of code examples demonstrating how to work with Neo4j vector indexes, from creation to querying, including examples in both Cypher and Python.

### 3.1. Cypher Examples

#### Creating a Vector Index

```cypher
CREATE VECTOR INDEX moviePlots IF NOT EXISTS
FOR (m:Movie)
ON m.embedding
OPTIONS { indexConfig: {
 `vector.dimensions`: 1536,
 `vector.similarity_function`: 'cosine'
}}
```

#### Querying with the `SEARCH` Clause

```cypher
MATCH (m:Movie {title: 'The Godfather'})
MATCH (movie: Movie)
SEARCH movie IN (
    VECTOR INDEX moviePlots
    FOR m.embedding
    LIMIT 5
) SCORE AS score
RETURN movie.title AS title, movie.plot AS plot, score
```

#### Querying with the `db.index.vector.queryNodes()` Procedure

```cypher
MATCH (m:Movie {title: 'The Godfather'})
CALL db.index.vector.queryNodes('moviePlots', 5, m.embedding) YIELD node, score
RETURN node.title, node.plot, score
```

#### Generating Embeddings with the GenAI Plugin

```cypher
MATCH (m:Movie {title:'Godfather, The'})
WHERE m.plot IS NOT NULL AND m.title IS NOT NULL
WITH m, m.title + ' ' + m.plot AS titleAndPlot
WITH m, ai.text.embed(titleAndPlot, 'OpenAI', { token: $openaiToken, model: 'text-embedding-3-small' }) AS vector
SET m.embedding = vector
RETURN m.embedding AS embedding
```

### 3.2. Python Examples

The following examples utilize the `langchain` library to interact with Neo4j vector indexes from a Python application.

#### Creating a Vector Index from an Existing Graph

```python
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# Create the vectorstore for our existing graph
paper_graph = Neo4jVector.from_existing_graph(
    embedding=OpenAIEmbeddings(),
    url="bolt://localhost:7687",
    username="neo4j",
    password="password",
    index_name="paper_index",
    node_label="Paper",
    text_node_properties=["abstract", "title"],
    embedding_node_property="paper_embedding",
)
```

#### Performing a Similarity Search

```python
from pprint import pprint

result = paper_graph.similarity_search("dark matter field fluid model")
pprint(result[0].page_content)
```

## 4. Configuration Options and Best Practices

Proper configuration of vector indexes is crucial for achieving optimal performance and accuracy.

### 4.1. Index Configuration

When creating a vector index, you can specify several configuration options within the `OPTIONS` clause.

| Parameter                     | Description                                                                                             | Default Value |
| ----------------------------- | ------------------------------------------------------------------------------------------------------- | ------------- |
| `vector.dimensions`           | The dimensionality of the vectors.                                                                      | None          |
| `vector.similarity_function`  | The similarity function to use (`cosine` or `euclidean`).                                               | `cosine`      |
| `vector.quantization.enabled` | Enables or disables quantization to reduce the size of vector representations.                          | `true`        |
| `vector.hnsw.m`               | The maximum number of connections per node in the HNSW graph.                                           | `16`          |
| `vector.hnsw.ef_construction` | The number of nearest neighbors to track during index construction.                                     | `100`         |

### 4.2. Best Practices

*   **Choose the Right Similarity Function:** Use `cosine` for text embeddings and `euclidean` for other types of vector data.
*   **Set Vector Dimensions:** Always specify the `vector.dimensions` to ensure data integrity.
*   **Use Batching for Embedding Generation:** When generating embeddings for a large number of nodes or relationships, use the `ai.text.embedBatch()` procedure to improve efficiency.
*   **Leverage the Java Vector API:** For performance-critical applications, ensure you are using a compatible Java version to take advantage of the Java Vector API.
*   **Monitor Memory Usage:** Vector indexes can be memory-intensive. Monitor your database's memory usage and adjust your configuration as needed.

## 5. Relevance to Building AI Agent Applications with Neo4j

Neo4j's vector indexes are a cornerstone for building sophisticated AI agent applications that can reason and interact with knowledge graphs. By combining the power of graph traversals with semantic search, developers can create agents that have a deep understanding of the data and its relationships.

For a graph-native AI agent system like LLMitM v2, Neo4j's vector indexes provide the fundamental capability for semantic memory and retrieval. An agent can store its memories, observations, and knowledge as nodes in a graph, with their semantic meaning captured in vector embeddings. When the agent needs to recall relevant information, it can perform a similarity search on its memory graph, retrieving the most relevant memories based on the current context. This allows the agent to have a more human-like memory, where it can recall information based on meaning and context, rather than just keywords.

Furthermore, the ability to combine graph queries with vector search allows for powerful and nuanced retrieval strategies. For example, an agent could search for similar memories that are also connected to a specific person or event in the graph. This hybrid approach of combining structured and unstructured search is a key advantage of using Neo4j for AI agent development.

## 6. Limitations and Known Issues

While Neo4j's vector indexes are a powerful feature, there are some limitations and known issues to be aware of.

*   **Memory Consumption:** As with any HNSW-based implementation, vector indexes can be memory-intensive, especially for large datasets with high-dimensional vectors. Careful memory planning and configuration are essential.
*   **Dimension Limit:** The current implementation has a limit of 4096 dimensions for vectors. While this is sufficient for most common embedding models, it may be a limitation for some specialized use cases.
*   **Filtering:** While Neo4j supports pre- and post-filtering, the implementation of metadata filtering during the HNSW search is still in progress. This means that for queries with specific filtering conditions, you may need to retrieve a larger set of results and then filter them in a subsequent step.

## 7. Key Takeaways for Developers

For developers building graph-native AI agent systems, Neo4j's vector indexes offer a powerful and integrated solution for semantic search and memory.

*   **Embrace the Hybrid Approach:** The real power of Neo4j's vector indexes lies in the ability to combine them with graph traversals. This allows you to build sophisticated retrieval strategies that leverage both the semantic meaning of your data and its rich relationships.
*   **Understand the Trade-offs:** Be aware of the performance and memory trade-offs associated with vector indexes. Tune your configuration parameters and monitor your system's performance to ensure it meets your application's requirements.
*   **Stay Up-to-Date:** The field of vector search is rapidly evolving. Keep an eye on the latest Neo4j releases and documentation for new features, performance improvements, and best practices.

## 8. References

[1] Neo4j. (2026). *Vector indexes - Cypher Manual*. Retrieved from https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/

[2] Neo4j. (2026). *Neo4j Vector Index and Search - Developer Guides*. Retrieved from https://neo4j.com/developer/genai-ecosystem/vector-search/

[3] Sharma, S. (2024). *Building a Graph Database with Vector Embeddings: A Python Tutorial with Neo4j and Embeddings*. Medium. Retrieved from https://medium.com/thedeephub/building-a-graph-database-with-vector-embeddings-a-python-tutorial-with-neo4j-and-embeddings-277ce608634d

[4] Williams, C. (2024). *Elasticsearch vs Neo4j on Vector Search Capabilities - Zilliz blog*. Zilliz. Retrieved from https://zilliz.com/blog/elasticsearch-vs-neo4j-a-comprehensive-vector-database-comparison

[5] Hacker News. (2025). *Neo4j supports vector indexes*. Retrieved from https://news.ycombinator.com/item?id=43980247
