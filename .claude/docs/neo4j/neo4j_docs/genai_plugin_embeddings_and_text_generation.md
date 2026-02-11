# Neo4j GenAI Plugin: A Comprehensive Research Report

**Author:** Manus AI

**Date:** February 10, 2026

## 1. Overview and Purpose

The Neo4j GenAI Plugin is a powerful extension that bridges the gap between the world's leading graph database and the rapidly evolving landscape of Generative AI. It provides a seamless integration with large language models (LLMs) from major providers, enabling developers to perform sophisticated AI-powered operations directly within the Cypher query language. This eliminates the need for complex and often cumbersome external orchestration, allowing for the creation of more intelligent, context-aware, and efficient graph-native applications.

The primary purpose of the GenAI Plugin is to empower developers to leverage the capabilities of LLMs for two key tasks: creating vector embeddings and generating text. By integrating these functionalities directly into the database, Neo4j transforms from a passive data store into an active participant in the AI development lifecycle. This allows for the creation of a new class of applications that can understand, reason about, and generate human-like text based on the rich, interconnected data stored within the graph.

This report provides a comprehensive overview of the Neo4j GenAI Plugin, covering its core features, configuration, and practical applications. It is intended for a technical audience of developers, data scientists, and architects who are interested in building next-generation AI applications with Neo4j.

## 2. Features, Functions, and Capabilities

The GenAI Plugin offers a rich set of features, functions, and procedures that can be broadly categorized into two main areas: vector embeddings and text generation.

### 2.1. Vector Embeddings

Vector embeddings are a cornerstone of modern AI, providing a numerical representation of text, images, and other data types that can be used for a variety of tasks, including semantic search, recommendation, and clustering. The GenAI Plugin provides a set of functions and procedures for creating and storing vector embeddings directly within the Neo4j database.

#### 2.1.1. `ai.text.embed()`

This function generates a vector embedding for a single text value. It takes as input the text to be embedded, the name of the AI provider to use, and a configuration map that specifies the model and other provider-specific options.

**Signature:**

```cypher
ai.text.embed(resource, provider, configuration = {}) :: VECTOR
```

#### 2.1.2. `ai.text.embedBatch()`

This procedure generates vector embeddings for a batch of text values in a single API request. This is significantly more efficient than calling `ai.text.embed()` multiple times, as it reduces network overhead and latency.

**Signature:**

```cypher
ai.text.embedBatch(resources, provider, configuration = {}) :: (index, resource, vector)
```

#### 2.1.3. `ai.text.embed.providers()`

This procedure returns a list of the available vector embedding providers and their configuration options.

**Signature:**

```cypher
ai.text.embed.providers() :: (name, requiredConfigType, optionalConfigType, defaultConfig)
```

### 2.2. Text Generation

The GenAI Plugin also provides a set of functions for generating text and performing chat-like interactions with LLMs.

#### 2.2.1. `ai.text.completion()`

This function generates text based on a textual input prompt. It is similar to submitting a prompt to an LLM in a playground or other interface.

**Signature:**

```cypher
ai.text.completion(prompt, provider, configuration) :: STRING
```

#### 2.2.2. `ai.text.chat()`

This function allows you to exchange several messages with an LLM as part of a single thread. It takes as input a prompt, a chat ID (which is used to maintain the context of the conversation), the name of the AI provider, and a configuration map.

**Signature:**

```cypher
ai.text.chat(prompt, chatId, provider, configuration = {}) :: MAP
```

#### 2.2.3. `ai.text.completion.providers()` and `ai.text.chat.providers()`

These procedures return a list of the available text completion and chat providers, respectively, along with their configuration options.

**Signatures:**

```cypher
ai.text.completion.providers() :: (name, requiredConfigType, optionalConfigType, defaultConfig)
ai.text.chat.providers() :: (name, requiredConfigType, optionalConfigType, defaultConfig)
```

### 2.3. Supported Providers

The GenAI Plugin supports a wide range of AI providers, including:

*   **OpenAI:** A leading provider of LLMs, including the popular GPT series.
*   **Azure OpenAI:** Microsoft's managed version of OpenAI's models.
*   **Vertex AI:** Google's unified AI platform, which includes a variety of models for text generation and other tasks.
*   **Amazon Bedrock:** Amazon's fully managed service that makes foundation models from leading AI startups and Amazon available via an API.

## 3. Code Examples

This section provides a series of code examples that demonstrate how to use the GenAI Plugin for a variety of tasks.

### 3.1. Creating and Storing Embeddings

This example shows how to create and store vector embeddings for the `plot` and `title` of movies in the Neo4j movie recommendations dataset.

```cypher
MATCH (m:Movie)
WHERE m.plot IS NOT NULL AND m.title IS NOT NULL
WITH m, m.title + ' ' + m.plot AS text
CALL ai.text.embed(text, 'OpenAI', {token: $openai_token, model: 'text-embedding-3-small'}) YIELD vector
SET m.embedding = vector
```

