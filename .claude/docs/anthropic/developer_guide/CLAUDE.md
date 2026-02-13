# Developer Guide Documentation Index

This index provides cross-links to all documentation files in this section, organized by category for quick reference.

---

## Getting Started

Start here for introductory guides, quickstarts, and model selection. Reference these when setting up new projects or choosing the right Claude model for your use case.

- [Intro to Claude](./intro_to_claude.md) - Claude is a highly performant, trustworthy, and intelligent AI platform built by
- [Quickstart - Get started with Claude](./quickstart_get_started_with_claude.md) - Make your first API call to Claude and build a simple web search assistant
- [Models overview](./models_overview.md) - Claude is a family of state-of-the-art large language models developed by Anthro
- [Choosing a model - Choosing the right model](./choosing_a_model_choosing_the_right_model.md) - Selecting the optimal Claude model for your application involves balancing three
- [What's new in Claude 4.6](./whats_new_in_claude_46.md) - Overview of new features and capabilities in Claude Opus 4.6
- [Features overview](./features_overview.md) - Explore Claude's advanced features and capabilities
- [Migration guide](./migration_guide.md) - Guide for migrating to Claude 4.6 models from previous Claude versions
- [Model deprecations](./model_deprecations.md) - As we launch safer and more capable models, we regularly retire older models

---

## Core API Usage

Fundamental API patterns, message handling, and request/response patterns. Reference these when implementing basic API integration with Claude.

- [Using the Messages API](./using_the_messages_api.md) - Practical patterns and examples for using the Messages API effectively
- [Streaming Messages](./streaming_messages.md) - Stream responses incrementally using server-sent events (SSE)
- [Streaming refusals](./streaming_refusals.md) - Starting with Claude 4 models, streaming responses from Claude's API return refusal information
- [Handling stop reasons](./handling_stop_reasons.md) - Detect refusals and other stop reasons directly from result messages
- [Token counting](./token_counting.md) - Token counting enables you to determine the number of tokens in a message before
- [Batch processing](./batch_processing.md) - Batch processing is a powerful approach for handling large volumes of requests
- [Files API](./files_api.md) - The Files API lets you upload and manage files to use with the Claude API

---

## Agent SDK

Build production AI agents with the Claude Agent SDK (formerly Claude Code). Reference these when building autonomous agents that execute code, use tools, and manage sessions.

- [Overview - Agent SDK overview](./overview_agent_sdk_overview.md) - Build production AI agents with Claude Code as a library
- [Quickstart](./quickstart.md) - Get started with the Python or TypeScript Agent SDK to build AI agents
- [Python SDK - Agent SDK reference - Python](./python_sdk_agent_sdk_reference_python.md) - Complete API reference for the Python Agent SDK
- [TypeScript SDK - Agent SDK reference - TypeScript](./typescript_sdk_agent_sdk_reference_typescript.md) - Complete API reference for the TypeScript Agent SDK
- [TypeScript V2 (preview) - TypeScript SDK V2 interface (preview)](./typescript_v2_preview_typescript_sdk_v2_interface_preview.md) - Preview of the simplified V2 TypeScript Agent SDK
- [Migration Guide - Migrate to Claude Agent SDK](./migration_guide_migrate_to_claude_agent_sdk.md) - Guide for migrating from the old Claude Code SDK to Claude Agent SDK
- [Session Management](./session_management.md) - Understanding how the Claude Agent SDK handles sessions and session resumption
- [Streaming Input](./streaming_input.md) - Understanding the two input modes for Claude Agent SDK
- [Stream responses in real-time](./stream_responses_in_real_time.md) - Get real-time responses from the Agent SDK as text and tool calls stream in
- [Structured outputs in the SDK - Get structured output from agents](./structured_outputs_in_the_sdk_get_structured_output_from_agents.md) - Return validated JSON from agent workflows using JSON Schema, Zod, or Pydantic
- [Hosting the Agent SDK](./hosting_the_agent_sdk.md) - Deploy and host Claude Agent SDK in production environments
- [Securely deploying AI agents](./securely_deploying_ai_agents.md) - A guide to securing Claude Code and Agent SDK deployments
- [Todo Lists](./todo_lists.md) - Track and display todos using the Claude Agent SDK
- [Tracking Costs and Usage](./tracking_costs_and_usage.md) - Understand and track token usage for billing in the Claude Agent SDK

---

## Tools & Tool Use

Custom tools, built-in tools, programmatic tool calling, and MCP integration. Reference these when extending Claude's capabilities with external functions and services.

- [Overview - Tool use with Claude](./overview_tool_use_with_claude.md) - Claude is capable of interacting with tools and functions
- [How to implement tool use](./how_to_implement_tool_use.md) - Best practices for implementing tool use with Claude
- [Custom Tools](./custom_tools.md) - Build and integrate custom tools to extend Claude Agent SDK functionality
- [Programmatic tool calling](./programmatic_tool_calling.md) - Allow Claude to write code that calls your tools programmatically within a code execution sandbox
- [Fine-grained tool streaming](./fine_grained_tool_streaming.md) - Fine-grained tool streaming is generally available on all models
- [Tool search - Tool search tool](./tool_search_tool_search_tool.md) - The tool search tool enables Claude to work with hundreds or thousands of tools
- [Code execution tool](./code_execution_tool.md) - Claude can analyze data, create visualizations, perform complex calculations
- [Computer use tool](./computer_use_tool.md) - Claude can interact with computer environments through the computer use tool
- [Bash tool](./bash_tool.md) - The bash tool enables Claude to execute shell commands in a persistent bash session
- [Text editor tool](./text_editor_tool.md) - Claude can use an Anthropic-defined text editor tool to view and modify text files
- [Memory tool](./memory_tool.md) - The memory tool enables Claude to store and retrieve information across conversations
- [Web search tool](./web_search_tool.md) - The web search tool gives Claude direct access to real-time web content
- [Web fetch tool](./web_fetch_tool.md) - The web fetch tool allows Claude to retrieve full content from specified web pages

---

## MCP (Model Context Protocol)

Connect Claude to external tools and data sources using the Model Context Protocol. Reference these when integrating databases, APIs, or third-party services.

- [MCP in the SDK - Connect to external tools with MCP](./mcp_in_the_sdk_connect_to_external_tools_with_mcp.md) - Configure MCP servers to extend your agent with external tools
- [MCP connector](./mcp_connector.md) - Claude's Model Context Protocol (MCP) connector feature
- [Remote MCP servers](./remote_mcp_servers.md) - Several companies have deployed remote MCP servers that developers can connect to

---

## Agent Skills

Modular capabilities that extend Claude's functionality with domain-specific expertise. Reference these when building reusable, specialized workflows.

- [Overview - Agent Skills](./overview_agent_skills.md) - Agent Skills are modular capabilities that extend Claude's functionality
- [Agent Skills in the SDK](./agent_skills_in_the_sdk.md) - Extend Claude with specialized capabilities using Agent Skills in the Claude Agent SDK
- [Quickstart - Get started with Agent Skills in the API](./quickstart_get_started_with_agent_skills_in_the_api.md) - Learn how to use Agent Skills to create documents with the Claude API
- [Using Skills with the API - Using Agent Skills with the API](./using_skills_with_the_api_using_agent_skills_with_the_api.md) - Learn how to use Agent Skills to extend Claude's capabilities through the API
- [Best practices - Skill authoring best practices](./best_practices_skill_authoring_best_practices.md) - Learn how to write effective Skills that Claude can discover and use
- [Skills for enterprise](./skills_for_enterprise.md) - Governance, security review, evaluation, and organizational guidance

---

## Agent SDK Extensions

Hooks, plugins, subagents, slash commands, and other advanced SDK features. Reference these when building complex agent behaviors or extending SDK functionality.

- [Control execution with hooks - Intercept and control agent behavior with hooks](./control_execution_with_hooks_intercept_and_control_agent_behavior_with_hooks.md) - Intercept and customize agent behavior at key execution points with hooks
- [Handling Permissions - Configure permissions](./handling_permissions_configure_permissions.md) - Control how your agent uses tools with permission modes, hooks, and declarative config
- [User approvals and input - Handle approvals and user input](./user_approvals_and_input_handle_approvals_and_user_input.md) - Surface Claude's approval requests and clarifying questions to users
- [Subagents in the SDK](./subagents_in_the_sdk.md) - Define and invoke subagents to isolate context, run tasks in parallel
- [Plugins in the SDK](./plugins_in_the_sdk.md) - Load custom plugins to extend Claude Code with commands, agents, skills
- [Slash Commands in the SDK](./slash_commands_in_the_sdk.md) - Learn how to use slash commands to control Claude Code sessions through the SDK
- [File checkpointing - Rewind file changes with checkpointing](./file_checkpointing_rewind_file_changes_with_checkpointing.md) - Track file changes during agent sessions and restore files to any previous state

---

## Prompt Engineering

Core techniques for crafting effective prompts, structured outputs, and advanced prompting patterns. Reference these when optimizing Claude's behavior for specific tasks.

- [Overview - Prompt engineering overview](./overview_prompt_engineering_overview.md) - This guide assumes that you have clear success criteria
- [Prompting best practices](./prompting_best_practices.md) - Prompt engineering techniques for Claude's latest models
- [Be clear and direct - Be clear, direct, and detailed](./be_clear_and_direct_be_clear_direct_and_detailed.md) - Think of Claude as a brilliant but very new employee
- [Use examples (multishot prompting) - Use examples (multishot prompting) to guide Claude's behavior](./use_examples_multishot_prompting_use_examples_multishot_prompting_to_guide_claudes_behavior.md) - Examples are your secret weapon for getting exact output formats
- [Let Claude think (CoT) - Let Claude think (chain of thought prompting) to increase performance](./let_claude_think_cot_let_claude_think_chain_of_thought_prompting_to_increase_performance.md) - Give Claude time to think for complex tasks
- [Use XML tags - Use XML tags to structure your prompts](./use_xml_tags_use_xml_tags_to_structure_your_prompts.md) - Structure multi-component prompts with XML tags
- [Chain complex prompts - Chain complex prompts for stronger performance](./chain_complex_prompts_chain_complex_prompts_for_stronger_performance.md) - Break complex tasks into multiple prompts
- [Give Claude a role (system prompts) - Giving Claude a role with a system prompt](./give_claude_a_role_system_prompts_giving_claude_a_role_with_a_system_prompt.md) - Dramatically improve performance using system prompts
- [Keep Claude in character - Keep Claude in character with role prompting and prefilling](./keep_claude_in_character_keep_claude_in_character_with_role_prompting_and_prefilling.md) - Keep Claude in character during long conversations
- [Use prompt templates - Use prompt templates and variables](./use_prompt_templates_use_prompt_templates_and_variables.md) - Deploy LLM applications with reusable prompt templates
- [Long context tips - Long context prompting tips](./long_context_tips_long_context_prompting_tips.md) - Handle Claude's extended 200K token context window effectively
- [Modifying system prompts](./modifying_system_prompts.md) - Customize Claude's behavior by modifying system prompts

---

## Structured Outputs & Validation

Grammar-constrained decoding, JSON schemas, and validated outputs. Reference these when you need guaranteed JSON structure or schema validation (critical for LLMitM's ActionGraph compilation).

- [Structured outputs](./structured_outputs.md) - Get validated JSON results from agent workflows
- [Increase output consistency](./increase_output_consistency.md) - Make Claude's responses more consistent
- [Citations](./citations.md) - Claude is capable of providing detailed citations when answering questions
- [Search results](./search_results.md) - Enable natural citations for RAG applications by providing search results

---

## Advanced Reasoning & Performance

Extended thinking, adaptive thinking, effort control, and optimization techniques. Reference these when building complex reasoning tasks or optimizing for quality vs. speed tradeoffs.

- [Extended thinking - Building with extended thinking](./extended_thinking_building_with_extended_thinking.md) - Extended thinking gives Claude enhanced reasoning capabilities
- [Extended thinking tips](./extended_thinking_tips.md) - Advanced strategies for getting the most out of extended thinking
- [Adaptive thinking](./adaptive_thinking.md) - Let Claude dynamically determine when and how much to use extended thinking
- [Effort](./effort.md) - Control how many tokens Claude uses when responding with the effort parameter
- [Fast mode (research preview)](./fast_mode_research_preview.md) - Higher output speed for Claude Opus 4.6

---

## Context Management

Managing context windows, prompt caching, compaction, and context editing. Reference these when optimizing token usage and managing long conversations.

- [Context windows](./context_windows.md) - Approach context window limits gracefully
- [Context editing](./context_editing.md) - Automatically manage conversation context as it grows
- [Compaction](./compaction.md) - Server-side context compaction for managing long conversations
- [Prompt caching](./prompt_caching.md) - Optimize API usage by caching prompt prefixes

---

## Multimodal Capabilities

Vision, PDF processing, and other non-text inputs. Reference these when working with images, documents, or visual data.

- [Vision](./vision.md) - Claude's vision capabilities allow it to understand and analyze images
- [PDF support](./pdf_support.md) - Process PDFs with Claude. Extract text, analyze charts, and understand visual content

---

## Quality & Safety

Reducing hallucinations, preventing jailbreaks, security best practices. Reference these when hardening production deployments or improving output reliability.

- [Define success criteria - Define your success criteria](./define_success_criteria_define_your_success_criteria.md) - Building successful LLM applications starts with clear success criteria
- [Develop test cases - Create strong empirical evaluations](./develop_test_cases_create_strong_empirical_evaluations.md) - Design evaluations to measure your success criteria
- [Using the Evaluation Tool](./using_the_evaluation_tool.md) - The Claude Console features an Evaluation tool
- [Reduce hallucinations](./reduce_hallucinations.md) - Techniques to reduce hallucinations in Claude's outputs
- [Mitigate jailbreaks - Mitigate jailbreaks and prompt injections](./mitigate_jailbreaks_mitigate_jailbreaks_and_prompt_injections.md) - Protect against prompt exploitation
- [Reduce prompt leak](./reduce_prompt_leak.md) - Prevent sensitive information exposure from system prompts

---

## Performance Optimization

Reducing latency, streaming, token optimization, and cost management. Reference these when optimizing API performance and costs (critical for LLMitM's token budget enforcement).

- [Reducing latency](./reducing_latency.md) - Minimize time for model processing and response generation
- [Pricing](./pricing.md) - Learn about Anthropic's pricing structure for models and features
- [Usage and Cost API](./usage_and_cost_api.md) - Programmatically access your organization's API usage and cost data

---

## Platform Integrations

Using Claude through AWS Bedrock, Azure/Microsoft Foundry, Google Vertex AI, and other cloud platforms. Reference these when deploying on cloud infrastructure.

- [Amazon Bedrock - Claude on Amazon Bedrock](./amazon_bedrock_claude_on_amazon_bedrock.md) - Anthropic's Claude models are available through Amazon Bedrock
- [Microsoft Foundry - Claude in Microsoft Foundry](./microsoft_foundry_claude_in_microsoft_foundry.md) - Access Claude models through Microsoft Foundry
- [Vertex AI - Claude on Vertex AI](./vertex_ai_claude_on_vertex_ai.md) - Anthropic's Claude models are available through Vertex AI

---

## Enterprise & Administration

Organization management, workspaces, admin API, analytics, and governance. Reference these when managing team access, API keys, or organizational deployments.

- [Admin API overview](./admin_api_overview.md) - Programmatically manage your organization's resources
- [Workspaces](./workspaces.md) - Organize API keys, manage team access, and control costs
- [Claude Code Analytics API](./claude_code_analytics_api.md) - Programmatically access your organization's Claude Code usage analytics
- [Data residency](./data_residency.md) - Manage where model inference runs and where data is stored
- [Zero Data Retention - Zero Data Retention (ZDR)](./zero_data_retention_zero_data_retention_zdr.md) - Learn about Anthropic's Zero Data Retention (ZDR) policy

---

## Additional Capabilities

Embeddings, multilingual support, and other specialized features. Reference these when working with non-English languages or semantic similarity tasks.

- [Embeddings](./embeddings.md) - Text embeddings are numerical representations enabling semantic similarity
- [Multilingual support](./multilingual_support.md) - Claude excels at tasks across multiple languages

---

## Tools & Utilities

Prompt generation, prompt improvement, and helper tools. Reference these when bootstrapping new prompts or iterating on existing ones.

- [Prompt generator - Automatically generate first draft prompt templates](./prompt_generator_automatically_generate_first_draft_prompt_templates.md) - Generate starting prompts automatically
- [Prompt improver - Use our prompt improver to optimize your prompts](./prompt_improver_use_our_prompt_improver_to_optimize_your_prompts.md) - Iterate and improve prompts through automated feedback
