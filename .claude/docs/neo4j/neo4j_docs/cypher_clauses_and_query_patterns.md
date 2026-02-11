# Neo4j Cypher Clauses & Query Patterns: A Comprehensive Research Report

## MATCH Clause

The `MATCH` clause is the cornerstone of reading data from a Neo4j graph. It allows you to describe the patterns of nodes and relationships you are looking for. These patterns can be simple, like a single node, or complex, involving multiple nodes and relationships with specific properties and labels.

### Key Concepts

- **Patterns**: At the heart of the `MATCH` clause is the pattern. Patterns are expressed using an ASCII-art-like syntax that visually represents the graph structure you want to find.
- **Nodes**: Nodes are represented by parentheses, `()`. You can assign a variable to a node to reference it later, like `(n)`. To find nodes with a specific label, you use the syntax `(n:Label)`. You can also use label expressions to match nodes with one of several labels, `(n:Label1|Label2)`, or to exclude a label, `(n:!Label)`.
- **Relationships**: Relationships are represented by square brackets, `[]`, and arrows, `-->` or `<--`, to indicate direction. A relationship can also have a type, `-[r:REL_TYPE]->`, and you can use a `|` to match one of several types, `-[:TYPE1|TYPE2]-`.
- **Properties**: You can filter nodes and relationships by their properties using a map-like syntax within the parentheses or brackets, for example, `(p:Person {name: 'Keanu Reeves'})`.

### Common Usage

**Finding Nodes**

- To find all nodes in the graph (not recommended for large graphs): `MATCH (n) RETURN n`
- To find all nodes with a specific label: `MATCH (m:Movie) RETURN m`
- To find a node with a specific property: `MATCH (p:Person {name: 'Tom Hanks'}) RETURN p`

**Finding Relationships**

- To find all nodes connected to a specific node: `MATCH (:Person {name: 'Tom Hanks'})--(other) RETURN other`
- To find nodes connected by a specific relationship type: `MATCH (:Movie {title: 'The Matrix'})<-[:ACTED_IN]-(actor) RETURN actor.name`

**Multi-hop Traversals**

You can chain patterns together to traverse multiple relationships and discover more complex connections. For example, to find the directors of movies that Charlie Sheen acted in:

```cypher
MATCH (:Person {name: 'Charlie Sheen'})-[:ACTED_IN]->(movie:Movie)<-[:DIRECTED]-(director:Person)
RETURN movie.title, director.name
```

**Path Finding**

The `MATCH` clause can also be used to find paths between nodes. The `shortestPath()` and `allShortestPaths()` functions are particularly useful for this purpose.

```cypher
MATCH p = shortestPath((startNode)-[*]-(endNode))
RETURN p
```

## WHERE Clause

The `WHERE` clause is used to filter the results of a `MATCH` clause, allowing for more complex conditions than what can be expressed directly in the `MATCH` pattern. It can also be used to filter intermediate results when used with the `WITH` clause.

### Key Concepts

- **Filtering Patterns**: `WHERE` is not just a post-filter. The Cypher planner uses the conditions in the `WHERE` clause to optimize the query execution. It's an integral part of the pattern description.
- **Predicates**: The `WHERE` clause uses predicates, which are expressions that evaluate to `true` or `false`. These can include comparisons, boolean operators (`AND`, `OR`, `NOT`), and various functions.

### Common Usage

**Basic Filtering**

- **Filter by property**: `WHERE n.age < 35`
- **Filter by relationship property**: `WHERE r.since < 2000`
- **Filter by label**: `WHERE n:Swedish`

**Filtering with `WITH`**

When used with `WITH`, the `WHERE` clause filters the intermediate results before they are passed to the next part of the query.

```cypher
MATCH (n:Person)
WITH n.name AS name, n.age AS age
WHERE age > 30
RETURN name, age
```

**Inline `WHERE`**

Cypher also allows for an inline `WHERE` clause directly within a `MATCH` pattern. This can sometimes improve readability.

