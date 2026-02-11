# Neo4j GraphRAG Python Package: Knowledge Graph Builder and Pipeline

## Introduction

The Neo4j GraphRAG Python package is a powerful library that enables developers to build sophisticated Retrieval-Augmented Generation (RAG) applications on top of Neo4j graph databases. This report provides a comprehensive overview of the package's Knowledge Graph (KG) Builder and Pipeline features, which are essential for transforming unstructured text into a structured knowledge graph. We will explore the entire process, from data loading and entity extraction to schema definition and pipeline construction. This report will also delve into the practical applications of these features, providing code examples and best practices for building robust and scalable AI agent applications.

## User Guide: Knowledge Graph Builder

This page provides information about how to create a Knowledge Graph from unstructured data.

**Warning:** This feature is still experimental. API changes and bug fixes are expected.

### Pipeline Structure

A Knowledge Graph (KG) construction pipeline requires a few components (some of the below components are optional):

*   **Data loader**: extract text from files (PDFs, …).
*   **Text splitter**: split the text into smaller pieces of text (chunks), manageable by the LLM context window (token limit).
*   **Chunk embedder** (optional): compute the chunk embeddings.
*   **Schema builder**: provide a schema to ground the LLM extracted node and relationship types and obtain an easily navigable KG. Schema can be provided manually or extracted automatically using LLMs.
*   **Lexical graph builder**: build the lexical graph (Document, Chunk and their relationships) (optional).
*   **Entity and relation extractor**: extract relevant entities and relations from the text.
*   **Graph pruner**: clean the graph based on schema, if provided.
*   **Knowledge Graph writer**: save the identified entities and relations.
*   **Entity resolver**: merge similar entities into a single node.

This package contains the interface and implementations for each of these components, which are detailed in the following sections.

