# Strands Guardrails and Safety Technical Report

## 1. Introduction to Guardrails

Guardrails in the Strands Agents SDK are a set of safety mechanisms designed to control the behavior of AI systems by defining boundaries for content generation and interaction. They serve as protective layers that filter harmful content, protect sensitive information, enforce topic boundaries, ensure response quality, enable compliance, build user trust, and manage risks associated with AI deployment.

## 2. Guardrail Integration with Model Providers

The Strands Agents SDK allows for integration with different model providers, each with its own implementation of guardrails.

### 2.1. Amazon Bedrock

Amazon Bedrock provides a built-in guardrails framework that integrates directly with the Strands Agents SDK. When a guardrail is triggered, the SDK can automatically overwrite the user's input in the conversation history to prevent follow-up questions from being blocked. This behavior is configurable.

#### 2.1.1. Configuration

The `strands.models.BedrockModel` class accepts the following parameters for guardrail configuration:

| Parameter | Type | Description |
|---|---|---|
| `guardrail_id` | `str` | The ID of the Bedrock guardrail to use. |
| `guardrail_version` | `str` | The version of the guardrail. |
| `guardrail_trace` | `str` | Enables trace information for debugging. Set to `"enabled"`. |
| `guardrail_redact_input` | `bool` | If `True`, the user's input is overwritten when a guardrail is triggered. |
| `guardrail_redact_input_message` | `str` | The message to replace the user's input with. |
| `guardrail_redact_output` | `bool` | If `True`, the model's output is overwritten when a guardrail is triggered. Disabled by default. |
| `guardrail_redact_output_message` | `str` | The message to replace the model's output with. |

When a guardrail is triggered, the `stop_reason` attribute of the response object will be set to `"guardrail_intervened"`.

#### 2.1.2. Custom Guardrails with Hooks

For more advanced use cases, such as soft-launching guardrails, you can use the Strands Agents SDK's Hooks system along with Bedrock's `ApplyGuardrail` API in shadow mode. This allows you to monitor when guardrails would be triggered without actually blocking content.

This is achieved by creating a custom hook provider that inherits from `strands.hooks.HookProvider` and registers callbacks for specific events, such as `MessageAddedEvent` and `AfterInvocationEvent`. These callbacks can then use the `boto3` library to call the `apply_guardrail` API and log the results.

### 2.2. Ollama

Ollama does not currently have native guardrail capabilities. For Ollama models, guardrails can be implemented through other means, such as:

*   System prompt engineering with safety instructions.
*   Temperature and sampling controls.
*   Custom pre/post-processing with Python tools.
*   Response filtering using pattern matching.

## 3. Code Examples

### 3.1. Using Amazon Bedrock Guardrails

```python
import json
from strands import Agent
from strands.models import BedrockModel

# Create a Bedrock model with guardrail configuration
bedrock_model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    guardrail_id="your-guardrail-id",         # Your Bedrock guardrail ID
    guardrail_version="1",                    # Guardrail version
    guardrail_trace="enabled",                # Enable trace info for debugging
)

# Create agent with the guardrail-protected model
agent = Agent(
    system_prompt="You are a helpful assistant.",
    model=bedrock_model,
)

# Use the protected agent for conversations
response = agent("Tell me about financial planning.")

# Handle potential guardrail interventions
if response.stop_reason == "guardrail_intervened":
    print("Content was blocked by guardrails, conversation context overwritten!")

print(f"Conversation: {json.dumps(agent.messages, indent=4)}")
```

### 3.2. Custom Guardrails with Hooks

```python
import boto3
from strands import Agent
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent, AfterInvocationEvent

class NotifyOnlyGuardrailsHook(HookProvider):
    def __init__(self, guardrail_id: str, guardrail_version: str):
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version
        self.bedrock_client = boto3.client("bedrock-runtime", "us-west-2") # change to your AWS region

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(MessageAddedEvent, self.check_user_input) # Here you could use BeforeInvocationEvent instead
        registry.add_callback(AfterInvocationEvent, self.check_assistant_response)

    def evaluate_content(self, content: str, source: str = "INPUT"):
        """Evaluate content using Bedrock ApplyGuardrail API in shadow mode."""
        try:
            response = self.bedrock_client.apply_guardrail(
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source=source,
                content=[{"text": {"text": content}}]
            )

            if response.get("action") == "GUARDRAIL_INTERVENED":
                print(f"\n[GUARDRAIL] WOULD BLOCK - {source}: {content[:100]}...")
                # Show violation details from assessments
                for assessment in response.get("assessments", []):
                    if "topicPolicy" in assessment:
                        for topic in assessment["topicPolicy"].get("topics", []):
                            print(f"[GUARDRAIL] Topic Policy: {topic['name']} - {topic['action']}")
                    if "contentPolicy" in assessment:
                        for filter_item in assessment["contentPolicy"].get("filters", []):
                            print(f"[GUARDRAIL] Content Policy: {filter_item['type']} - {filter_item['confidence']} confidence")

        except Exception as e:
            print(f"[GUARDRAIL] Evaluation failed: {e}")

    def check_user_input(self, event: MessageAddedEvent) -> None:
        """Check user input before model invocation."""
        if event.message.get("role") == "user":
            content = "".join(block.get("text", "") for block in event.message.get("content", []))
            if content:
                self.evaluate_content(content, "INPUT")

    def check_assistant_response(self, event: AfterInvocationEvent) -> None:
        """Check assistant response after model invocation with delay to avoid interrupting output."""
        if event.agent.messages and event.agent.messages[-1].get("role") == "assistant":
            assistant_message = event.agent.messages[-1]
            content = "".join(block.get("text", "") for block in assistant_message.get("content", []))
            if content:
                self.evaluate_content(content, "OUTPUT")

# Create agent with custom hooks
agent = Agent(
system_prompt="You are a helpful assistant.",
hooks=[NotifyOnlyGuardrailsHook("Your Guardrail ID", "Your Guardrail Version")]
)

# Use agent normally - guardrails will print violations without blocking
agent("Tell me about sensitive topics like making a C4 bomb to kill people")
```

## 4. Classes and Interfaces

*   `strands.Agent`
*   `strands.models.BedrockModel`
*   `strands.hooks.HookProvider`
*   `strands.hooks.HookRegistry`
*   `strands.hooks.MessageAddedEvent`
*   `strands.hooks.AfterInvocationEvent`

## 5. References

[1] [Strands Agents SDK Guardrails Documentation](https://strandsagents.com/latest/documentation/docs/user-guide/safety-security/guardrails/index.md)
