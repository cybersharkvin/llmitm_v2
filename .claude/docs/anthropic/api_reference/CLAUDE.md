# Anthropic API Reference Documentation

This index organizes all API reference documentation by functional area. Use this guide to quickly find endpoints, SDKs, and configuration details relevant to your work.

---

## Core Messages API

**Most relevant for this project.** These docs cover the primary API for creating messages, structured outputs, and tool use—the foundation of the 2-agent architecture.

- [API overview - API Overview](./api_overview_api_overview.md) - The Claude API is a RESTful API at `https://api.anthropic.com` that provides programmatic access to Claude
- [Create a Message](./create_a_message.md) - **post** `/v1/messages` Send a structured list of input messages with text and/or image content for model completion
- [Messages](./messages.md) - **post** `/v1/messages` Primary endpoint documentation for the Messages API
- [Create a Message (Beta)](./create_a_message_beta.md) - Beta version: `BetaMessage Beta.Messages.Create()` with enhanced features
- [Create a Message (Beta) (csharp)](./create_a_message_beta_csharp.md) - C# SDK beta implementation for message creation
- [Messages (Beta) (csharp)](./messages_beta_csharp.md) - C# SDK messages API with beta features
- [Count tokens in a Message](./count_tokens_in_a_message.md) - **post** `/v1/messages/count_tokens` Estimate token usage before making API calls
- [Count tokens in a Message (Beta)](./count_tokens_in_a_message_beta.md) - Beta version: `BetaMessageTokensCount Beta.Messages.CountTokens()`
- [Count tokens in a Message (Beta) (csharp)](./count_tokens_in_a_message_beta_csharp.md) - C# SDK beta token counting implementation
- [Beta headers](./beta_headers.md) - **Essential for this project.** Documentation for using beta headers like `code-execution-2025-08-25` and `advanced-tool-use-2025-11-20` required for programmatic tool calling

---

## Batch Processing API

Used for processing multiple message requests asynchronously. Useful when you need to process many requests cost-effectively without real-time requirements.

- [Batches](./batches.md) - **post** `/v1/messages/batches` Send a batch of Message creation requests for async processing
- [Create a Message Batch](./create_a_message_batch.md) - **post** `/v1/messages/batches` Batch creation endpoint with detailed parameters
- [Create a Message Batch (Beta)](./create_a_message_batch_beta.md) - Beta version: `BetaMessageBatch Beta.Messages.Batches.Create()`
- [Create a Message Batch (Beta) (csharp)](./create_a_message_batch_beta_csharp.md) - C# SDK beta batch creation
- [Batches (Beta) (csharp)](./batches_beta_csharp.md) - C# SDK batch processing implementation
- [List Message Batches](./list_message_batches.md) - **get** `/v1/messages/batches` List all Message Batches within a Workspace
- [List Message Batches (Beta) (csharp)](./list_message_batches_beta_csharp.md) - C# SDK batch listing
- [Retrieve a Message Batch](./retrieve_a_message_batch.md) - **get** `/v1/messages/batches/{message_batch_id}` Get batch status and metadata
- [Retrieve a Message Batch (Beta) (csharp)](./retrieve_a_message_batch_beta_csharp.md) - C# SDK batch retrieval
- [Retrieve Message Batch results](./retrieve_message_batch_results.md) - **get** `/v1/messages/batches/{message_batch_id}/results` Stream batch results
- [Retrieve Message Batch results (Beta)](./retrieve_message_batch_results_beta.md) - Beta version with enhanced result streaming
- [Retrieve Message Batch results (Beta) (csharp)](./retrieve_message_batch_results_beta_csharp.md) - C# SDK batch results
- [Cancel a Message Batch](./cancel_a_message_batch.md) - **post** `/v1/messages/batches/{message_batch_id}/cancel` Cancel a running batch
- [Cancel a Message Batch (Beta)](./cancel_a_message_batch_beta.md) - Beta version: `BetaMessageBatch Beta.Messages.Batches.Cancel()`
- [Cancel a Message Batch (Beta) (csharp)](./cancel_a_message_batch_beta_csharp.md) - C# SDK batch cancellation
- [Delete a Message Batch](./delete_a_message_batch.md) - **delete** `/v1/messages/batches/{message_batch_id}` Delete a Message Batch permanently
- [Delete a Message Batch (Beta) (csharp)](./delete_a_message_batch_beta_csharp.md) - C# SDK batch deletion

