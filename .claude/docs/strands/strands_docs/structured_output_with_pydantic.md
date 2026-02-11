# Strands Structured Output with Pydantic

This report details the use of Pydantic for structured output in the Strands Agents SDK for Python. It covers the core concepts, usage patterns, and best practices for obtaining type-safe, validated data from language models.

## Key Findings

Strands leverages Pydantic to transform unstructured language model outputs into reliable, program-friendly data structures. This is achieved by defining a Pydantic model and passing it to the `agent` during invocation. The key features and findings are summarized below:

| Feature | Description |
| --- | --- |
| **Type Safety** | Instead of raw text, you get typed Python objects that match your Pydantic model. |
| **Automatic Validation** | Pydantic automatically validates the language model's response against your schema. |
| **Clear Documentation** | The Pydantic model itself serves as clear documentation for the expected output structure. |
| **IDE Support** | Provides IDE type hinting for the LLM-generated responses, improving developer experience. |
| **Error Prevention** | Malformed responses are caught early through validation, preventing downstream errors. |

### Basic Usage

The primary mechanism for structured output is the `structured_output_model` parameter in the `agent` invocation. You define a Pydantic `BaseModel` and pass it to the agent. The validated data is then accessible through the `structured_output` attribute of the `AgentResult` object.

### Asynchronous Support

Structured output is also supported in asynchronous operations via the `invoke_async` method, which allows for non-blocking calls.

### Error Handling

If the structured output parsing fails, Strands raises a `StructuredOutputException`. This allows for robust error handling and fallback mechanisms.

### Migration from Legacy API

The older `Agent.structured_output()` and `Agent.structured_output_async()` methods are deprecated. The recommended approach is to use the `structured_output_model` parameter.

### Advanced Usage

- **Auto Retries with Validation**: Strands can automatically retry validation if the initial extraction fails a `field_validator`.
- **Streaming**: Structured output can be streamed, allowing for progressive processing of data.
- **Tool Integration**: It can be combined with tools to format the results of tool execution.
- **Multiple Output Models**: A single agent instance can be used with different Pydantic models for various extraction tasks.
- **Conversation History**: You can extract structured information from the context of a conversation.
- **Defaults**: A default `structured_output_model` can be set at the agent level, and can be overridden for specific invocations.

## Code Examples

```python
from pydantic import BaseModel, Field
from strands import Agent

# 1) Define the Pydantic model
class PersonInfo(BaseModel):
    """Model that contains information about a Person"""
    name: str = Field(description="Name of the person")
    age: int = Field(description="Age of the person")
    occupation: str = Field(description="Occupation of the person")

# 2) Pass the model to the agent
agent = Agent()
result = agent(
    "John Smith is a 30 year-old software engineer",
    structured_output_model=PersonInfo
)

# 3) Access the `structured_output` from the result
person_info: PersonInfo = result.structured_output
print(f"Name: {person_info.name}")      # "John Smith"
print(f"Age: {person_info.age}")        # 30
print(f"Job: {person_info.occupation}") # "software engineer"
```

```python
import asyncio
agent = Agent()
result = asyncio.run(
    agent.invoke_async(
        "John Smith is a 30 year-old software engineer",
        structured_output_model=PersonInfo
    )
)
```

```python
from pydantic import ValidationError
from strands.types.exceptions import StructuredOutputException

try:
    result = agent(prompt, structured_output_model=MyModel)
except StructuredOutputException as e:
    print(f"Structured output failed: {e}")
```

```python
from strands.agent import Agent
from pydantic import BaseModel, field_validator


class Name(BaseModel):
    first_name: str

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value: str) -> str:
        if not value.endswith('abc'):
            raise ValueError("You must append 'abc' to the end of my name")
        return value


agent = Agent()
result = agent("What is Aaron's name?", structured_output_model=Name)
```

```python
from strands import Agent
from pydantic import BaseModel, Field

class WeatherForecast(BaseModel):
    """Weather forecast data."""
    location: str
    temperature: int
    condition: str
    humidity: int
    wind_speed: int
    forecast_date: str

streaming_agent = Agent()

async for event in streaming_agent.stream_async(
    "Generate a weather forecast for Seattle: 68°F, partly cloudy, 55% humidity, 8 mph winds, for tomorrow",
    structured_output_model=WeatherForecast
):
    if "data" in event:
        print(event["data"], end="", flush=True)
    elif "result" in event:
        print(f'The forecast for today is: {event["result"].structured_output}')
```

```python
from strands import Agent
from strands_tools import calculator
from pydantic import BaseModel, Field

class MathResult(BaseModel):
    operation: str = Field(description="the performed operation")
    result: int = Field(description="the result of the operation")

tool_agent = Agent(
    tools=[calculator]
)
res = tool_agent("What is 42 + 8", structured_output_model=MathResult)
```

## Classes and Interfaces

- `pydantic.BaseModel`
- `pydantic.Field`
- `strands.Agent`
- `strands.agent.AgentResult`
- `strands.types.exceptions.StructuredOutputException`
- `pydantic.field_validator`
- `strands_tools.calculator`

## References

[1] [Strands Agents SDK — Structured Output](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/structured-output/index.md)
[2] [Pydantic Documentation — Models](https://docs.pydantic.dev/latest/concepts/models/)
[3] [Strands Agents SDK — Agent Class](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-class/index.md)