```cypher
MATCH (a:Person WHERE a.name = 'Andy')-[:KNOWS]->(b:Person WHERE b.age > 35)
RETURN b.name
```

## RETURN Clause

The `RETURN` clause is what makes a query a read query. It specifies what the query should output, defining the columns of the result set. You can return nodes, relationships, properties, literals, and the results of expressions and functions.

### Key Concepts

- **Projection**: `RETURN` projects the results of your query into a tabular format. You can return entire nodes and relationships, or just specific properties.
- **Aliasing**: The `AS` keyword allows you to rename the columns in your result set, which is useful for clarity and for client applications that consume the data.
- **Uniqueness**: The `DISTINCT` keyword ensures that you only get unique rows in your result set.

### Common Usage

**Returning Nodes, Relationships, and Properties**

- To return a node: `RETURN n`
- To return a relationship: `RETURN r`
- To return a specific property: `RETURN n.name`
- To return multiple properties: `RETURN n.name, n.age`

**Using Expressions and Functions**

You can return the result of any valid Cypher expression or function.

- **Literals**: `RETURN "Hello, World!"`
- **Predicates**: `RETURN n.age > 30`
- **Functions**: `RETURN count(n)`

**Aliasing and Distinct Results**

```cypher
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
RETURN DISTINCT m.title AS movieTitle
```

In this example, we are finding all the movies that any person has acted in, and returning a unique list of movie titles, with the column name `movieTitle`.

## CREATE Clause

The `CREATE` clause is used to add new nodes and relationships to the graph. It is a fundamental part of writing data to the database.

### Key Concepts

- **Creating Nodes**: You can create one or more nodes with labels and properties.

  ```cypher
  CREATE (p:Person {name: 'Alice', age: 30})
  ```

- **Creating Relationships**: You can create relationships between existing nodes or as part of a larger pattern.

  ```cypher
  MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
  CREATE (a)-[:KNOWS]->(b)
  ```

- **Creating Full Patterns**: You can create an entire pattern of nodes and relationships in a single `CREATE` clause.

  ```cypher
  CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})
  ```

### Important Considerations

- `CREATE` will always create new nodes and relationships, even if identical ones already exist. If you want to avoid creating duplicates, you should use the `MERGE` clause.
- You can use parameters to provide the properties for new nodes and relationships, which is essential for building applications and preventing Cypher injection.

  ```cypher
  CREATE (p:Person $props)
  ```

## MERGE Clause

The `MERGE` clause is a powerful feature that combines the functionality of `MATCH` and `CREATE`. It attempts to match a specified pattern, and if the pattern does not exist, it creates it. This is the primary way to avoid creating duplicate data in your graph.

### Key Concepts

- **"Find or Create"**: `MERGE` provides an idempotent way to ensure that a pattern exists in the graph. It's the perfect tool for "find or create" logic.
- **Whole Pattern Matching**: It's important to understand that `MERGE` matches on the *entire* pattern specified. If any part of the pattern doesn't match, the entire pattern will be created.
- **`ON CREATE` and `ON MATCH`**: These sub-clauses allow you to specify different actions to take depending on whether the pattern was found or created.

### Common Usage

**Merging a Single Node**

```cypher
MERGE (p:Person {name: 'Alice'})
RETURN p
```

This query will find a `Person` node with the name 'Alice' and return it. If no such node exists, it will be created first and then returned.

**Merging a Relationship**

```cypher
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
MERGE (a)-[:KNOWS]->(b)
```

This will create a `KNOWS` relationship between Alice and Bob, but only if one doesn't already exist.

**Using `ON CREATE` and `ON MATCH`**

```cypher
MERGE (p:Person {name: 'Alice'})
  ON CREATE SET p.created = timestamp()
  ON MATCH SET p.lastSeen = timestamp()
RETURN p
```

This query demonstrates how to perform different actions based on whether the node was created or matched. If the 'Alice' node is created, the `created` property is set. If it already exists, the `lastSeen` property is updated.

### Important Considerations

