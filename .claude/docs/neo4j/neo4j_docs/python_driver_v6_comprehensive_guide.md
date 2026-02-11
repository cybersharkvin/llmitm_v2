# Neo4j Python Driver v6: A Comprehensive Guide

This report provides a comprehensive overview of the Neo4j Python Driver v6, covering its features, usage, and best practices. It is intended for developers and technical researchers who want to leverage the power of Neo4j in their Python applications.

## 1. Installation and Setup

The official Neo4j Python driver can be installed using pip. It is compatible with a range of Neo4j server versions, ensuring flexibility for different environments.

### 1.1. Driver Installation

The driver is installed via pip:

```bash
pip install neo4j
```

The driver requires Python 3.10 or newer. For a significant performance boost (3x to 10x), a Rust-based extension is available as a drop-in replacement:

```bash
pip install neo4j-rust-ext
```

### 1.2. Neo4j Database Setup

To use the driver, you need a running Neo4j database. Here are a few ways to set one up:

A convenient way to run a local instance is with Docker.

    ```bash
    docker run \
        -p7474:7474 \
        -p7687:7687 \
        -d \
        -e NEO4J_AUTH=neo4j/password \
        neo4j:latest
    ```

Neo4j Aura is a fully managed cloud service from Neo4j.
You can also download and install Neo4j directly on your machine.

## 2. Connecting to the Database

Establishing a connection to a Neo4j database is the first step in any application. The driver provides a robust and flexible connection management system.

### 2.1. The Driver Object

A `Driver` object is the central point of interaction with the database. It is created using `GraphDatabase.driver()` and configured with the database URI and authentication credentials.

```python
from neo4j import GraphDatabase

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "password")

driver = GraphDatabase.driver(URI, auth=AUTH)

# Verify that the connection is successful
driver.verify_connectivity()

# Close the driver when it's no longer needed
driver.close()
```

It is a best practice to maintain a single `Driver` instance throughout the lifecycle of the application, as it is a thread-safe but expensive object to create.

### 2.2. Connection URIs and Schemes

The driver supports various URI schemes to control encryption and routing:

| Scheme      | Encryption                      | Routing | Comment                                   |
|-------------|---------------------------------|---------|-------------------------------------------|
| `neo4j`     | No                              | Yes     | Default for local setups.                 |
| `neo4j+s`   | Yes (CA-signed certificates)    | Yes     | Default for Aura.                         |
| `neo4j+ssc` | Yes (CA- and self-signed certs) | Yes     |                                           |
| `bolt`      | No                              | No      | Direct connection to a single server.     |
| `bolt+s`    | Yes (CA-signed certificates)    | No      | Direct connection with encryption.        |
| `bolt+ssc`  | Yes (CA- and self-signed certs) | No      | Direct connection with encryption.        |

### 2.3. Authentication

The driver supports multiple authentication mechanisms:

The default authentication method is basic authentication, which uses a username and password.
For enterprise environments with Kerberos integration, Kerberos authentication is supported.
Bearer authentication can be used with SSO and identity providers.
The driver also allows for the implementation of custom authentication logic.
Mutual TLS (mTLS) provides a second factor of authentication using client-side certificates.

### 2.4. Advanced Connection Management

For more complex scenarios, the driver offers advanced features:

For more complex scenarios, the driver offers advanced features such as rotating authentication tokens. The `AuthManagers` class can be used to handle expiring authentication tokens, such as those from SSO providers.
A custom address resolver function can be provided to the driver to control how it resolves database addresses, which is useful in dynamic environments or for custom routing logic.

## 3. Querying the Database

The `Driver.execute_query()` method is the most direct way to interact with the database. It simplifies query execution by managing sessions and transactions automatically.

### 3.1. Basic CRUD Operations

The driver supports all standard Cypher operations for creating, reading, updating, and deleting data.

```python
# Create a node
records, summary, keys = driver.execute_query(
    "CREATE (p:Person {name: $name})",
    name="Alice"
)

# Read data
records, summary, keys = driver.execute_query("MATCH (p:Person) RETURN p.name AS name")
for record in records:
    print(record["name"])

# Update data
records, summary, keys = driver.execute_query(
    "MATCH (p:Person {name: $name}) SET p.age = $age",
    name="Alice", age=30
)

# Delete data
records, summary, keys = driver.execute_query(
    "MATCH (p:Person {name: $name}) DETACH DELETE p",
    name="Alice"
)
```

### 3.2. Parameterization

Using parameters is essential for security and performance. The driver handles the conversion of Python types to their Cypher equivalents.