To see an end-to-end example of a Knowledge Graph construction pipeline, visit the [example folder](https://github.com/neo4j/neo4j-graphrag-python/tree/main/examples) in the project’s GitHub repository.

### Simple KG Pipeline

The simplest way to begin building a KG from unstructured data using this package is utilizing the `SimpleKGPipeline` interface:

```python
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline

kg_builder = SimpleKGPipeline(
    llm=llm, # an LLMInterface for Entity and Relation extraction
    driver=neo4j_driver,  # a neo4j driver to write results to graph
    embedder=embedder,  # an Embedder for chunks
    from_pdf=True,   # set to False if parsing an already extracted text
)
await kg_builder.run_async(file_path=str(file_path))
# await kg_builder.run_async(text="my text")  # if using from_pdf=False
```

See:

*   [Using Another LLM Model](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html#using-another-llm-model) to learn how to instantiate the llm
*   [Embedders](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html#embedders) to learn how to instantiate the embedder

The following section outlines the configuration parameters for this class.

#### Customizing the SimpleKGPipeline

##### Graph Schema

It is possible to guide the LLM by supplying a list of node and relationship types ( with, optionally, a list of their expected properties) and instructions on how to connect them (patterns). Node and relationship types can be represented as either simple strings (for their labels) or dictionaries. If using a dictionary, it must include a `label` key and can optionally include `description` and `properties` keys, as shown below:

```python
NODE_TYPES = [
    # node types can be defined with a simple label...
    "Person",
    # ... or with a dict if more details are needed,
    # such as a description:
    {"label": "House", "description": "Family the person belongs to"},
    # or a list of properties the LLM will try to attach to the entity:
    {"label": "Planet", "properties": [{"name": "name", "type": "STRING", "required": True}, {"name": "weather", "type": "STRING"}]},
]
# same thing for relationships:
RELATIONSHIP_TYPES = [
    "PARENT_OF",
    {
        "label": "HEIR_OF",
        "description": "Used for inheritor relationship between father and sons",
    },
    {"label": "RULES", "properties": [{"name": "fromYear", "type": "INTEGER"}]},
]
```

The patterns are defined by a list of triplet in the format: `(source_node_label, relationship_label, target_node_label)`. For instance:

```python
PATTERNS = [
    ("Person", "PARENT_OF", "Person"),
    ("Person", "HEIR_OF", "House"),
    ("House", "RULES", "Planet"),
]
```

This schema information can be provided to the `SimpleKGBuilder` as demonstrated below:

```python
# Using the schema parameter (recommended approach)
kg_builder = SimpleKGPipeline(
    # ...
    schema={
        "node_types": NODE_TYPES,
        "relationship_types": RELATIONSHIP_TYPES,
        "patterns": PATTERNS,
        "additional_node_types": False,
    },
    # ...
)
```

##### Schema Parameter Behavior

The `schema` parameter controls how entity and relation extraction is performed:

*   **EXTRACTED**: `schema="EXTRACTED"` or (`schema=None`, default value) The schema is automatically extracted from the input text once using LLM. This guiding schema is then used to structure entity and relation extraction for all chunks. This guarantees all chunks have the same guiding schema. (See [Automatic Schema Extraction](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html#automatic-schema-extraction))
*   **FREE**: `schema="FREE"` or empty schema (`{"node_types": ()}`) No schema extraction is performed. Entity and relation extraction proceed without a predefined or derived schema, resulting in unguided entity and relation extraction. Use this to bypass automatic schema extraction.

##### Extra configurations

These parameters are part of the `EntityAndRelationExtractor` component. For detailed information, refer to the section on [Entity and Relation Extractor](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html#entity-and-relation-extractor). They are also accessible via the `SimpleKGPipeline` interface.

```python
kg_builder = SimpleKGPipeline(
    # ...
    prompt_template="",
    lexical_graph_config=my_config,
    on_error="RAISE",
    # ...
)
```

##### Skip Entity Resolution

By default, after each run, an Entity Resolution step is performed to merge nodes that share the same label and `name` property. To disable this behavior, adjust the following parameter:

```python
kg_builder = SimpleKGPipeline(
    # ...
    perform_entity_resolution=False,
    # ...
)
```

##### Neo4j Database

To write to a non-default Neo4j database, specify the database name using this parameter:

```python
kg_builder = SimpleKGPipeline(
    # ...
    neo4j_database="myDb",
    # ...
)
```

##### Using Custom Components

For advanced customization or when using a custom implementation, you can pass instances of specific components to the `SimpleKGPipeline`. The components that can customized at the moment are:

*   `text_splitter`: must be an instance of `TextSplitter`
*   `pdf_loader`: must be an instance of `PdfLoader`
*   `kg_writer`: must be an instance of `KGWriter`

For instance, the following code can be used to customize the chunk size and chunk overlap in the text splitter component:

```python
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)

text_splitter = FixedSizeSplitter(chunk_size=500, chunk_overlap=100)

kg_builder = SimpleKGPipeline(
    # ...
    text_splitter=text_splitter,
    # ...
)
```

##### Run Parameters

`SimpleKGPipeline` also accepts addition runtime parameters:

*   `document_metadata` (dict): each item will be saved as a property attached to the `Document` node.

### Using a Config file

```python
from neo4j_graphrag.experimental.pipeline.config.runner import PipelineRunner

file_path = "my_config.json"

pipeline = PipelineRunner.from_config_file(file_path)
await pipeline.run({"text": "my text"})
```

The config file can be written in either JSON or YAML format.

Here is an example of a base configuration file in JSON format:

```json
{
    "version_": 1,
    "template_": "SimpleKGPipeline",
    "neo4j_config": {},
    "llm_config": {},
    "embedder_config": {}
}
```

And like this in YAML:

```yaml
version_: 1
template_: SimpleKGPipeline
neo4j_config:
llm_config:
embedder_config:
```

#### Defining a Neo4j Driver

Below is an example of configuring a Neo4j driver in a JSON configuration file:

```json
{
    "neo4j_config": {
        "params_": {
            "uri": "bolt://...",
            "user": "neo4j",
            "password": "password"
        }
    }
}
```

Same for YAML:

```yaml
neo4j_config:
    params_:
        uri: bolt://...
        user: neo4j
        password: password
```


## User Guide: Pipeline

This page provides information about how to create a pipeline.

**Note:** Pipelines run asynchronously, see examples below.

### Creating Components

Components are asynchronous units of work that perform simple tasks, such as chunking documents or saving results to Neo4j. This package includes a few default components, but developers can create their own by following these steps:

1.  Create a subclass of the Pydantic `neo4j_graphrag.experimental.pipeline.DataModel` to represent the data being returned by the component
2.  Create a subclass of `neo4j_graphrag.experimental.pipeline.Component`
3.  Create a `run` method in this new class and specify the required inputs and output model using the just created `DataModel`
4.  Implement the `run` method: it’s an `async` method, allowing tasks to be parallelized and awaited within this method.

An example is given below, where a `ComponentAdd` is created to add two numbers together and return the resulting sum:

```python
from neo4j_graphrag.experimental.pipeline import Component, DataModel

class IntResultModel(DataModel):
    result: int

class ComponentAdd(Component):
    async def run(self, number1: int, number2: int = 1) -> IntResultModel:
        return IntResultModel(result = number1 + number2)
```

Read more about [Components](https://neo4j.com/docs/neo4j-graphrag-python/current/api_reference/experimental/pipeline/components.html) in the API Documentation.

### Connecting Components within a Pipeline

The ultimate aim of creating components is to assemble them into a complex pipeline for a specific purpose, such as building a Knowledge Graph from text data.

Here’s how to create a simple pipeline and propagate results from one component to another (detailed explanations follow):

```python
import asyncio
from neo4j_graphrag.experimental.pipeline import Pipeline

pipe = Pipeline()
pipe.add_component(ComponentAdd(), "a")
pipe.add_component(ComponentAdd(), "b")

pipe.connect("a", "b", input_config={"number2": "a.result"})
asyncio.run(pipe.run({"a": {"number1": 10, "number2": 1}, "b": {"number1": 4}}))
# result: 10+1+4 = 15
```

1.  First, a pipeline is created, and two components named “a” and “b” are added to it.
2.  Next, the two components are connected so that “b” runs after “a”, with the “number2” parameter for component “b” being the result of component “a”.
3.  Finally, the pipeline is run with 10 and 1 as input parameters for “a”. Component “b” will receive 11 (10 + 1, the result of “a”) as “number1” and 4 as “number2” (as specified in the `pipeline.run` parameters).

The data flow is illustrated in the diagram below:

```
10 ---\
        Component "a" -> 11
1 ----/                   \\
                           \\
                             Component "b" -> 15
4 -------------------------/
```

**Warning:** Cyclic graph

Cycles are not allowed in a Pipeline.

**Warning:** Ignored user inputs

If inputs are provided both by user in the `pipeline.run` method and as `input_config` in a `connect` method, the user input will be ignored. Take for instance the following pipeline, adapted from the previous one:

```python
pipe.connect("a", "b", input_config={"number2": "a.result"})
asyncio.run(pipe.run({"a": {"number1": 10, "number2": 1}, "b": {"number1": 4, "number2": 42}}))
```

The result will still be **15** because the user input `“number2”: 42` is ignored.

### Visualising a Pipeline

Pipelines can be visualized using the `draw` method:

```python
from neo4j_graphrag.experimental.pipeline import Pipeline

pipe = Pipeline()
# ... define components and connections

pipe.draw("pipeline.html")
```

Here is an example pipeline rendering as an interactive HTML visualization:

```python
# To view the visualization in a browser
import webbrowser
webbrowser.open("pipeline.html")
```

By default, output fields which are not mapped to any component are hidden. They can be added to the visualization by setting `hide_unused_outputs` to `False`:

```python
pipe.draw("pipeline_full.html", hide_unused_outputs=False)

# To view the full visualization in a browser
import webbrowser
webbrowser.open("pipeline_full.html")
```

### Adding an Event Callback

It is possible to add a callback to receive notification about pipeline progress:

*   `PIPELINE_STARTED`, when pipeline starts
*   `PIPELINE_FINISHED`, when pipeline ends
*   `TASK_STARTED`, when a task starts
*   `TASK_PROGRESS`, sent by each component (depends on component’s implementation, see below)
*   `TASK_FINISHED`, when a task ends

See `PipelineEvent` and `TaskEvent` to see what is sent in each event type.

```python
import asyncio
import logging

from neo4j_graphrag.experimental.pipeline import Pipeline
from neo4j_graphrag.experimental.pipeline.notification import Event

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.WARNING)

async def event_handler(event: Event) -> None:
    """Function can do anything about the event,
    here we're just logging it if it's a pipeline-level event.
    """
    if event.event_type.is_pipeline_event:
        logger.warning(event)

pipeline = Pipeline(
    callback=event_handler,
)
# ... add components, connect them as usual

await pipeline.run(...)
```

### Send Events from Components

Components can send progress notifications using the `notify` function from `context_` by implementing the `run_from_context` method:

```python
from neo4j_graphrag.experimental.pipeline import Component, DataModel
from neo4j_graphrag.experimental.pipeline.types.context import RunContext

class IntResultModel(DataModel):
    result: int

class ComponentAdd(Component):
    async def run_with_context(self, context_: RunContext, number1: int, number2: int = 1) -> IntResultModel:
        for fake_iteration in range(10):
            await context_.notify(
                message=f"Starting iteration {fake_iteration} out of 10",
                data={"iteration": fake_iteration, "total": 10}
            )
        return IntResultModel(result = number1 + number2)
```

This will send an `TASK_PROGRESS` event to the pipeline callback.

**Note:** In a future release, the `context_` parameter will be added to the `run` method.


## Example: Knowledge Graph Builder Pipeline

This example demonstrates how to define and run a complete Knowledge Graph Builder pipeline using the `neo4j-graphrag` library.

```python
# Copyright (c) "Neo4j"
# Neo4j Sweden AB [https://neo4j.com]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import annotations

import asyncio
import logging

import neo4j
from neo4j_graphrag.experimental.components.entity_relation_extractor import (
    LLMEntityRelationExtractor,
    OnError,
)
from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter
from neo4j_graphrag.experimental.components.pdf_loader import PdfLoader
from neo4j_graphrag.experimental.components.schema import (
    SchemaBuilder,
    NodeType,
    RelationshipType,
)
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)
from neo4j_graphrag.experimental.pipeline.pipeline import PipelineResult
from neo4j_graphrag.llm import LLMInterface, OpenAILLM

logging.basicConfig(level=logging.INFO)


async def define_and_run_pipeline(
    neo4j_driver: neo4j.Driver, llm: LLMInterface
) -> PipelineResult:
    from neo4j_graphrag.experimental.pipeline import Pipeline

    # Instantiate Entity and Relation objects
    node_types = [
        NodeType(label="PERSON", description="An individual human being."),
        NodeType(
            label="ORGANIZATION",
            description="A structured group of people with a common purpose.",
        ),
        NodeType(label="LOCATION", description="A location or place."),
        NodeType(
            label="HORCRUX",
            description="A magical item in the Harry Potter universe.",
        ),
    ]

    relationship_types = [
        RelationshipType(
            label="SITUATED_AT", description="Indicates the location of a person."
        ),
        RelationshipType(
            label="PART_OF",
            description="Indicates that a person is a part of an organization.",
        ),
    ]

    patterns = [
        ("PERSON", "SITUATED_AT", "LOCATION"),
        ("PERSON", "PART_OF", "ORGANIZATION"),
    ]

    pdf_loader = PdfLoader()
    text_splitter = FixedSizeSplitter(chunk_size=500, chunk_overlap=100)
    schema_builder = SchemaBuilder(
        node_types=node_types, relationship_types=relationship_types, patterns=patterns
    )
    entity_relation_extractor = LLMEntityRelationExtractor(
        llm=llm, on_error=OnError.RAISE
    )
    kg_writer = Neo4jWriter(driver=neo4j_driver)

    pipeline = Pipeline(description="My first pipeline")

    pipeline.add_component(pdf_loader, "pdf_loader")
    pipeline.add_component(text_splitter, "text_splitter")
    pipeline.add_component(schema_builder, "schema_builder")
    pipeline.add_component(entity_relation_extractor, "entity_relation_extractor")
    pipeline.add_component(kg_writer, "kg_writer")

    pipeline.connect("pdf_loader", "text_splitter")
    pipeline.connect("text_splitter", "entity_relation_extractor")
    pipeline.connect("schema_builder", "entity_relation_extractor", "graph_schema")
    pipeline.connect("entity_relation_extractor", "kg_writer")

    return await pipeline.run(
        {
            "pdf_loader": {
                "file_path": "./examples/data/harry_potter.pdf",
            },
        }
    )


if __name__ == "__main__":
    # Make sure to export your OPENAI_API_KEY in the environment
    llm = OpenAILLM()
    # Make sure to have a Neo4j instance running
    driver = neo4j.GraphDatabase.driver("bolt://localhost:7687")
    asyncio.run(define_and_run_pipeline(driver, llm))
```


## Overview and Purpose

The Neo4j GraphRAG Python package is a comprehensive library designed to facilitate the development of Retrieval-Augmented Generation (RAG) applications that leverage the power of Neo4j's graph database technology. The primary purpose of this package is to provide developers with a streamlined and efficient workflow for transforming unstructured data, such as text from documents and web pages, into a structured knowledge graph. This process, known as Knowledge Graph (KG) construction, is a critical first step in building advanced AI agent applications that can reason over and retrieve information from large and complex datasets.

The package's KG Builder and Pipeline features are at the heart of this process. The KG Builder provides a set of tools and components for extracting entities and relationships from text, defining a schema for the knowledge graph, and writing the extracted data to a Neo4j database. The Pipeline feature, in turn, allows developers to compose these components into complex, asynchronous workflows that can be easily customized and extended. By providing a flexible and modular framework for KG construction, the Neo4j GraphRAG Python package empowers developers to build sophisticated AI agents that can perform a wide range of tasks, from question answering and summarization to complex reasoning and analysis.


## Features, Functions, and Capabilities

The Neo4j GraphRAG Python package offers a rich set of features for building knowledge graphs from unstructured text. These features are organized into two main components: the Knowledge Graph (KG) Builder and the Pipeline API.

### Knowledge Graph Builder

The KG Builder is a collection of components that work together to extract, structure, and store information from text. The key components of the KG Builder pipeline are:

*   **Data Loader:** This component is responsible for extracting text from various file formats, with a primary focus on PDFs. It can handle both local files and remote URLs.
*   **Text Splitter:** Large documents are difficult for LLMs to process due to context window limitations. The Text Splitter component breaks down the text into smaller, manageable chunks.
*   **Chunk Embedder:** This optional component computes vector embeddings for each text chunk, which can be used for similarity searches and other downstream tasks.
*   **Schema Builder:** The Schema Builder allows you to define the structure of your knowledge graph by specifying the types of nodes and relationships that the LLM should extract. You can provide a predefined schema or have the package automatically extract one from the text.
*   **Entity and Relation Extractor:** This is the core component of the KG Builder. It uses an LLM to identify and extract entities (nodes) and relationships from the text chunks based on the provided schema.
*   **Graph Pruner:** This component cleans the extracted graph by removing any nodes or relationships that do not conform to the defined schema.
*   **Knowledge Graph Writer:** The Knowledge Graph Writer saves the extracted entities and relationships to a Neo4j database.
*   **Entity Resolver:** This component helps to improve the quality of the knowledge graph by merging similar entities into a single node.

### Pipeline API

The Pipeline API provides a flexible and powerful way to compose the KG Builder components into complex, asynchronous workflows. The key features of the Pipeline API are:

*   **Asynchronous Execution:** Pipelines run asynchronously, allowing for efficient and parallel processing of large amounts of data.
*   **Component-Based Architecture:** The Pipeline API is built around a component-based architecture, which makes it easy to create, customize, and reuse components.
*   **Data Flow Management:** The Pipeline API provides a simple and intuitive way to connect components and manage the flow of data between them.
*   **Visualization:** The Pipeline API includes a visualization tool that allows you to see the structure of your pipeline and the flow of data through it.
*   **Event Handling:** The Pipeline API includes an event handling system that allows you to monitor the progress of your pipeline and receive notifications about important events.


## Configuration options and best practices

The Neo4j GraphRAG Python package provides a wide range of configuration options that allow you to customize the behavior of the KG Builder and Pipeline to meet your specific needs. This section will discuss some of the most important configuration options and best practices for using them.

### SimpleKGPipeline Configuration

The `SimpleKGPipeline` class provides a high-level interface for building knowledge graphs. It has several important configuration options:

*   `llm`: This option allows you to specify the LLM that you want to use for entity and relation extraction. You can use any LLM that implements the `LLMInterface`.
*   `embedder`: This option allows you to specify the embedding model that you want to use for computing chunk embeddings. You can use any model that implements the `Embedder` interface.
*   `schema`: This option allows you to provide a schema for your knowledge graph. You can provide a predefined schema or have the package automatically extract one from the text.
*   `perform_entity_resolution`: This option allows you to enable or disable entity resolution.
*   `neo4j_database`: This option allows you to specify the name of the Neo4j database that you want to write to.

### Customizing Components

For more advanced customization, you can create your own custom components and use them in your pipelines. For example, you can create a custom data loader to extract text from a new file format, or you can create a custom entity and relation extractor to use a different extraction algorithm.

### Best Practices

Here are some best practices for using the Neo4j GraphRAG Python package:

*   **Start with a simple schema:** When you are first starting out, it is a good idea to start with a simple schema and then gradually add more complexity as needed.
*   **Use a high-quality LLM:** The quality of your knowledge graph will depend on the quality of the LLM that you use for entity and relation extraction. It is important to use a high-quality LLM that has been trained on a large dataset of text and code.
*   **Experiment with different settings:** The best way to find the optimal settings for your specific use case is to experiment with different settings and see what works best.
*   **Use the visualization tool:** The visualization tool can be a valuable tool for debugging your pipelines and understanding how they work.


## How this relates to building AI agent applications with Neo4j

The Neo4j GraphRAG Python package is a critical tool for building sophisticated AI agent applications with Neo4j. AI agents that can reason over and interact with large and complex datasets require a structured and queryable knowledge base. The KG Builder and Pipeline features of the GraphRAG package provide the means to create this knowledge base from unstructured text, which is a common source of information in many real-world applications.

By transforming unstructured text into a knowledge graph, developers can create AI agents that can:

*   **Perform complex queries:** AI agents can use the knowledge graph to answer complex questions that would be difficult or impossible to answer from the original unstructured text.
*   **Reason over data:** AI agents can use the relationships in the knowledge graph to reason about the data and make inferences that are not explicitly stated in the text.
*   **Provide more accurate and context-aware responses:** By grounding their responses in the knowledge graph, AI agents can provide more accurate and context-aware responses to user queries.

The Pipeline API, in particular, is well-suited for building AI agent applications. The asynchronous and component-based nature of the Pipeline API makes it easy to create complex and scalable data processing workflows that can be integrated into the agent's decision-making process. For example, an AI agent could use a pipeline to automatically extract information from new documents as they become available and update its knowledge base in real-time.


## Limitations and Known Issues

While the Neo4j GraphRAG Python package is a powerful tool, it is important to be aware of its limitations and known issues. The documentation explicitly states that the Knowledge Graph Builder feature is still experimental, and that API changes and bug fixes are to be expected. This means that developers should be prepared for potential breaking changes in future releases.

One of the main limitations of the package is its reliance on LLMs for entity and relation extraction. The quality of the extracted knowledge graph is directly dependent on the quality of the LLM used. If the LLM is not well-suited for the task, it may produce inaccurate or incomplete results. Additionally, the performance of the LLM can be a bottleneck in the KG construction process, especially when processing large volumes of text.

Another limitation is the lack of support for certain file formats. While the package has a built-in PDF loader, it does not have native support for other common formats like Word documents or HTML files. Developers who need to process these file formats will need to create their own custom data loaders.


## Key takeaways for a developer building a graph-native AI agent system

For developers building graph-native AI agent systems, the Neo4j GraphRAG Python package offers a powerful and flexible solution for knowledge graph construction. Here are some key takeaways:

*   **Embrace the pipeline:** The Pipeline API is the most powerful and flexible feature of the package. By creating custom components and composing them into pipelines, you can build sophisticated and scalable data processing workflows that are tailored to your specific needs.
*   **Schema is key:** The quality of your knowledge graph is highly dependent on the quality of your schema. Take the time to design a schema that accurately reflects the domain you are modeling.
*   **Don't be afraid to experiment:** The package is still experimental, so don't be afraid to experiment with different settings and configurations to see what works best for your use case.
*   **Contribute to the community:** The package is open source, so if you find a bug or have an idea for a new feature, don't hesitate to contribute to the project.


## References

[1] [Neo4j GraphRAG for Python documentation](https://neo4j.com/docs/neo4j-graphrag-python/current/)

[2] [Neo4j GraphRAG for Python GitHub repository](https://github.com/neo4j/neo4j-graphrag-python)

[3] [User Guide: Knowledge Graph Builder](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html)

[4] [User Guide: Pipeline](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_pipeline.html)