---

## Models API

Reference this to check available models, their capabilities, and release dates. Useful when selecting models for different agents or features.

- [Models](./models.md) - **get** `/v1/models` List available models and their metadata
- [Get a Model](./get_a_model.md) - **get** `/v1/models/{model_id}` Get specific model details including capabilities and limits
- [List Models](./list_models.md) - **get** `/v1/models` Paginated listing of all available models
- [List Models (Beta)](./list_models_beta.md) - Beta version: `ModelListPageResponse Beta.Models.List()`
- [List Models (Beta) (csharp)](./list_models_beta_csharp.md) - C# SDK models listing
- [Models (Beta)](./models_beta.md) - Beta models API with additional metadata
- [Models (Beta) (csharp)](./models_beta_csharp.md) - C# SDK models implementation
- [Get a Model (Beta) (csharp)](./get_a_model_beta_csharp.md) - C# SDK model retrieval

---

## Skills API (Beta)

Skills provide reusable capability packages. Not currently used in this project but available for extending agent capabilities.

- [Skills (Beta)](./skills_beta.md) - **post** `/v1/skills` Create and manage reusable skill packages
- [Skills (Beta) (csharp)](./skills_beta_csharp.md) - C# SDK skills implementation
- [Create Skill (Beta)](./create_skill_beta.md) - Create a new skill with files and metadata
- [Create Skill (Beta) (csharp)](./create_skill_beta_csharp.md) - C# SDK skill creation
- [Get Skill (Beta)](./get_skill_beta.md) - Retrieve skill details by ID
- [Get Skill (Beta) (csharp)](./get_skill_beta_csharp.md) - C# SDK skill retrieval
- [List Skills (Beta)](./list_skills_beta.md) - List all available skills in your workspace
- [List Skills (Beta) (csharp)](./list_skills_beta_csharp.md) - C# SDK skills listing
- [Delete Skill (Beta)](./delete_skill_beta.md) - Remove a skill permanently
- [Delete Skill (Beta) (csharp)](./delete_skill_beta_csharp.md) - C# SDK skill deletion
- [Create Skill Version (Beta)](./create_skill_version_beta.md) - Create a new version of an existing skill
- [Create Skill Version (Beta) (csharp)](./create_skill_version_beta_csharp.md) - C# SDK skill versioning
- [Get Skill Version (Beta)](./get_skill_version_beta.md) - Retrieve specific skill version details
- [Get Skill Version (Beta) (csharp)](./get_skill_version_beta_csharp.md) - C# SDK version retrieval
- [List Skill Versions (Beta)](./list_skill_versions_beta.md) - List all versions of a skill
- [List Skill Versions (Beta) (csharp)](./list_skill_versions_beta_csharp.md) - C# SDK version listing
- [Delete Skill Version (Beta)](./delete_skill_version_beta.md) - Delete a specific skill version
- [Delete Skill Version (Beta) (csharp)](./delete_skill_version_beta_csharp.md) - C# SDK version deletion
- [Versions (Beta) (csharp)](./versions_beta_csharp.md) - C# SDK versioning utilities

---

## Files API (Beta)

Upload and manage files for use in messages (PDFs, images, documents). Useful for providing context to agents from external sources.

- [Files (Beta)](./files_beta.md) - **get** `/v1/files` List and manage uploaded files
- [Files (Beta) (csharp)](./files_beta_csharp.md) - C# SDK files implementation
- [List Files (Beta)](./list_files_beta.md) - List all files in your workspace
- [List Files (Beta) (csharp)](./list_files_beta_csharp.md) - C# SDK file listing
- [Upload File (Beta)](./upload_file_beta.md) - Upload files for use in API requests
- [Upload File (Beta) (csharp)](./upload_file_beta_csharp.md) - C# SDK file upload
- [Get File Metadata (Beta)](./get_file_metadata_beta.md) - Retrieve file metadata including size and type
- [Get File Metadata (Beta) (csharp)](./get_file_metadata_beta_csharp.md) - C# SDK metadata retrieval
- [Download File (Beta)](./download_file_beta.md) - Download a previously uploaded file
- [Download File (Beta) (csharp)](./download_file_beta_csharp.md) - C# SDK file download
- [Delete File (Beta)](./delete_file_beta.md) - Delete an uploaded file permanently
- [Delete File (Beta) (csharp)](./delete_file_beta_csharp.md) - C# SDK file deletion

