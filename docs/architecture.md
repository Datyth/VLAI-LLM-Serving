# System Architecture

**Project:** VLAI LLM Serving  
**Reference:** [`dc9dec5`](https://github.com/Datyth/VLAI-LLM-Serving/commit/dc9dec5d9875d0b5ec8a6db5efa042d8f7ddb202) (26 October 2026)  
**Status:** Local development implementation. Not yet ready for public access.

## 1. Purpose

VLAI LLM Serving provides an OpenAI-compatible API for coding assistants. A shared GPU server runs the language model, so client computers do not need to host it.

The system currently has **two services**:

```text
OpenCode or HTTP client
        |
        | HTTP (JSON or Server-Sent Events)
        v
 FastAPI backend :8001
        |  API routes + HTTPX client
        | HTTP (JSON or Server-Sent Events)
        v
    vLLM server :8000
        |
        v
 NVIDIA GPU + Qwen3.5-9B FP8
```

Both ports are bound to `127.0.0.1` during local development.

## 2. Components

| Component | File or runtime | Responsibility |
| --- | --- | --- |
| FastAPI entry point | `src/llm_api/main.py` | Starts the API and manages the shared HTTPX client lifecycle. |
| API routes | `src/llm_api/api/routes/` | Implements `/health`, `/v1/models`, and `/v1/chat/completions`. |
| LLM service | `src/llm_api/services/llm/service.py` | Forwards requests to vLLM and handles upstream connection/timeout errors. |
| Configuration | `src/llm_api/core/config.py` | Loads vLLM URL, model name, and timeout from environment variables. |
| Inference service | `scripts/run_vllm.sh` | Starts a separate Docker container running vLLM and Qwen3.5-9B FP8. |
| Coding client | OpenCode (planned) | Sends prompts, assembles streamed tool calls, and executes local tools. |

The GPU and model are managed by vLLM. **FastAPI does not load model weights and does not execute coding tools.**

## 3. Request flows

### Normal chat

1. The client posts JSON to `POST /v1/chat/completions` on FastAPI.
2. FastAPI passes the request body to `LLMService`.
3. HTTPX sends it to vLLM's same endpoint.
4. vLLM generates a response. FastAPI forwards the response body and HTTP status.

### Streaming chat and tool calls

1. The client sends the same request with `"stream": true`.
2. vLLM returns Server-Sent Events (SSE).
3. FastAPI relays chunks using `StreamingResponse`, without rebuilding the tool-call JSON.
4. The client assembles `delta.content` or `delta.tool_calls`, then waits for the complete tool call before executing anything.
5. The client sends any tool result back in a new chat request.

**Tool execution stays on the client.** A tool-call response is an instruction proposal, not an executed action.

## 4. Error handling

- If vLLM is unreachable, FastAPI returns **502** (`Inference server unavailable`).
- If communication with vLLM times out, FastAPI returns **504** (`Inference server timed out`).
- Other upstream HTTP statuses and response bodies are forwarded by the current proxy.
- `/health` checks FastAPI only. It does **not** prove vLLM or the GPU is ready.

## 5. Current boundaries

**Implemented:** FastAPI-to-vLLM proxy, JSON responses, SSE response forwarding, local configuration, and automated tests with mocked vLLM responses.

**Not implemented yet:** API-key authentication, HTTPS, rate limiting, quotas, Docker Compose deployment, persistent operations, and verified OpenCode integration. The backend currently exposes only the three routes described above, not every endpoint supported by the underlying vLLM server.

For now, **do not expose ports 8000 or 8001 to the public internet**. The intended production path is authenticated clients through a secure gateway to FastAPI, with vLLM reachable only on an internal network.

## 6. Where to look next

- [API reference](api.md)
- [Deployment guide](deployment.md)
- [Validation report](validation-report.md)
