# Policies

AgentEthan2 provides execution policies to control retry behavior, rate limiting, data masking, permissions, and cost management.

## Overview

Policies are configured in the `policies` section of your YAML configuration:

```yaml
policies:
  retry: {...}
  rate_limit: {...}
  masking: {...}
  permissions: {...}
  cost: {...}
```

---

## Retry Policy

Automatically retry failed operations with configurable backoff strategies.

### Configuration

```yaml
policies:
  retry:
    default:
      strategy: exponential  # fixed, exponential, jitter
      max_attempts: 3
      interval: 1.0          # seconds
      jitter: 0.5            # for jitter strategy
    overrides:
      - target: critical_node
        strategy: exponential
        max_attempts: 5
        interval: 2.0
```

### Fields

- **`default`**: Default retry policy for all nodes
  - `strategy`: Retry strategy (`fixed`, `exponential`, `jitter`)
  - `max_attempts`: Maximum number of retry attempts (minimum 1)
  - `interval`: Base interval in seconds between retries
  - `jitter`: Jitter range for random delay (jitter strategy only)
- **`overrides`**: Node-specific retry policies
  - `target`: Node ID to apply this policy to
  - Same fields as `default`

### Retry Strategies

#### Fixed
Retries with a constant interval.

```yaml
strategy: fixed
interval: 2.0  # Always wait 2 seconds
```

#### Exponential
Doubles the interval on each retry.

```yaml
strategy: exponential
interval: 1.0
# Attempts: 1s, 2s, 4s, 8s, ...
```

#### Jitter
Adds random delay to prevent thundering herd.

```yaml
strategy: jitter
interval: 1.0
jitter: 0.5
# Base delay + random(0, 0.5)
```

### Retryable Errors

Automatically retries on:
- HTTP status 429 (Too Many Requests)
- HTTP status 5xx (Server Errors)
- `TimeoutError`
- `ConnectionError`
- Errors containing "timeout", "temporarily", or "retry" in the message

### Events

Emits `retry.attempt` event:

```json
{
  "event": "retry.attempt",
  "node_id": "llm1",
  "attempt": 2,
  "delay": 2.0,
  "error": "Connection timeout"
}
```

### Example

```yaml
meta:
  version: 2

policies:
  retry:
    default:
      strategy: exponential
      max_attempts: 3
      interval: 1.0
    overrides:
      - target: external_api
        strategy: exponential
        max_attempts: 5
        interval: 2.0

components:
  - id: flaky
    type: custom_logic
    # Will retry up to 3 times with exponential backoff

  - id: external_api
    type: tool
    # Will retry up to 5 times with 2s initial interval
```

---

## Rate Limiting

Control the rate of requests to providers and nodes to avoid hitting API limits.

### Configuration

```yaml
policies:
  rate_limit:
    providers:
      - target: openai
        type: token_bucket
        capacity: 10
        refill_rate: 5.0      # 5 tokens per second
    nodes:
      - target: search_node
        type: fixed_window
        limit: 3
        window: 1.0           # 3 requests per second
    shared_providers:
      openai_gpt4: openai_shared
      openai_gpt35: openai_shared
```

### Rate Limiter Types

#### Token Bucket

Refills tokens at a constant rate. Allows bursts up to capacity.

```yaml
type: token_bucket
capacity: 10      # Max burst size
refill_rate: 2.0  # 2 tokens per second
```

- **Use case**: API with burst allowance
- **Behavior**: Can make 10 requests immediately, then 2 per second

#### Fixed Window

Allows a fixed number of requests per time window.

```yaml
type: fixed_window
limit: 5       # Max requests
window: 1.0    # Per second
```

- **Use case**: Strict rate limits
- **Behavior**: 5 requests per second, resets every second

### Shared Rate Limits

Share rate limits across multiple providers:

```yaml
rate_limit:
  providers:
    - target: openai_shared
      type: token_bucket
      capacity: 20
      refill_rate: 10.0
  shared_providers:
    openai_gpt4: openai_shared    # Both share the same limiter
    openai_gpt35: openai_shared
```

### Events

Emits `rate.limit.wait` event when waiting:

```json
{
  "event": "rate.limit.wait",
  "scope": "provider",
  "target": "openai",
  "wait_time": 0.5
}
```

### Example

```yaml
policies:
  rate_limit:
    providers:
      - target: openai
        type: token_bucket
        capacity: 60
        refill_rate: 1.0  # 1 request per second, burst of 60
    nodes:
      - target: expensive_node
        type: fixed_window
        limit: 10
        window: 60.0      # 10 requests per minute
```

---

## Masking Policy

Mask sensitive data in telemetry before export.

### Configuration

```yaml
policies:
  masking:
    fields:
      - inputs.api_key
      - inputs.password
      - outputs.secret
    diff_fields:
      - state.user_data
    mask_value: "***REDACTED***"
```

### Fields

- **`fields`**: Always mask these fields (dot-notation paths)
- **`diff_fields`**: Mask if value changes between events in the same run
- **`mask_value`**: String to replace sensitive values (default: `"***"`)

### Path Syntax

Use dot notation to specify nested fields:

