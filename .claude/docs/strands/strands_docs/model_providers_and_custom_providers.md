# Strands Model Providers and Custom Providers: A Technical Deep Dive

This report provides a comprehensive technical overview of Model Providers in the Strands Agents SDK, with a focus on implementing custom providers. It covers the architecture, abstract base classes, required methods, and code examples for creating and using custom model providers in Python.

## 1. Introduction to Model Providers

A model provider is a service or platform that hosts and serves large language models (LLMs) through an API. The Strands Agents SDK abstracts the complexities of interacting with various providers, offering a unified interface. This design allows developers to seamlessly switch between different models or even use multiple providers within the same application with minimal code changes.

## 2. Supported Providers

The Strands Agents SDK for Python supports a wide array of model providers. Most of these are available as optional dependencies, which can be installed using `pip`. For example, to install the OpenAI provider, you would run:

```bash
pip install 'strands-agents[openai]'
```

Alternatively, all providers can be installed at once:

```bash
pip install 'strands-agents[all]'
```

The SDK's architecture makes these providers interchangeable. By simply swapping the model instance, an agent can be reconfigured to use a different LLM, as demonstrated in the basic usage examples.

## 3. Implementing a Custom Model Provider

The Strands Agents SDK is highly extensible, allowing developers to integrate their own LLM services by creating custom model providers. This is achieved by extending a core abstract base class and implementing a set of required methods.

### 3.1. Architecture

All model providers in the Strands Agents SDK, including custom ones, inherit from the `strands.models.Model` abstract base class. This ensures a consistent interface across all providers, enabling the interchangeability mentioned earlier.

### 3.2. The `Model` Abstract Base Class

The `Model` abstract base class, located at `strands.models.model.Model`, defines the contract that all model providers must adhere to. To create a custom model provider, you must create a class that inherits from `Model` and implements its abstract methods.

The key abstract methods to implement are:

*   `update_config(self, **model_config: Any) -> None`: Updates the model's configuration at runtime.
*   `get_config(self) -> Any`: Retrieves the current model configuration.
*   `stream(...)`: The primary method for handling conversational interactions with the model.
*   `structured_output(...)`: A specialized method for obtaining structured, type-safe output from the model.

### 3.3. The `stream()` Method

The `stream()` method is the core of any model provider. It's responsible for formatting the request, invoking the model's API, and processing the response as a stream of events. The method signature is as follows:

```python
async def stream(
    self,
    messages: Messages,
    tool_specs: list[ToolSpec] | None = None,
    system_prompt: str | None = None,
    *,
    tool_choice: ToolChoice | None = None,
    system_prompt_content: list[SystemContentBlock] | None = None,
    invocation_state: dict[str, Any] | None = None,
    **kwargs: Any,
) -> AsyncIterable[StreamEvent]:
```

This method returns an asynchronous iterable of `StreamEvent` objects, which represent the various events that occur during the model's response stream (e.g., message start, content delta, message stop).

### 3.4. The `structured_output()` Method

For tasks that require reliable data extraction, the `structured_output()` method is used. It leverages the model's tool-calling capabilities to return a Pydantic `BaseModel` object, ensuring the output is validated and type-safe.

The method signature is:

```python
async def structured_output(
    self, output_model: type[T], prompt: Messages, system_prompt: str | None = None, **kwargs: Any
) -> AsyncGenerator[dict[str, T | Any], None]:
```

Internally, this method converts the Pydantic model into a tool specification that is passed to the `stream()` method.

### 3.5. Configuration

Custom model providers should define a `ModelConfig` class, typically a `TypedDict`, to manage the configuration parameters for the model. This allows for a clean and type-safe way to handle settings like `model_id`, `max_tokens`, and `temperature`.

## 4. Code Examples

Here are some code examples illustrating the concepts discussed:

**Basic Usage of Pre-built Providers:**

```python
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.models.openai import OpenAIModel

# Use Bedrock
bedrock_model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0"
)
agent = Agent(model=bedrock_model)
response = agent("What can you help me with?")

# Alternatively, use OpenAI by just switching model provider
openai_model = OpenAIModel(
    client_args={"api_key": "<KEY>"},
    model_id="gpt-4o"
)
agent = Agent(model=openai_model)
response = agent("What can you help me with?")
```

**Skeleton of a Custom Model Provider:**

```python
# your_org/models/custom_model.py
import logging
import os
from typing import Any, Iterable, Optional, TypedDict
from typing_extensions import Unpack

from custom.model import CustomModelClient

from strands.models import Model
from strands.types.content import Messages
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolSpec

logger = logging.getLogger(__name__)


class CustomModel(Model):
    """Your custom model provider implementation."""

    class ModelConfig(TypedDict):
        """
        Configuration your model.

        Attributes:
            model_id: ID of Custom model.
            params: Model parameters (e.g., max_tokens).
        """
        model_id: str
        params: Optional[dict[str, Any]]

    def __init__(
        self,
        api_key: str,
        *,
        **model_config: Unpack[ModelConfig]
    ) -> None:
        self.config = CustomModel.ModelConfig(**model_config)
        self.client = CustomModelClient(api_key)

    def update_config(self, **model_config: Unpack[ModelConfig]) -> None:
        self.config.update(model_config)

    def get_config(self) -> ModelConfig:
        return self.config

    async def stream(
        self,
        messages: Messages,
        tool_specs: Optional[list[ToolSpec]] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AsyncIterable[StreamEvent]:
        # Implementation details...
        pass

    async def structured_output(
        self,
        output_model: type[T],
        prompt: Messages,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> Generator[dict[str, Union[T, Any]], None, None]:
        # Implementation details...
        pass
```

## 5. Conclusion

The Strands Agents SDK provides a powerful and flexible framework for working with large language models. Its unified interface for model providers simplifies development and promotes code reusability. The ability to create custom model providers allows for seamless integration of proprietary or specialized LLMs, making the SDK adaptable to a wide range of use cases.

## References

[1] [Strands Agents SDK — Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/index.md)
[2] [Strands Agents SDK — Custom Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/custom-model-providers/index.md)
[3] [Strands Agents SDK — Amazon Bedrock Provider](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/amazon-bedrock/index.md)
[4] [Strands Agents SDK — OpenAI Provider](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/open-ai/index.md)
[5] [Strands Agents SDK — Ollama Provider](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/ollama/index.md)
