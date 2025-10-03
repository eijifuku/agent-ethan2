# Error Code Reference

This document lists the main error codes used in AgentEthan2 validation and execution, organized by module. Code definitions can be found in repository comments and exception messages.

## YAML Loader (`agent_ethan2/loader/yaml_loader.py`)

| Code | Description |
| ---- | ----------- |
| `ERR_YAML_PARSE` | YAML syntax parsing failed |
| `ERR_YAML_EMPTY` | Document is empty |
| `ERR_ROOT_NOT_MAPPING` | Root element is not a mapping |
| `ERR_YAML_DUPLICATE_KEY` | Duplicate keys at the same level |
| `ERR_YAML_COMPLEX_KEY` | Complex keys are used |
| `ERR_YAML_SCALAR` | Unsupported scalar type encountered |
| `ERR_YAML_NODE_UNSUPPORTED` | Unsupported YAML node type |
| `ERR_META_VERSION_UNSUPPORTED` | `meta.version` is not v2 |
| `ERR_RUNTIME_ENGINE_UNSUPPORTED` | `runtime.engine` is unsupported |
| `ERR_PROVIDER_DUP` / `ERR_TOOL_DUP` / `ERR_COMPONENT_DUP` / `ERR_NODE_DUP` | ID duplication |
| `ERR_OUTPUT_KEY_COLLISION` | Duplicate keys in `graph.outputs` |
| `ERR_SCHEMA_VALIDATION` | JSON Schema validation error |

## IR Normalizer (`agent_ethan2/ir/model.py`)

### General
| Code | Description |
| ---- | ----------- |
| `ERR_IR_INPUT_TYPE` | Normalization target is not a mapping |
| `ERR_META_TYPE` | `meta` is not a mapping |
| `ERR_RUNTIME_TYPE` | `runtime` is not a mapping |
| `ERR_RUNTIME_ENGINE` | `runtime.engine` is not a string |
| `ERR_RUNTIME_DEFAULT_PROVIDER` | `defaults.provider` references undefined provider |

### Providers / Tools
| Code | Description |
| ---- | ----------- |
| `ERR_PROVIDERS_TYPE` | `providers` is not an array |
| `ERR_PROVIDER_ID` / `ERR_PROVIDER_TYPE` / `ERR_PROVIDER_TYPE_FIELD` | Required fields in provider definition are invalid |
| `ERR_TOOLS_TYPE` | `tools` is not an array |
| `ERR_TOOL_ID` / `ERR_TOOL_TYPE` / `ERR_TOOL_TYPE_FIELD` | Required fields in tool definition are invalid |
| `ERR_TOOL_PROVIDER_NOT_FOUND` | Tool references non-existent provider |

### Components
| Code | Description |
| ---- | ----------- |
| `ERR_COMPONENTS_TYPE` | `components` is not an array |
| `ERR_COMPONENT_ID` / `ERR_COMPONENT_TYPE` / `ERR_COMPONENT_TYPE_FIELD` | Required fields in component definition are invalid |
| `ERR_COMPONENT_PROVIDER_NOT_FOUND` | Component references undefined provider |
| `ERR_COMPONENT_TOOL_NOT_FOUND` | Component references undefined tool |
| `ERR_NODE_COMPONENT_NOT_FOUND` | Node references non-existent component |

### Graph / Outputs
| Code | Description |
| ---- | ----------- |
| `ERR_GRAPH_TYPE` | `graph` is not a mapping |
| `ERR_GRAPH_ENTRY_NOT_FOUND` | `graph.entry` does not match any node |
| `ERR_GRAPH_NODES` / `ERR_GRAPH_NODE_TYPE` | Node definition is not an array or structure is invalid |
| `ERR_GRAPH_OUTPUTS_TYPE` | `graph.outputs` is not an array |
| `ERR_GRAPH_OUTPUT_KEY` / `ERR_GRAPH_OUTPUT_NAME` / `ERR_GRAPH_OUTPUT_NODE` / `ERR_GRAPH_OUTPUT_TYPE` | Required fields in output mapping are invalid |
| `ERR_EDGE_ENDPOINT_INVALID` | Node transition destination/output is undefined |

### Conversation History / Policies
| Code | Description |
| ---- | ----------- |
| `ERR_HISTORY_TYPE` / `ERR_HISTORY_ID` / `ERR_HISTORY_BACKEND_TYPE` | `histories` section structure is invalid |
| `ERR_HISTORY_DUPLICATE` | History ID duplication |
| `ERR_POLICIES_TYPE` | `policies` is not a mapping |

## Graph Builder (`agent_ethan2/graph/builder.py`)

| Code | Description |
| ---- | ----------- |
| `ERR_GRAPH_ENTRY_NOT_FOUND` | Entry node does not exist |
| `ERR_COMPONENT_IMPORT` | Component factory is not materialized |
| `ERR_NODE_TYPE` | Unsupported node type (or required config is missing) |
| `ERR_PROVIDER_DEFAULT_MISSING` | Provider for LLM/tool node cannot be resolved |
| `ERR_TOOL_NOT_FOUND` | Tool node is not materialized |
| `ERR_ROUTER_NO_MATCH` | Router node has no defined routes |
| `ERR_MAP_BODY_NOT_FOUND` | Map node has no component configured |

## Runtime Scheduler (`agent_ethan2/runtime/scheduler.py`)

| Code | Description |
| ---- | ----------- |
| `ERR_NODE_RUNTIME` | Exception occurred during component execution |
| `ERR_EDGE_ENDPOINT_INVALID` | Attempted to transition to undefined node during execution |
| `ERR_ROUTER_NO_MATCH` | Router node does not return a route |
| `ERR_MAP_BODY_NOT_FOUND` / `ERR_MAP_OVER_NOT_ARRAY` | Map node configuration is invalid |
| `ERR_PARALLEL_EMPTY` | Parallel node branches are empty |
| `ERR_NODE_TYPE` | Encountered unsupported node at runtime |

## Registry (`agent_ethan2/registry/resolver.py`)

| Code | Description |
| ---- | ----------- |
| `ERR_COMPONENT_IMPORT` | Component factory import failed |
| `ERR_COMPONENT_SIGNATURE` | Component call signature is not `(state, inputs, ctx)` |
| `ERR_TOOL_IMPORT` | Tool factory import failed |
| `ERR_TOOL_PERM_TYPE` | Tool's `permissions` attribute is not a sequence |

## Policies / Cost Management

| Code | Description |
| ---- | ----------- |
| `ERR_RETRY_PREDICATE` (`policy/retry.py`) | Retry configuration is invalid |
| `ERR_RL_POLICY_PARAM` (`policy/ratelimit.py`) | Rate limit configuration is invalid |
| `ERR_TOOL_PERMISSION_DENIED` (`policy/permissions.py`) | Permission not allowed by policy is requested |
| `ERR_COST_LIMIT_EXCEEDED` (`policy/cost.py`) | Token limit exceeded for LLM calls |

## Other

| Code | Description |
| ---- | ----------- |
| `ERR_LLM_JSON_PARSE` (`validation/strict_json.py`) | Failed to parse JSON from LLM output |

> **Note:** The implementation may include codes not listed here that are for testing or internal use. Refer to the exception class definitions in each module for the latest information.