### 3.2. Generating Text

This example shows how to use the `ai.text.completion()` function to generate a summary of a movie's plot.

```cypher
MATCH (m:Movie {title: 'The Matrix'})
WITH m.plot AS plot
CALL ai.text.completion('Summarize the following plot in one sentence: ' + plot, 'OpenAI', {token: $openai_token, model: 'gpt-4.1-mini'}) YIELD result
RETURN result
```

### 3.3. Chatting with an LLM

This example shows how to use the `ai.text.chat()` function to have a conversation with an LLM about a movie.

```cypher
// Start a new chat
CALL ai.text.chat('What is the movie The Matrix about?', null, 'OpenAI', {token: $openai_token, model: 'gpt-4.1-mini'}) YIELD message, chatId

// Continue the chat
CALL ai.text.chat('Who is the main character?', chatId, 'OpenAI', {token: $openai_token, model: 'gpt-4.1-mini'}) YIELD message, chatId
```

## 4. Configuration and Best Practices

### 4.1. Configuration

The GenAI Plugin can be configured via a file called `genai.conf`, which must be located in the same directory as `neo4j.conf`. This file allows you to set a variety of options, including the base URL for the OpenAI API and other provider-specific settings.

### 4.2. Best Practices

*   **Use batching:** When creating embeddings for a large number of nodes or relationships, always use the `ai.text.embedBatch()` procedure to improve performance.
*   **Use a proxy:** To avoid exposing your API keys in your Cypher queries, consider using a proxy to forward requests to the AI provider.
*   **Use a dedicated user:** For security reasons, it is a good practice to create a dedicated user with limited privileges for running GenAI queries.

## 5. Relevance to Building AI Agent Applications with Neo4j

The Neo4j GenAI Plugin is a game-changer for building AI agent applications with Neo4j. By providing a seamless integration with LLMs, the plugin enables developers to create agents that can:

*   **Understand and reason about the graph:** Agents can use the `ai.text.completion()` function to generate Cypher queries based on natural language input, allowing them to explore and understand the graph in a more intuitive way.
*   **Generate human-like text:** Agents can use the `ai.text.completion()` and `ai.text.chat()` functions to generate natural language responses to user queries, making them more engaging and user-friendly.
*   **Perform complex tasks:** Agents can combine the power of the graph with the capabilities of LLMs to perform complex tasks, such as summarizing a large amount of text, answering questions about the graph, and even generating new content based on the data in the graph.

## 6. Limitations and Known Issues

*   **Cost:** The use of LLMs can be expensive, especially for large-scale applications. It is important to carefully consider the cost implications of using the GenAI Plugin before deploying it in a production environment.
*   **Latency:** The performance of the GenAI Plugin is dependent on the performance of the underlying LLM. In some cases, the latency of the LLM may be too high for real-time applications.
*   **Security:** The GenAI Plugin requires access to your AI provider's API keys. It is important to store these keys securely and to use a dedicated user with limited privileges for running GenAI queries.

## 7. Key Takeaways for a Developer Building a Graph-Native AI Agent System

*   The Neo4j GenAI Plugin is a powerful tool for building intelligent, context-aware, and efficient graph-native AI agent systems.
*   The plugin provides a seamless integration with LLMs from major providers, enabling developers to perform sophisticated AI-powered operations directly within the Cypher query language.
*   The plugin can be used for a variety of tasks, including creating vector embeddings, generating text, and performing chat-like interactions with LLMs.
*   When using the plugin, it is important to consider the cost, latency, and security implications of using LLMs.

## 8. References

[1] Neo4j. (2026). *Introduction - Neo4j GenAI Plugin*. Retrieved from https://neo4j.com/docs/genai/plugin/current/

[2] Neo4j. (2026). *Create and store embeddings - Neo4j GenAI Plugin*. Retrieved from https://neo4j.com/docs/genai/plugin/current/embeddings/

[3] Neo4j. (2026). *Generate text & Chat - Neo4j GenAI Plugin*. Retrieved from https://neo4j.com/docs/genai/plugin/current/generate-text/

[4] Neo4j. (2026). *Functions and procedures - Neo4j GenAI Plugin*. Retrieved from https://neo4j.com/docs/genai/plugin/current/reference/functions-procedures/

[5] Neo4j. (2026). *Configuration settings - Neo4j GenAI Plugin*. Retrieved from https://neo4j.com/docs/genai/plugin/current/reference/config/

[6] Galleta, C. (2024). *How I created a Neo4j Search Engine with Generative AI*. Medium. Retrieved from https://medium.com/@thcookieh/how-i-created-a-neo4j-search-engine-with-generative-ai-98b43cf8ec1e
