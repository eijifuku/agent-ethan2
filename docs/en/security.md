# Security Guide

Best practices for securing your AgentEthan2 applications.

## Overview

This guide covers:
- API key and secret management
- Safe custom component development
- Permission management
- Data masking
- Input validation
- Secure deployment

---

## Secret Management

### Never Hardcode Secrets

**❌ Bad**:
```yaml
providers:
  - id: openai
    type: openai
    config:
      api_key: "sk-abc123..."  # NEVER DO THIS
```

**✅ Good**:
```yaml
providers:
  - id: openai
    type: openai
    # Load from environment in factory
```

### Use Environment Variables

```python
# factories.py
import os

def openai_provider_factory(provider):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    return {
        "client": OpenAI(api_key=api_key),
        "model": provider.config.get("model", "gpt-4"),
    }
```

### Environment Files

Use `.env` files (never commit to git):

```bash
# .env
OPENAI_API_KEY=sk-abc123...
ANTHROPIC_API_KEY=sk-ant-abc123...
DATABASE_URL=postgresql://...
```

**`.gitignore`**:
```
.env
.env.*
*.key
secrets/
```

### Secrets Management Services

For production, use dedicated services:

- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

def openai_provider_factory(provider):
    api_key = get_secret("openai-api-key")
    return {"client": OpenAI(api_key=api_key)}
```

---

## Safe Custom Components

### Input Validation

Always validate inputs in custom components:

```python
async def search_component(state, inputs, ctx):
    # Validate inputs
    query = inputs.get("query")
    if not query or not isinstance(query, str):
        raise ValueError("Invalid query: must be non-empty string")
    
    if len(query) > 1000:
        raise ValueError("Query too long: max 1000 characters")
    
    # Sanitize query
    query = query.strip()
    
    # Execute search
    results = await search_api.search(query)
    return {"results": results}
```

### Avoid Code Execution

**❌ Dangerous**:
```python
# NEVER DO THIS
async def eval_component(state, inputs, ctx):
    code = inputs.get("code")
    result = eval(code)  # DANGEROUS!
    return {"result": result}
```

**✅ Safe**:
```python
# Use sandboxed execution or predefined operations
async def calc_component(state, inputs, ctx):
    operation = inputs.get("operation")
    a = inputs.get("a")
    b = inputs.get("b")
    
    allowed_ops = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
    }
    
    if operation not in allowed_ops:
        raise ValueError(f"Operation not allowed: {operation}")
    
    return {"result": allowed_ops[operation](a, b)}
```

### File System Access

Use permissions and validation:

```python
async def read_file_component(state, inputs, ctx):
    filepath = inputs.get("filepath")
    
    # Validate path
    import os
    from pathlib import Path
    
    # Prevent directory traversal
    filepath = Path(filepath).resolve()
    allowed_dir = Path("/app/data").resolve()
    
    if not filepath.is_relative_to(allowed_dir):
        raise ValueError(f"Access denied: {filepath}")
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Read file
    with open(filepath, 'r') as f:
        content = f.read()
    
    return {"content": content}

# Declare permissions
read_file_component.permissions = ["fs:read"]
```

### SQL Injection Prevention

**❌ Vulnerable**:
```python
async def query_db(state, inputs, ctx):
    user_id = inputs.get("user_id")
    query = f"SELECT * FROM users WHERE id = {user_id}"  # VULNERABLE!
    result = await db.execute(query)
    return {"result": result}
```

**✅ Safe**:
```python
async def query_db(state, inputs, ctx):
    user_id = inputs.get("user_id")
    
    # Use parameterized queries
    query = "SELECT * FROM users WHERE id = ?"
    result = await db.execute(query, (user_id,))
    
    return {"result": result}
```

### HTTP Request Safety

```python
async def api_call_component(state, inputs, ctx):
    url = inputs.get("url")
    
    # Whitelist allowed domains
    from urllib.parse import urlparse
    
    allowed_domains = ["api.example.com", "data.example.com"]
    parsed = urlparse(url)
    
    if parsed.hostname not in allowed_domains:
        raise ValueError(f"Domain not allowed: {parsed.hostname}")
    
    # Set timeouts
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return {"data": response.json()}

api_call_component.permissions = ["http:get"]
```

---

## Permission Management

### Principle of Least Privilege

Only grant necessary permissions:

```yaml
policies:
  permissions:
    default_allow: []  # Deny all by default
    allow:
      # Grant specific permissions to specific tools
      file_reader:
        - fs:read
      web_scraper:
        - http:get
      admin_tool:
        - fs:read
        - fs:write
        - exec:shell  # Be very careful with this!
```

### Standard Permissions

Define clear permission namespaces:

```
fs:read          - Read filesystem
fs:write         - Write filesystem
http:get         - HTTP GET requests
http:post        - HTTP POST requests
db:read          - Database read
db:write         - Database write
exec:shell       - Execute shell commands
external:api     - Call external APIs
```

### Component Permission Declaration

```python
def tool_factory(tool, provider):
    instance = MyTool(config=tool.config)
    
    # Declare required permissions
    instance.permissions = ["http:get", "fs:read"]
    
    return instance