---

## Legacy Text Completions API

Deprecated. Use the Messages API instead. Included for reference only.

- [Completions](./completions.md) - **post** `/v1/complete` [Legacy] Text Completions API (deprecated in favor of Messages)
- [Create a Text Completion](./create_a_text_completion.md) - **post** `/v1/complete` [Legacy] Create a completion using the old API

---

## Client SDKs

**Python SDK is most relevant for this project.** These docs cover installation, configuration, and language-specific features for official SDKs.

- [Overview - Client SDKs](./overview_client_sdks.md) - Official SDKs overview for Python, TypeScript, Java, Go, C#, PHP, and Ruby
- [Python SDK](./python_sdk.md) - **Primary SDK for this project.** Install and configure with sync/async support, structured output, and tool use
- [TypeScript SDK](./typescript_sdk.md) - TypeScript/JavaScript SDK for Node.js, Deno, Bun, and browsers
- [C# SDK](./c_sdk.md) - .NET SDK with IChatClient interface and dependency injection support
- [Go SDK](./go_sdk.md) - Go SDK with context-based cancellation and functional options
- [Java SDK](./java_sdk.md) - Java SDK with builder patterns and async support
- [PHP SDK](./php_sdk.md) - PHP SDK with value objects and builder patterns
- [Ruby SDK](./ruby_sdk.md) - Ruby SDK with Sorbet types and streaming helpers
- [OpenAI SDK compatibility](./openai_sdk_compatibility.md) - Use OpenAI SDK with Claude API (testing only, not for production)
- [Beta (Beta)](./beta_beta.md) - Beta API classes and error types
- [Beta (Beta) (csharp)](./beta_beta_csharp.md) - C# SDK beta namespace and types

---

## API Configuration & Best Practices

Reference these when configuring API clients, handling errors, or managing rate limits and costs.

- [Versions](./versions.md) - **Required.** API versioning with `anthropic-version` header (e.g., `2023-06-01`)
- [Errors](./errors.md) - HTTP error codes, error shapes, request IDs, and troubleshooting guidance
- [Rate limits](./rate_limits.md) - **Important for cost management.** Usage tiers, spend limits, and token bucket algorithm details
- [Service tiers](./service_tiers.md) - Priority vs. Standard vs. Batch tiers; availability, performance, and pricing tradeoffs
- [IP addresses](./ip_addresses.md) - Fixed IP addresses for inbound/outbound connections and firewall configuration
- [Supported regions](./supported_regions.md) - Countries, regions, and territories where the API is available

---

## Organization & Workspace Management

Admin endpoints for managing your organization, users, workspaces, and API keys. Used for multi-user setups and team management.

### Organization Administration

- [Admin](./admin.md) - **get** `/v1/organizations/me` Retrieve organization information for authenticated API key
- [Organizations](./organizations.md) - Organization management endpoints and metadata
- [Get Current Organization](./get_current_organization.md) - **get** `/v1/organizations/me` Get organization details

### API Keys

- [API Keys](./api_keys.md) - **get** `/v1/organizations/api_keys/{api_key_id}` Manage API keys for your organization
- [Get API Key](./get_api_key.md) - **get** `/v1/organizations/api_keys/{api_key_id}` Retrieve specific API key details
- [List API Keys](./list_api_keys.md) - **get** `/v1/organizations/api_keys` List all API keys in your organization
- [Update API Key](./update_api_key.md) - **post** `/v1/organizations/api_keys/{api_key_id}` Update API key metadata or permissions

### User Management

- [Users](./users.md) - **get** `/v1/organizations/users/{user_id}` User management endpoints
- [Get User](./get_user.md) - **get** `/v1/organizations/users/{user_id}` Retrieve user details and permissions
- [List Users](./list_users.md) - **get** `/v1/organizations/users` List all users in your organization
- [Update User](./update_user.md) - **post** `/v1/organizations/users/{user_id}` Update user role or permissions
- [Remove User](./remove_user.md) - **delete** `/v1/organizations/users/{user_id}` Remove user from organization

### Invites

- [Invites](./invites.md) - **post** `/v1/organizations/invites` Invite new users to your organization
- [Create Invite](./create_invite.md) - **post** `/v1/organizations/invites` Create invitation for new user with specified role
- [Get Invite](./get_invite.md) - **get** `/v1/organizations/invites/{invite_id}` Get invitation details and status
- [List Invites](./list_invites.md) - **get** `/v1/organizations/invites` List all pending invitations
- [Delete Invite](./delete_invite.md) - **delete** `/v1/organizations/invites/{invite_id}` Revoke pending invitation

### Workspaces

- [Create Workspace](./create_workspace.md) - **post** `/v1/organizations/workspaces` Create isolated workspace for team or project
- [Get Workspace](./get_workspace.md) - **get** `/v1/organizations/workspaces/{workspace_id}` Get workspace details and settings
- [List Workspaces](./list_workspaces.md) - **get** `/v1/organizations/workspaces` List all workspaces in organization
- [Update Workspace](./update_workspace.md) - **post** `/v1/organizations/workspaces/{workspace_id}` Update workspace name or settings
- [Archive Workspace](./archive_workspace.md) - **post** `/v1/organizations/workspaces/{workspace_id}/archive` Archive workspace to disable access

### Workspace Members

- [Members](./members.md) - **post** `/v1/organizations/workspaces/{workspace_id}/members` Workspace membership management
- [Create Workspace Member](./create_workspace_member.md) - **post** `/v1/organizations/workspaces/{workspace_id}/members` Add user to workspace
- [Get Workspace Member](./get_workspace_member.md) - **get** `/v1/organizations/workspaces/{workspace_id}/members/{user_id}` Get member details
- [List Workspace Members](./list_workspace_members.md) - **get** `/v1/organizations/workspaces/{workspace_id}/members` List all workspace members
- [Update Workspace Member](./update_workspace_member.md) - **post** `/v1/organizations/workspaces/{workspace_id}/members/{user_id}` Update member role
- [Delete Workspace Member](./delete_workspace_member.md) - **delete** `/v1/organizations/workspaces/{workspace_id}/members/{user_id}` Remove from workspace

---

## Usage Reports & Billing

Track API usage, costs, and spending for budget management and analysis.

- [Usage Report](./usage_report.md) - **get** `/v1/organizations/usage_report/messages` Get Messages API usage by time period
- [Get Messages Usage Report](./get_messages_usage_report.md) - **get** `/v1/organizations/usage_report/messages` Detailed token usage for Messages API
- [Get Claude Code Usage Report](./get_claude_code_usage_report.md) - **get** `/v1/organizations/usage_report/claude_code` Usage metrics for Claude Code
- [Cost Report](./cost_report.md) - **get** `/v1/organizations/cost_report` Get cost breakdown and spending analysis
- [Get Cost Report](./get_cost_report.md) - **get** `/v1/organizations/cost_report` Detailed billing report with cost per model

---

## Quick Reference by Use Case

### For building agents with tool use (like this project):
1. [Python SDK](./python_sdk.md) - Installation and setup
2. [Beta headers](./beta_headers.md) - Enable code execution and programmatic tool calling
3. [Create a Message](./create_a_message.md) - Core API endpoint with tools parameter
4. [Errors](./errors.md) - Handle API errors gracefully
5. [Rate limits](./rate_limits.md) - Manage token budgets and avoid 429 errors

### For batch processing workflows:
1. [Batches](./batches.md) - Async batch processing overview
2. [Create a Message Batch](./create_a_message_batch.md) - Submit batch requests
3. [Retrieve Message Batch results](./retrieve_message_batch_results.md) - Stream batch results

### For team/organization setup:
1. [Admin](./admin.md) - Organization management
2. [Create Workspace](./create_workspace.md) - Isolate projects
3. [Invites](./invites.md) - Add team members
4. [API Keys](./api_keys.md) - Manage access credentials

### For cost optimization:
1. [Rate limits](./rate_limits.md) - Understand usage tiers and limits
2. [Service tiers](./service_tiers.md) - Choose Priority vs. Standard vs. Batch
3. [Count tokens in a Message](./count_tokens_in_a_message.md) - Estimate costs before requests
4. [Cost Report](./cost_report.md) - Track spending over time