- For `MERGE` to be efficient, you should have an index or a uniqueness constraint on the properties you are merging on. This allows Neo4j to quickly find the node(s) you are trying to merge.
- `MERGE` on its own does not guarantee uniqueness in a concurrent environment. To enforce uniqueness, you must create a uniqueness constraint on the relevant node property.

## SET Clause

The `SET` clause is used to update data in your graph. You can use it to add or update properties on nodes and relationships, and to add labels to nodes.

### Key Concepts

- **Updating Properties**: You can set or update the value of a property on a node or relationship.
- **Adding Labels**: You can add one or more labels to a node.
- **Property Replacement**: The `=` operator replaces all existing properties on a node or relationship with a new set of properties.
- **Property Mutation**: The `+=` operator adds new properties and updates existing ones, without removing properties that are not in the provided map.

### Common Usage

**Setting a Property**

```cypher
MATCH (p:Person {name: 'Andy'})
SET p.age = 37
```

**Adding a Label**

```cypher
MATCH (p:Person {name: 'Andy'})
SET p:Developer
```

**Replacing All Properties**

```cypher
MATCH (p:Person {name: 'Andy'})
SET p = {name: 'Andrew', age: 37}
```

**Mutating Properties**

```cypher
MATCH (p:Person {name: 'Andy'})
SET p += {age: 37, city: 'Malmo'}
```

## WITH Clause

The `WITH` clause is a powerful tool for structuring complex Cypher queries. It allows you to chain query parts together, passing results from one part to the next. This enables you to perform intermediate manipulations, such as filtering, aggregation, and ordering, before the final `RETURN` clause.

### Key Concepts

- **Chaining Queries**: `WITH` acts as a bridge between different parts of a query, allowing you to build up complex logic step-by-step.
- **Filtering**: You can use `WHERE` with `WITH` to filter intermediate results.
- **Aggregation**: `WITH` is essential for performing aggregations in the middle of a query.
- **Controlling Scope**: `WITH` controls which variables are passed to the next part of the query. If you don't explicitly include a variable in the `WITH` clause, it will be dropped from the scope. You can use `WITH *` to pass all variables.

### Common Usage

**Filtering and Aggregating**

```cypher
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
WITH p, count(m) AS movies_acted_in
WHERE movies_acted_in > 5
RETURN p.name, movies_acted_in
```

In this example, the `WITH` clause is used to aggregate the number of movies each person has acted in. The subsequent `WHERE` clause then filters these results to find people who have acted in more than five movies.

**Ordering and Pagination**

```cypher
MATCH (p:Person)
WITH p
ORDER BY p.name
SKIP 10
LIMIT 5
RETURN p.name
```

Here, `WITH` is used to pass the `p` variable to the ordering and pagination clauses before the final `RETURN`.

## Core Cypher Concepts

Cypher is a declarative graph query language, meaning you describe what you want to find, not how to find it. It uses an intuitive, ASCII-art-like syntax to represent graph patterns, making queries easy to read and understand.

### The Building Blocks of a Graph

- **Nodes**: Nodes are the fundamental entities in a graph. They can have zero or more labels, which are used to group nodes together, and properties, which are key-value pairs that store data about the node.
- **Relationships**: Relationships connect nodes and give the graph its structure. They have a type, a direction, a start node, and an end node. Relationships can also have properties.
- **Paths**: A path is a sequence of alternating nodes and relationships. Traversing paths is a core concept in graph databases and is central to how Cypher queries work.

### A Simple Cypher Query

```cypher
MATCH (p:Person {name: 'Anna'})-[:KNOWS]->(friend:Person)
WHERE friend.born < p.born
RETURN friend.name, friend.born
```

This query demonstrates the basic structure of a Cypher query. It finds all the friends of a person named Anna who are younger than her. The `MATCH` clause defines the pattern to search for, the `WHERE` clause filters the results, and the `RETURN` clause specifies what data to output.

## Basic Querying

This section covers the fundamental operations of creating, reading, and deleting data in a Neo4j graph database using Cypher.