```

### Runtime Permission Checks

AgentEthan2 automatically checks permissions before tool execution:

1. Tool declares `permissions` attribute
2. Runtime checks against `policies.permissions`
3. Raises `ERR_TOOL_PERMISSION_DENIED` if unauthorized

---

## Data Masking

### Sensitive Data

Always mask sensitive data in logs:

```yaml
policies:
  masking:
    fields:
      # Credentials
      - inputs.api_key
      - inputs.password
      - inputs.auth_token
      - outputs.session_token
      
      # Personal data
      - inputs.ssn
      - inputs.credit_card
      - outputs.user_email
      - outputs.phone_number
      
      # Business secrets
      - inputs.api_secret
      - outputs.private_key
    
    mask_value: "***REDACTED***"
```

### PII (Personally Identifiable Information)

```yaml
masking:
  fields:
    - inputs.user.email
    - inputs.user.phone
    - inputs.user.address
    - outputs.customer.ssn
    - state.session.user_id
```

### Diff Masking for Session Data

```yaml
masking:
  diff_fields:
    - state.session_token
    - state.csrf_token
  # Masks when value changes (prevents token leakage)
```

---

## Input Validation

### Validate All Inputs

```python
from typing import Any, Mapping

def validate_inputs(inputs: Mapping[str, Any]) -> None:
    """Validate component inputs."""
    
    # Type validation
    prompt = inputs.get("prompt")
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    
    # Length validation
    if len(prompt) > 10000:
        raise ValueError("prompt exceeds maximum length (10000)")
    
    # Content validation (example: no malicious patterns)
    forbidden_patterns = ["<script>", "javascript:", "data:"]
    prompt_lower = prompt.lower()
    for pattern in forbidden_patterns:
        if pattern in prompt_lower:
            raise ValueError(f"Forbidden pattern detected: {pattern}")

async def my_component(state, inputs, ctx):
    validate_inputs(inputs)
    # ... rest of component logic
```

### Schema Validation

Use libraries like Pydantic:

```python
from pydantic import BaseModel, Field, validator

class ComponentInputs(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    max_results: int = Field(10, ge=1, le=100)
    filters: dict = Field(default_factory=dict)
    
    @validator('query')
    def validate_query(cls, v):
        if '<script>' in v.lower():
            raise ValueError('Invalid query content')
        return v

async def search_component(state, inputs, ctx):
    # Validate and parse inputs
    validated = ComponentInputs(**inputs)
    
    # Use validated inputs
    results = await search_api.query(
        query=validated.query,
        limit=validated.max_results,
        filters=validated.filters,
    )
    return {"results": results}
```

---

## Secure Deployment

### Container Security

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Run as non-root user
RUN useradd -m -u 1000 agent
USER agent

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=agent:agent . .

# Run application
CMD ["python", "main.py"]
```

### Network Security

Limit network access:

```yaml
# docker-compose.yml
services:
  agent:
    networks:
      - internal
    # No external network access unless needed

networks:
  internal:
    internal: true
```

### Environment Isolation

```bash
# Use separate environments
export ENV=production
export LOG_LEVEL=warning
export ENABLE_DEBUG=false
```

### Rate Limiting

Prevent abuse:

```yaml
policies:
  rate_limit:
    providers:
      - target: openai
        type: token_bucket
        capacity: 60
        refill_rate: 1.0  # 1 req/sec
```

### Monitoring

Monitor for security issues:

```yaml
runtime:
  exporters:
    - type: jsonl
      path: /var/log/agent/security.jsonl
```

Watch for:
- `ERR_TOOL_PERMISSION_DENIED`
- `rate.limit.wait` events
- Unusual input patterns
- Failed authentication attempts

---

## Incident Response

### Logging

Comprehensive logging for investigation:

```yaml
runtime:
  exporters:
    - type: jsonl
      path: /var/log/agent/audit.jsonl

policies:
  masking:
    fields:
      - inputs.password  # Mask sensitive data
    # But log enough to investigate
```

### Alerting

Set up alerts for security events:

```python
from agent_ethan2.telemetry import EventBus

class SecurityAlertExporter:
    def export(self, event: str, payload: dict) -> None:
        if event == "error.raised":
            if "PERMISSION_DENIED" in payload.get("message", ""):
                self.send_alert("Permission denied", payload)
        
        if event == "rate.limit.wait":
            if payload.get("wait_time", 0) > 5.0:
                self.send_alert("Excessive rate limiting", payload)
    
    def send_alert(self, message: str, payload: dict):
        # Send to monitoring service
        pass
```

### Revocation

Quickly revoke compromised credentials:

```python
# Emergency credential rotation
def rotate_credentials():
    # 1. Generate new credentials
    # 2. Update secret manager
    # 3. Restart services
    # 4. Revoke old credentials
    pass
```

---

## Security Checklist

### Development
- [ ] Never commit secrets to git
- [ ] Use environment variables for secrets
- [ ] Validate all user inputs
- [ ] Sanitize outputs
- [ ] Use parameterized queries
- [ ] Declare component permissions

### Configuration
- [ ] Enable data masking
- [ ] Configure permission policies
- [ ] Set rate limits
- [ ] Set cost limits
- [ ] Use least privilege principle

### Deployment
- [ ] Run as non-root user
- [ ] Use container isolation
- [ ] Enable audit logging
- [ ] Set up monitoring alerts
- [ ] Regular security updates
- [ ] Incident response plan

---

## Related Documentation

- [Policies](./policies.md) - Policy configuration
- [Custom Tools](./custom_tools.md) - Safe tool development
- [Custom Logic Nodes](./custom_logic_node.md) - Safe component development
- [Runtime Configuration](./runtime-config.md) - Factory security