```python
# Using keyword arguments
driver.execute_query(
    "CREATE (p:Person {name: $name, born: $born})",
    name="Alice", born=1990
)

# Using a dictionary
driver.execute_query(
    "CREATE (p:Person {name: $name, born: $born})",
    parameters_={'name': 'Bob', 'born': 1985}
)
```

### 3.3. Error Handling and Retries

The driver automatically retries transactions that fail due to transient errors. For other errors, it raises a `Neo4jError`. You can inspect the error code to handle specific issues.

```python
from neo4j.exceptions import Neo4jError

try:
    driver.execute_query("invalid query")
except Neo4jError as e:
    print(f"Error {e.code}: {e.message}")
```

### 3.4. Query Configuration

You can configure query execution using special keyword arguments:

You can configure query execution using special keyword arguments such as `database_` to specify the target database.
`impersonated_user_` to run the query as a different user, and
`result_transformer_` which is a function to process the raw `EagerResult` object before it is returned.

## 4. Manipulating Query Results

The `EagerResult` object returned by `execute_query()` provides a convenient way to work with query results. The driver also offers built-in and custom transformers to process the results in various formats.

### 4.1. The `EagerResult` Object

The `EagerResult` object is a named tuple containing:

The `EagerResult` object is a named tuple containing `records`, a list of `Record` objects that behave like dictionaries;
`summary`, a `ResultSummary` object with metadata about the query execution; and
`keys`, a list of the result column names.

```python
records, summary, keys = driver.execute_query("MATCH (p:Person) RETURN p.name AS name, p.age AS age")

for record in records:
    print(f"{record['name']} is {record['age']} years old.")
```

### 4.2. Result Transformers

The `result_transformer_` argument allows you to transform the result into different formats.

If `pandas` is installed, you can convert the result to a DataFrame.

    ```python
    import neo4j

    df = driver.execute_query(
        "MATCH (p:Person) RETURN p.name AS name, p.age AS age",
        result_transformer_=neo4j.Result.to_df
    )
    print(df)
    ```

For queries returning graph structures, you can transform the result into a `Graph` object.

    ```python
    import neo4j

    graph = driver.execute_query(
        "MATCH (p:Person)-[r:KNOWS]->(f:Person) RETURN p, r, f LIMIT 1",
        result_transformer_=neo4j.Result.graph
    )
    print(graph)
    ```

You can also provide a custom function to process the result in any way you need.

    ```python
    def my_transformer(result):
        return [record['name'] for record in result]

    names = driver.execute_query(
        "MATCH (p:Person) RETURN p.name AS name",
        result_transformer_=my_transformer
    )
    print(names)
    ```
## 5. Sessions and Transactions

While `Driver.execute_query()` implicitly handles transactions, the driver also provides mechanisms for explicit transaction management, which is essential for more complex, multi-step database operations.

### Sessions

Transactions are managed within a **Session**. A session is obtained from the driver using `driver.session()`.
Sessions are lightweight and should be created for a specific task and then closed. The `with` statement is the recommended way to ensure sessions are properly closed.
**Sessions are not thread-safe.** Each thread should have its own session, although the `Driver` object itself is thread-safe and can be shared.
Sessions ensure **causal consistency**, meaning that a read transaction within a session will see the writes of a previous transaction in the same session.

### 5.1. Managed Transactions (Recommended)

The recommended way to handle transactions is through managed transactions, which automatically handle retries for transient errors.

```python
def create_person(tx, name):
    tx.run("CREATE (p:Person {name: $name})", name=name)

with driver.session() as session:
    session.execute_write(create_person, "Alice")
```


The recommended way to handle transactions is through **managed transactions**, which automatically handle retries for transient errors.

The driver provides `session.execute_read(transaction_function, ...)` for read-only transactions and
`session.execute_write(transaction_function, ...)` for transactions that modify the database.

These methods take a **transaction function** as the first argument. This function receives a `Transaction` object (`tx`) and is where you execute your queries using `tx.run()`.

These methods take a **transaction function** as the first argument. This function receives a `Transaction` object (`tx`) and is where you execute your queries using `tx.run()`. The transaction function should be **idempotent**, as it might be executed multiple times in case of retries.
The transaction is **committed** if the function returns normally, and
it is **rolled back** if the function raises an exception.
It is important to **never return a `Result` object directly** from a transaction function. Always process it (e.g., by converting it to a list) before returning.

### 5.2. Explicit Transactions