### Creating Data

Before you start creating data, it is important to have a clear data model in mind. This model will define the different types of nodes (labels), the relationships between them, and the properties that each node and relationship will have. Once you have a data model, you can use the `CREATE` clause to bring your graph to life.

```cypher
CREATE (p:Person {name: 'Keanu Reeves', born: 1964})
```

### Reading Data

The `MATCH` clause is your primary tool for reading data from the graph. You can use it to find nodes and relationships that fit a specific pattern.

```cypher
MATCH (p:Person {name: 'Keanu Reeves'})
RETURN p
```

To find connected nodes, you simply extend the pattern in your `MATCH` clause to include a relationship.

```cypher
MATCH (m:Movie {title: 'The Matrix'})<-[:DIRECTED]-(p:Person)
RETURN p.name
```

### Finding Paths

Cypher excels at finding paths between nodes. You can search for paths of a fixed length or a variable length.

**Fixed-Length Paths**

```cypher
MATCH (p:Person {name: 'Tom Hanks'})--{2}(colleague:Person)
RETURN DISTINCT colleague.name
```

**Variable-Length Paths**

```cypher
MATCH (p:Person {name: 'Tom Hanks'})--{1,4}(colleague:Person)
RETURN DISTINCT colleague.name
```

### Deleting Data

The `DELETE` clause is used to remove nodes and relationships from the graph. To delete a node, you must first delete all of its relationships. The `DETACH DELETE` clause provides a convenient way to do both in a single step.

```cypher
MATCH (p:Person {name: 'Keanu Reeves'})
DETACH DELETE p
```

## Execution Plans and Query Tuning

Understanding how Cypher queries are executed is crucial for writing high-performance queries. Every Cypher query is transformed into an execution plan, which is a tree of operators that describes the step-by-step execution of the query.

### `EXPLAIN` and `PROFILE`

Cypher provides two powerful tools for analyzing execution plans:

- **`EXPLAIN`**: This clause shows you the execution plan for a query without actually running it. This is useful for getting a quick idea of how a query will be executed.
- **`PROFILE`**: This clause runs the query and provides a detailed breakdown of the execution plan, including the number of database hits for each operator. This is invaluable for identifying performance bottlenecks.

### Query Tuning Strategies

There are several key strategies for tuning Cypher queries:

- **Use Indexes**: Indexes are the most important tool for improving query performance. They allow the database to quickly find the starting nodes for a query, avoiding costly full graph scans.
- **Use Constraints**: Constraints, such as uniqueness constraints, provide the query planner with valuable information about your data, which can lead to more efficient execution plans.
- **Choose the Right Clauses**: Different clauses have different performance characteristics. For example, `OPTIONAL MATCH` can be more expensive than `MATCH`.
- **Use Planner Hints**: In some cases, you may need to guide the query planner with hints, such as `USING INDEX` or `USING SCAN`. These should be used with caution, as they can sometimes lead to slower queries if not used correctly.

## Advanced Query Tuning

Query tuning is the art and science of optimizing Cypher queries for maximum performance. The primary goal is to minimize the amount of data retrieved from the graph and to ensure that queries execute as quickly as possible.

### General Recommendations

- **Filter Early**: Apply filters as early as possible in your query to reduce the amount of data that needs to be processed in later stages.
- **Return Only What You Need**: Avoid returning entire nodes and relationships. Instead, be specific about the properties you need.
- **Limit Variable-Length Patterns**: Always set an upper bound on variable-length patterns to prevent them from traversing large portions of the graph unexpectedly.
- **Use Parameters**: Use parameters instead of literals in your queries. This allows Cypher to cache and reuse execution plans, which can significantly improve performance for frequently executed queries.

### Cypher Planner Options

Cypher provides several options to influence the query planner's behavior. These are specified at the beginning of a query using the `CYPHER` keyword.

