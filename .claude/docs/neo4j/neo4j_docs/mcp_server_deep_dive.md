# Neo4j MCP (Model Context Protocol) Server: A Deep Dive

## 1. Introduction to Neo4j MCP

The Neo4j Model Context Protocol (MCP) is a groundbreaking open protocol designed to standardize the way Large Language Models (LLMs) interact with external tools and data sources. It provides a clean, modular architecture for connecting LLMs to various backend systems, with a particular focus on graph databases like Neo4j. The Neo4j MCP Server is the official implementation of this protocol for the Neo4j ecosystem, enabling AI agents to seamlessly and intelligently interact with Neo4j databases.

This report provides a comprehensive, technical deep dive into the Neo4j MCP Server. We will explore its architecture, features, and capabilities, and provide practical guidance on how to install, configure, and use it to build powerful, graph-native AI agent applications. This research is based on the official Neo4j MCP documentation [1], the official GitHub repository [2], and various technical blog posts and tutorials [3, 4, 5].

## 2. Core Concepts

The Neo4j MCP Server acts as a bridge between an LLM-powered agent and a Neo4j database. It exposes a set of tools that the agent can invoke to perform various operations on the database, such as querying for information, retrieving the database schema, and even modifying the data. The MCP server handles the translation of the agent's requests into Cypher queries, executes them against the database, and returns the results to the agent in a structured format.

This architecture offers several key advantages:

*   **Standardization:** MCP provides a standardized way for LLMs to interact with external tools, making it easier to build and maintain AI agents that can leverage a variety of different services.
*   **Modularity:** The modular design of MCP allows for the separation of concerns between the agent's logic and the specifics of the backend system. This makes it easier to develop and maintain both the agent and the tools it uses.
*   **Security:** The MCP server provides a secure way to expose a Neo4j database to an AI agent. It allows for fine-grained control over the operations that the agent can perform, and it supports secure communication via TLS/HTTPS.
*   **Discoverability:** The MCP server allows an agent to discover the available tools and their capabilities at runtime. This enables the agent to adapt its behavior to the specific tools that are available.

## 3. Installation and Configuration

The Neo4j MCP Server is a lightweight, standalone binary that can be easily installed on a variety of platforms. It can be installed via Homebrew on macOS or by downloading the binary from the official GitHub releases page for other operating systems.

### 3.1. Prerequisites

Before installing the Neo4j MCP Server, you need to have the following:

*   A running Neo4j database instance (Aura, Desktop, or self-managed).
*   The APOC (Awesome Procedures on Cypher) plugin installed in your Neo4j instance.
*   An MCP-compatible client, such as VSCode with MCP support or Claude Desktop.

### 3.2. Installation

**Homebrew (macOS):**

```bash
brew install neo4j-mcp
```

**Manual Installation (Linux, Windows):**