```yaml
fields:
  - inputs.user.password           # Mask inputs.user.password
  - outputs.api_response.token     # Mask outputs.api_response.token
  - state.credentials              # Mask state.credentials
```

### Diff Masking

Useful for masking values that change (like session tokens):

```yaml
diff_fields:
  - state.session_token
```

- First occurrence: exported as-is
- Subsequent occurrences: masked if value changed

### Example

```yaml
policies:
  masking:
    fields:
      - inputs.api_key
      - inputs.password
      - outputs.auth_token
    diff_fields:
      - state.session_id
    mask_value: "***"

runtime:
  exporters:
    - type: jsonl
      path: run.jsonl  # Logs will have masked values
```

**Before masking**:
```json
{"event": "node.start", "inputs": {"api_key": "sk-abc123", "prompt": "Hello"}}
```

**After masking**:
```json
{"event": "node.start", "inputs": {"api_key": "***", "prompt": "Hello"}}
```

---

## Permissions Policy

Control which tools can be executed based on required permissions.

### Configuration

```yaml
policies:
  permissions:
    default_allow:
      - read:data
      - http:get
    allow:
      search_tool:
        - http:post
        - external:api
      admin_tool:
        - fs:write
        - exec:shell
```

### Fields

- **`default_allow`**: Permissions allowed for all tools by default
- **`allow`**: Tool-specific permission grants (keyed by tool/component ID)

### Tool Requirements

Tools declare required permissions:

```python
def search_tool_factory(tool, provider):
    instance = SearchTool(config=tool.config)
    instance.permissions = ["http:post", "external:api"]
    return instance
```

### Permission Check

At runtime, AgentEthan2 checks:
1. Tool declares `permissions` attribute
2. All required permissions are in `default_allow` OR tool-specific `allow`
3. If any permission is missing → `ERR_TOOL_PERMISSION_DENIED`

### Example

```yaml
policies:
  permissions:
    default_allow:
      - http:get
      - read:data
    allow:
      web_scraper:
        - http:post
        - fs:write
      admin_command:
        - exec:shell
        - fs:write

components:
  - id: web_scraper
    type: tool
    # Can use http:post and fs:write

  - id: safe_reader
    type: tool
    # Can only use http:get and read:data
```

### Error Handling

```python
try:
    result = agent.run_sync({"command": "rm -rf /"})
except GraphExecutionError as e:
    if e.code == "ERR_TOOL_PERMISSION_DENIED":
        print(f"Permission denied: {e.message}")
```

---

## Cost Management

Limit LLM token usage per run or globally.

### Configuration

```yaml
policies:
  cost:
    per_run_tokens: 10000  # Max tokens per run
```

### Fields

- **`per_run_tokens`**: Maximum total tokens (input + output) per run

### Tracking

Automatically tracks tokens from `llm.call` events:

```json
{
  "event": "llm.call",
  "tokens_in": 50,
  "tokens_out": 200
}
```

### Error

Raises `ERR_COST_LIMIT_EXCEEDED` when limit is reached:

```python
try:
    result = agent.run_sync({"prompt": "Very long prompt..."})
except GraphExecutionError as e:
    if e.code == "ERR_COST_LIMIT_EXCEEDED":
        print(f"Token limit exceeded: {e.message}")
```

### Example

```yaml
policies:
  cost:
    per_run_tokens: 5000  # Max 5000 tokens per run

components:
  - id: llm
    type: llm
    provider: openai
    # Will fail if total tokens exceed 5000
```

---

## Combining Policies

All policies work together:

```yaml
policies:
  retry:
    default:
      strategy: exponential
      max_attempts: 3
      interval: 1.0
  
  rate_limit:
    providers:
      - target: openai
        type: token_bucket
        capacity: 60
        refill_rate: 1.0
  
  masking:
    fields:
      - inputs.api_key
    mask_value: "***"
  
  permissions:
    default_allow:
      - http:get
    allow:
      admin_tool:
        - fs:write
  
  cost:
    per_run_tokens: 10000
```

---

## Best Practices

### 1. Use Exponential Backoff for External APIs

```yaml
retry:
  overrides:
    - target: external_api
      strategy: exponential
      max_attempts: 5
```

### 2. Set Conservative Rate Limits

```yaml
rate_limit:
  providers:
    - target: openai
      type: token_bucket
      capacity: 60
      refill_rate: 0.5  # Slightly below actual limit
```

### 3. Always Mask Credentials

```yaml
masking:
  fields:
    - inputs.api_key
    - inputs.password
    - outputs.auth_token
    - outputs.session_id
```

### 4. Use Principle of Least Privilege

```yaml
permissions:
  default_allow: []  # Deny by default
  allow:
    specific_tool:
      - http:get  # Only what's needed
```

### 5. Set Cost Limits

```yaml
cost:
  per_run_tokens: 10000  # Prevent runaway costs
```

---

## Related Documentation

- [Error Codes](./errors.md) - Policy-related error codes
- [Events](./events.md) - Policy-related events
- [YAML Reference](./yaml_reference.md) - Complete policy syntax
- [Examples](../examples/05_retry_ratelimit/) - Working examples