- **`planner=cost`**: This is the default planner, which uses a cost-based algorithm to find an efficient execution plan.
- **`planner=dp`**: This planner performs an exhaustive search for the best possible execution plan. It may find a better plan than the cost-based planner, but it can also take significantly longer to plan the query.

### Replanning

Cypher caches execution plans to avoid the overhead of planning the same query multiple times. However, there are times when you may want to force a replan, for example, after the data in the graph has changed significantly. The `replan` option gives you control over this behavior.

- **`replan=force`**: Forces a replan of the query, even if a valid plan is already in the cache.
- **`replan=skip`**: Skips replanning, even if the planner would normally choose to replan.

## Cypher Style Guide

A consistent coding style is crucial for writing readable and maintainable Cypher queries. The official Cypher style guide provides a set of recommendations to help you write clean and elegant code.

### Key Recommendations

- **Casing**: Write keywords in upper case (e.g., `MATCH`, `WHERE`, `RETURN`) and everything else (variables, labels, properties, functions) in camel case starting with a lower-case letter.
- **Indentation and Line Breaks**: Start each new clause on a new line. Indent sub-clauses like `ON CREATE` and `ON MATCH`. Limit line length to 80 characters for better readability.
- **Spacing**: Use a single space after commas and around operators. Do not use spaces within patterns.
- **Patterns**: When patterns need to wrap to a new line, break after the arrows, not before. Use anonymous nodes and relationships when you don't need to reference them later in the query.

## Relevance to Building AI Agent Applications with Neo4j

Cypher is a powerful tool for building AI agent applications that leverage the knowledge stored in a Neo4j graph. Here's how it can be applied:

*   **Knowledge Representation**: The graph model is a natural way to represent the complex, interconnected knowledge that AI agents need to operate. Cypher allows you to create, update, and query this knowledge base with ease.
*   **Complex Pattern Matching**: AI agents often need to identify complex patterns and relationships in data. Cypher's powerful pattern matching capabilities are ideal for this task. For example, an agent could use Cypher to find all the people who are connected to a particular organization and have a specific skill set.
*   **Multi-hop Traversals for Reasoning**: Many AI reasoning tasks involve traversing multiple steps in a knowledge graph. Cypher's multi-hop traversal capabilities allow agents to explore these connections and draw inferences.
*   **Dynamic Queries**: AI agents need to be able to generate queries on the fly based on their current context and goals. Cypher's support for parameters and dynamic property access makes it well-suited for this purpose.

## Limitations and Known Issues

While Cypher is a powerful language, it has some limitations:

*   **Procedural Logic**: Cypher is a declarative language, which means it is not well-suited for writing complex procedural logic. For tasks that require a lot of procedural code, it is often better to use a general-purpose programming language and the Neo4j drivers.
*   **Subqueries**: While Cypher has support for subqueries, they can sometimes be complex to write and reason about.
*   **Performance**: While Cypher is generally performant, poorly written queries can be slow. It is important to understand the basics of query tuning to write efficient queries.

## Key Takeaways for a Developer Building a Graph-Native AI Agent System

*   **Embrace the Graph Model**: The graph model is a powerful tool for representing knowledge. Take the time to design a data model that accurately reflects the entities and relationships in your domain.
*   **Master Cypher**: A deep understanding of Cypher is essential for building effective AI agent applications with Neo4j. Pay close attention to the nuances of the language, especially when it comes to pattern matching, filtering, and aggregation.
*   **Think in Patterns**: When you are writing Cypher queries, think in terms of patterns. What are the patterns of nodes and relationships that you are trying to find? How can you express those patterns in Cypher?
*   **Profile and Tune Your Queries**: Don't assume that your queries are performant. Use the `PROFILE` clause to analyze the execution plan and identify any bottlenecks. A little bit of query tuning can go a long way.
*   **Use Parameters**: Always use parameters in your queries to prevent Cypher injection and to allow the database to cache execution plans.

## References

*   [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
*   [Tuning Your Cypher: Tips & Tricks for More Effective Queries](https://neo4j.com/blog/cypher-and-gql/tuning-cypher-queries/)