For scenarios requiring more control, you can use explicit transactions. This approach gives you full control but requires manual handling of commits, rollbacks, and retries.

```python
with driver.session() as session:
    tx = session.begin_transaction()
    try:
        tx.run("CREATE (p:Person {name: $name})", name="Bob")
        tx.commit()
    except Exception as e:
        tx.rollback()
        raise e
```
```
```
```
```








































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































	```	```	```	```	```	```	```	```

For scenarios requiring more control, you can use **explicit transactions**.

You can use `session.begin_transaction()` to start a new transaction and return a `Transaction` object.
`transaction.run(query, ...)` to execute a query within the transaction,
`transaction.commit()` to commit the transaction, and
`transaction.rollback()` to roll back the transaction.

This approach gives you full control but requires manual handling of commits, rollbacks, and retries.

### Transaction Configuration
The `@unit_of_work()` decorator can be used to configure transaction functions, allowing you to set a `timeout` and attach `metadata` for logging and monitoring purposes.
## 6. Query Execution Summary

The `ResultSummary` object provides detailed information about the execution of a query. This is invaluable for monitoring, debugging, and performance tuning.

### 6.1. Accessing the Summary

When using `driver.execute_query()`, the summary is returned as the second element of the result tuple. In transaction functions, you can get the summary by calling `result.consume()` after processing all records.

### 6.2. Query Counters

The `summary.counters` attribute provides a breakdown of the write operations performed by the query:

```python
records, summary, keys = driver.execute_query("CREATE (p:Person {name: $name})", name="Alice")

print(f"Nodes created: {summary.counters.nodes_created}")
print(f"Relationships created: {summary.counters.relationships_created}")
```

### 6.3. Execution Plan and Profiling

To analyze and optimize query performance, you can use the `EXPLAIN` and `PROFILE` keywords.

*   **`EXPLAIN`**: Returns the query's execution plan without running it.
*   **`PROFILE`**: Executes the query and returns the plan with detailed performance metrics.

```python
# Get the execution plan
records, summary, keys = driver.execute_query("EXPLAIN MATCH (p:Person) RETURN p.name")
print(summary.plan)

# Get the profiled execution plan
records, summary, keys = driver.execute_query("PROFILE MATCH (p:Person) RETURN p.name")
print(summary.profile)
```

### 6.4. Notifications

The server may send notifications about performance issues or deprecated features. These are available in the `summary.gql_status_objects` list.

## 7. Parallel and Concurrent Transactions

The driver provides mechanisms for managing both parallel and concurrent transactions, which are crucial for building scalable and high-performance applications.

### 7.1. Causal Consistency and Bookmarks

In a clustered environment, **bookmarks** are used to ensure **causal consistency**, guaranteeing that a transaction can read the writes of a previous one, even if they are executed on different servers. The driver automatically manages bookmarks for consecutive `execute_query()` calls and within a single session. For coordinating transactions across multiple sessions, manual bookmark management is required.

```python
# Manual bookmark management
with driver.session() as session1:
    session1.execute_write(lambda tx: tx.run("CREATE (p:Person {name: 'Alice'})"))
    bookmarks = session1.last_bookmarks()

with driver.session(bookmarks=bookmarks) as session2:
    records, _, _ = session2.execute_read(lambda tx: tx.run("MATCH (p:Person) RETURN p.name AS name").data())
    print([record['name'] for record in records]) # Guaranteed to see 'Alice'
```

### 7.2. Asynchronous Operations with `asyncio`

The driver offers full support for Python's `asyncio` library, enabling concurrent I/O operations for improved performance. The `AsyncGraphDatabase.driver()` creates an `AsyncDriver` with an API that mirrors the synchronous version, but with `async` and `await` keywords.

```python
import asyncio
from neo4j import AsyncGraphDatabase

async def main():
    async with AsyncGraphDatabase.driver(URI, auth=AUTH) as driver:
        records, summary, keys = await driver.execute_query("MATCH (p:Person) RETURN p.name AS name")
        print([record['name'] for record in records])

if __name__ == "__main__":
    asyncio.run(main())
```

## 8. Performance Recommendations

To get the best performance out of the Neo4j Python driver, consider the following best practices:

For a significant speed boost, you can install the `neo4j-rust-ext` package.
Always provide the `database_` parameter to avoid extra round-trips to the server.
Group multiple queries into a single transaction to reduce overhead.
For large result sets, use `session.execute_read()` or `session.execute_write()` and iterate over the `Result` object instead of converting it to a list. This streams the results and reduces memory consumption.
Create indexes on frequently queried properties to speed up lookups.
Use `EXPLAIN` and `PROFILE` to analyze and optimize your Cypher queries.
In a clustered setup, route read queries to follower nodes to distribute the load.

