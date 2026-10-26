# API Reference

**Project:** VLAI LLM Serving  
**Reference:** [`dc9dec5`](https://github.com/Datyth/VLAI-LLM-Serving/commit/dc9dec5d9875d0b5ec8a6db5efa042d8f7ddb202)  
**Status:** Local development API, without authentication.

## 1. Base URLs

| Service | URL | Intended use |
| --- | --- | --- |
| FastAPI | `http://127.0.0.1:8001` | Application entry point for clients. |
| vLLM | `http://127.0.0.1:8000` | Internal inference service and direct debugging. |

Use port **8001** when testing the FastAPI integration. `http://127.0.0.1:8001/docs` provides FastAPI's interactive schema documentation.

## 2. Available endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Checks whether the FastAPI application responds. |
| `GET` | `/v1/models` | Forwards vLLM's model list. |
| `POST` | `/v1/chat/completions` | Forwards OpenAI-style chat, including streaming and tool calls. |

The current FastAPI backend does **not** proxy `/v1/responses`, embeddings, or other vLLM endpoints.

### GET /health

```bash
curl -sS http://127.0.0.1:8001/health
```

Expected:

```json
{"status":"ok"}
```

This is a **liveness check**, not an inference-readiness check.

### GET /v1/models

```bash
curl -sS http://127.0.0.1:8001/v1/models | python -m json.tool
```

Expected model ID: `qwen3.5-9b`, when the configured vLLM container is available.

### POST /v1/chat/completions

```bash
curl -sS http://127.0.0.1:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3.5-9b",
    "messages": [{"role": "user", "content": "What is 5 factorial?"}],
    "max_tokens": 128,
    "chat_template_kwargs": {"enable_thinking": false}
  }' | python -m json.tool
```

A successful response contains `choices[0].message.content` and `choices[0].finish_reason`. The complete response structure comes from vLLM; FastAPI does not rewrite it.

## 3. Streaming

Add `"stream": true` and use `curl -N` to see SSE chunks as they arrive:

```bash
curl -N -sS http://127.0.0.1:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3.5-9b",
    "messages": [{"role": "user", "content": "Explain binary search briefly."}],
    "stream": true,
    "max_tokens": 256,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

Typical SSE output:

```text
data: {"choices":[{"delta":{"content":"Binary"},"finish_reason":null}],...}

data: {"choices":[{"delta":{"content":" search"},"finish_reason":null}],...}

data: [DONE]
```

Chunks can split words or JSON fields. Consumers must assemble them correctly. `finish_reason: "length"` means the output-token limit was reached; `[DONE]` means the stream ended, not necessarily that the answer was complete.

## 4. Tool calling

The model can return structured tool requests when the request supplies `tools` and `tool_choice`.

```bash
curl -sS http://127.0.0.1:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3.5-9b",
    "messages": [{"role": "user", "content": "Use add_numbers to add 12 and 30."}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "add_numbers",
        "description": "Add two integers",
        "parameters": {
          "type": "object",
          "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"}
          },
          "required": ["a", "b"]
        }
      }
    }],
    "tool_choice": "auto",
    "max_tokens": 256,
    "chat_template_kwargs": {"enable_thinking": false}
  }' | python -m json.tool
```

Expected important fields:

```json
{
  "message": {
    "tool_calls": [{
      "type": "function",
      "function": {"name": "add_numbers", "arguments": "{\"a\": 12, \"b\": 30}"}
    }]
  },
  "finish_reason": "tool_calls"
}
```

This is an **illustrative excerpt** of a larger response. The client executes the tool, then sends a follow-up `role: "tool"` message containing the result and the matching `tool_call_id`.

Streaming tool calls work the same way, except names and arguments arrive in separate `delta.tool_calls` fragments. Do not execute incomplete arguments.

## 5. Errors and limits

| Case | Current behavior |
| --- | --- |
| vLLM connection failure | HTTP 502 from FastAPI. |
| vLLM timeout | HTTP 504 from FastAPI. |
| Invalid FastAPI request-body shape | FastAPI validation error (typically HTTP 422). |
| vLLM returns an HTTP error | Status and response body forwarded. |
| Unsupported FastAPI route | HTTP 404. |

Current vLLM defaults in `scripts/run_vllm.sh`: served model `qwen3.5-9b`, maximum model length **4096 tokens**, and `--gpu-memory-utilization 0.80`. A large prompt plus requested completion can exceed the model context limit.

**Security note:** The FastAPI routes do not yet enforce an API key, per-user quota, or rate limit. Keep the service local until those controls and HTTPS are implemented.

## 6. Implementation references

- Route definitions: `src/llm_api/api/routes/openai.py`
- HTTP transport: `src/llm_api/services/llm/service.py`
- Environment settings: `src/llm_api/core/config.py`
- Validation evidence: [validation-report.md](validation-report.md)