1.  Download the appropriate binary for your operating system and architecture from the [GitHub releases page](https://github.com/neo4j/mcp/releases).
2.  Extract the archive and place the `neo4j-mcp` (or `neo4j-mcp.exe`) executable in a directory that is in your system's PATH.

### 3.3. Configuration

The Neo4j MCP Server is configured using environment variables or command-line flags. Command-line flags take precedence over environment variables.

**Key Configuration Options:**

| Environment Variable | Command-Line Flag | Description | Default |
| --- | --- | --- | --- |
| `NEO4J_URI` | `--neo4j-uri` | The connection URI for your Neo4j database. | (none) |
| `NEO4J_USERNAME` | `--neo4j-username` | The username for your Neo4j database. | (none) |
| `NEO4J_PASSWORD` | `--neo4j-password` | The password for your Neo4j database. | (none) |
| `NEO4J_DATABASE` | `--neo4j-database` | The name of the Neo4j database to connect to. | `neo4j` |
| `NEO4J_READ_ONLY` | `--neo4j-read-only` | Set to `true` to disable write operations. | `false` |
| `NEO4J_TRANSPORT_MODE` | `--neo4j-transport-mode` | The transport mode to use (`stdio` or `http`). | `stdio` |

## 4. Exposed Tools and Capabilities

The Neo4j MCP Server exposes a set of tools that an AI agent can use to interact with a Neo4j database. These tools are designed to be simple and intuitive, and they provide a powerful set of capabilities for working with graph data.

**Available Tools:**

| Tool | Read-Only | Purpose | Notes |
| --- | --- | --- | --- |
| `get-schema` | Yes | Introspects the database schema (labels, relationship types, property keys). | Provides valuable context to the LLM. |
| `read-cypher` | Yes | Executes arbitrary read-only Cypher queries. | Rejects write operations. |
| `write-cypher` | No | Executes arbitrary write Cypher queries. | Disabled in read-only mode. |
| `list-gds-procedures` | Yes | Lists available Graph Data Science (GDS) procedures. | Helps the LLM discover available GDS procedures. |

These tools empower an LLM agent to perform a wide range of tasks, from simple data retrieval to complex graph analysis and modification. For example, an agent could use the `get-schema` tool to understand the structure of a graph, the `read-cypher` tool to query for specific information, and the `write-cypher` tool to add new data to the graph.

## 5. Transport Modes

The Neo4j MCP Server supports two transport modes: `stdio` and `http`.

### 5.1. STDIO Mode

STDIO (Standard Input/Output) mode is the default transport mode. In this mode, the MCP server communicates with the client over standard input and output. This mode is suitable for desktop clients like VSCode and Claude Desktop, where the MCP server is run as a local process.

### 5.2. HTTP Mode

HTTP mode allows the MCP server to be run as a web server. In this mode, the client communicates with the server over HTTP. This mode is suitable for web-based clients and multi-tenant scenarios, where a single MCP server can be used to serve multiple clients.

## 6. Authentication

The Neo4j MCP Server supports two authentication methods in HTTP mode: Basic Authentication and Bearer Token Authentication.

### 6.1. Basic Authentication

Basic Authentication is a simple authentication scheme that uses a username and password to authenticate the client. The credentials are sent in the `Authorization` header of the HTTP request, encoded in Base64.

**Example `curl` request:**

```bash
curl -u neo4j:password -X POST http://localhost:8080/mcp -d '...'
```

### 6.2. Bearer Token Authentication

Bearer Token Authentication is a more secure authentication scheme that uses a token to authenticate the client. The token is sent in the `Authorization` header of the HTTP request.

**Example `curl` request:**

```bash
curl -H "Authorization: Bearer <token>" -X POST http://localhost:8080/mcp -d '...'
```

## 7. Security: TLS/HTTPS

When running in HTTP mode, the Neo4j MCP Server can be configured to use TLS/HTTPS to secure the communication between the client and the server. This is highly recommended for production environments.

To enable TLS/HTTPS, you need to set the `NEO4J_MCP_HTTP_TLS_ENABLED` environment variable to `true` and provide the paths to your TLS certificate and key files.

**Example Configuration:**

```bash
export NEO4J_MCP_HTTP_TLS_ENABLED=true
export NEO4J_MCP_HTTP_TLS_CERT_FILE=/path/to/cert.pem
export NEO4J_MCP_HTTP_TLS_KEY_FILE=/path/to/key.pem
```

## 8. Building AI Agents with Neo4j MCP

The Neo4j MCP Server is a powerful tool for building AI agents that can leverage the power of graph databases. By providing a standardized way for LLMs to interact with Neo4j, the MCP server makes it easier to build and maintain sophisticated, graph-native AI applications.

One of the key benefits of using Neo4j with an AI agent is the ability to represent and reason about complex relationships in data. This is particularly useful for applications such as knowledge graphs, recommendation engines, and fraud detection systems.

For a developer building a graph-native AI agent system like LLMitM v2, the Neo4j MCP Server provides a critical piece of infrastructure. It allows the agent to offload the complexities of interacting with a Neo4j database to a dedicated server, and it provides a standardized set of tools that the agent can use to perform a wide range of graph-related tasks.

## 9. Limitations and Known Issues

While the Neo4j MCP Server is a powerful and flexible tool, it is still a relatively new technology and has some limitations and known issues. For example, there is a known issue with Neo4j version 5.18 that causes the `get-schema` tool to fail. This issue is fixed in version 5.19 and later.

It is important to consult the official documentation and GitHub repository for the latest information on limitations and known issues.

## 10. Conclusion and Key Takeaways

The Neo4j MCP Server is a powerful and promising technology that has the potential to revolutionize the way we build AI agent applications. By providing a standardized and secure way for LLMs to interact with Neo4j databases, the MCP server opens up a world of possibilities for building intelligent, graph-native applications.

**Key Takeaways for Developers:**

*   The Neo4j MCP Server is a must-have tool for anyone building AI agents that need to interact with Neo4j.
*   The MCP server is easy to install and configure, and it provides a powerful set of tools for working with graph data.
*   The `stdio` transport mode is suitable for local development, while the `http` transport mode is suitable for production deployments.
*   TLS/HTTPS should always be used to secure the communication between the client and the server in production environments.
*   The Neo4j MCP Server is a key enabler for building sophisticated, graph-native AI agent systems.

## 11. References

[1] Neo4j MCP Documentation. (https://neo4j.com/docs/mcp/current/)
[2] Neo4j MCP GitHub Repository. (https://github.com/neo4j/mcp)
[3] Getting Started With MCP Servers: A Technical Deep Dive. (https://neo4j.com/blog/developer/model-context-protocol/)
[4] Explore the Neo4j Data Modeling MCP Server. (https://medium.com/neo4j/explore-the-neo4j-data-modeling-mcp-server-56a6fdb1d2f7)
[5] Everything a Developer Needs to Know About MCP with Neo4j. (https://www.wearedevelopers.com/en/magazine/604/everything-a-developer-needs-to-know-about-mcp-with-neo4j-604)