## 9. Data Types

The driver handles the mapping between Python types and Cypher types, allowing for seamless data exchange.

### 9.1. Core Types

The driver automatically converts standard Python types to their corresponding Cypher types:

| Python Type | Cypher Type |
|-------------|-------------|
| `None`      | `NULL`      |
| `list`      | `LIST`      |
| `dict`      | `MAP`       |
| `bool`      | `BOOLEAN`   |
| `int`       | `INTEGER`   |
| `float`     | `FLOAT`     |
| `str`       | `STRING`    |
| `bytearray` | `ByteArray` |

### 9.2. Temporal and Spatial Types

For more specialized data types, the driver provides the `neo4j.time` and `neo4j.spatial` modules. These modules offer types that are compatible with Cypher's temporal and spatial types, such as `Date`, `Time`, `DateTime`, `Duration`, `CartesianPoint`, and `WGS84Point`.

### 9.3. Graph Types

When a query returns graph structures, the driver uses the `neo4j.graph` module to represent them. The main types are:

When a query returns graph structures, the driver uses the `neo4j.graph` module to represent them. The main types are `Node`, which represents a node in the graph, with properties like `element_id`, `labels`, and a dictionary of properties;
`Relationship`, which represents a relationship, with properties like `element_id`, `start_node`, `end_node`, `type`, and a dictionary of properties; and
`Path`, which represents a sequence of nodes and relationships.

These graph types are only returned from the database and cannot be used as query parameters.

### 9.4. Vector Type

Introduced in version 6.0, the `Vector` type maps to the Cypher `VECTOR` type, which is used for storing and querying high-dimensional vector embeddings. This is a key feature for building AI applications, such as similarity search and recommendation engines.

## 10. Relevance to Building a Graph-Native AI Agent System

The Neo4j Python Driver v6 is a critical component for building a graph-native AI agent system like LLMitM v2. Its robust feature set for managing connections, executing queries, and handling complex data types makes it an ideal choice for interacting with a Neo4j database, which can serve as the core knowledge graph for an AI agent. The driver's support for asynchronous operations with `asyncio` is particularly relevant for building high-performance, concurrent agent systems that can handle multiple tasks and user interactions simultaneously. Furthermore, the new `Vector` type is essential for implementing advanced AI capabilities, such as semantic search and similarity-based reasoning over the knowledge graph, which are fundamental for an intelligent agent.

## 11. Key Findings

This research has provided a comprehensive overview of the Neo4j Python Driver v6, a powerful and feature-rich library for connecting Python applications to Neo4j databases. The key findings of this research are:

The driver offers a complete set of features for managing the entire lifecycle of a Neo4j-backed application, from initial connection and configuration to complex query execution and result processing.
With features like connection pooling, asynchronous I/O, and the optional Rust extension, the driver is designed for high-performance and scalable applications.
The driver provides both implicit and explicit transaction management, with automatic retries for transient errors, ensuring data integrity and consistency.
The driver supports a wide range of data types, including temporal, spatial, and the new `Vector` type, enabling the development of sophisticated, data-intensive applications.
The driver's API is well-documented and intuitive, with features like result transformers and detailed query summaries that simplify development and debugging.

In conclusion, the Neo4j Python Driver v6 is a mature and powerful tool that is well-suited for a wide range of applications, from simple data-driven websites to complex, graph-native AI agent systems.

## References

[1] [Neo4j Python Driver Manual](https://neo4j.com/docs/python-manual/current/)
[2] [Neo4j Python Driver — Quickstart](https://neo4j.com/docs/python-manual/current/getting-started/)
[3] [Neo4j Python Driver — Connecting to the Database](https://neo4j.com/docs/python-manual/current/driver-connections/)
[4] [Neo4j Python Driver — Query the Database](https://neo4j.com/docs/python-manual/current/query-simple/)
[5] [Neo4j Python Driver — Transactions](https://neo4j.com/docs/python-manual/current/transactions/)
[6] [Neo4j Python Driver — Performance Recommendations](https://neo4j.com/docs/python-manual/current/performance/)
[7] [Neo4j Python Driver — Data Types](https://neo4j.com/docs/python-manual/current/cypher-values/)
[8] [Neo4j Blog — Driver Best Practices](https://neo4j.com/blog/developer/neo4j-driver-best-practices/)
