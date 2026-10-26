# Validation Report

**Project:** VLAI LLM Serving  
**Validation date:** 26 October 2026  
**Code reviewed:** [`dc9dec5`](https://github.com/Datyth/VLAI-LLM-Serving/commit/dc9dec5d9875d0b5ec8a6db5efa042d8f7ddb202)  
**Evidence:** Team-provided terminal output and vLLM startup logs; current source and test files from GitHub. The reviewer did not remotely execute commands on the GPU server.

## 1. Summary

The initial GPU-hosted Qwen3.5-9B inference service is functional. Direct vLLM tests confirmed model discovery, normal chat, text streaming, automatic tool calling, a tool-result follow-up, and streaming tool calls. The FastAPI proxy is implemented and **3 local automated tests passed** using mock upstream responses.

This validates the basic development path. It is **not** a performance benchmark, a security review, or confirmation that OpenCode works end-to-end.

| ID | Test | Result | Evidence level |
| --- | --- | --- | --- |
| ENV-01 | Docker can access NVIDIA GPU | **PASS** | Team-reported container smoke test. |
| LLM-01 | vLLM model list | **PASS** | Direct `/v1/models` output. |
| LLM-02 | Normal completion | **PASS** | Factorial answer with `finish_reason: stop`. |
| LLM-03 | Text streaming | **PASS** | SSE `delta.content` chunks ending in `[DONE]`. |
| LLM-04 | Automatic tool selection | **PASS** | `add_numbers` with valid JSON arguments. |
| LLM-05 | Tool-result follow-up | **PASS** | Tool result `42` accepted and final answer returned. |
| LLM-06 | Streaming tool calls | **PASS** | Tool-call argument fragments assembled correctly. |
| API-01 | FastAPI unit/integration tests | **PASS** | 3 pytest tests, vLLM mocked. |
| API-02 | Ruff lint and formatting | **PASS** | Clean final command outputs. |
| API-03 | Real FastAPI model discovery and streamed tool calls | **NOT YET VERIFIED** | No complete live transcripts through port 8001 in the provided evidence. |
| CLIENT-01 | Real OpenCode session | **NOT YET VERIFIED** | Planned next stage. |

## 2. Environment and model configuration

| Field | Observed/configured value |
| --- | --- |
| Host OS | Ubuntu 24.04 (from earlier host checks) |
| GPU | NVIDIA RTX PRO 4000 Blackwell, approximately 24 GB VRAM |
| Driver | 595.84 (from earlier host checks) |
| Python environment | Conda, Python 3.12 |
| vLLM image | `vllm/vllm-openai:v0.32.0` |
| Model | `RedHatAI/Qwen3.5-9B-FP8-dynamic` |
| Served ID | `qwen3.5-9b` |
| Max model length | 4096 tokens |
| GPU memory utilization setting | 0.80 |
| Reasoning parser | `qwen3` |
| Auto tool choice / parser | Enabled, `qwen3_coder` |
| Host ports | vLLM `127.0.0.1:8000`, FastAPI `127.0.0.1:8001` |

The vLLM launch configuration is recorded in `scripts/run_vllm.sh`.

## 3. Direct inference validation

### LLM-01: Model discovery

```bash
curl -sS http://127.0.0.1:8000/v1/models
```

**Observed:** Successful model list with ID `qwen3.5-9b`, root checkpoint `RedHatAI/Qwen3.5-9B-FP8-dynamic`, and `max_model_len: 4096`.

**Result:** PASS. The model is registered and the API is reachable.

### LLM-02: Non-streaming completion

**Request:** `What is 5 factorial? Answer in one sentence.` with `max_tokens: 128` and `enable_thinking: false`.

**Observed:** The assistant answered `120`; `finish_reason: "stop"`; prompt tokens **23**, completion tokens **39**, total **62**, reasoning tokens **0**.

**Result:** PASS. A complete response was generated.

**Note:** An earlier 256-token code-generation request returned `finish_reason: "length"` and truncated Python code. That was a generation-limit condition, not a deployment failure.

### LLM-03: Text streaming

**Request:** A binary-search explanation with `"stream": true` using `curl -N`.

**Observed:** Multiple `chat.completion.chunk` events with incremental `delta.content`, followed by `data: [DONE]`. The final chunk had `finish_reason: "length"` because the output limit was reached.

**Result:** PASS for SSE delivery and clean stream termination. It did not prove the response content was complete.

### LLM-04: Automatic tool calling

**Request:** `Use the add_numbers tool to calculate 12 + 30.` with a JSON schema, `"tool_choice": "auto"`, and thinking disabled.

**Observed:** The model returned `content: null`, `finish_reason: "tool_calls"`, and:

```json
{
  "name": "add_numbers",
  "arguments": "{\"a\": 12, \"b\": 30}"
}
```

Prompt tokens **294**, completion tokens **38**.

**Result:** PASS. The model selected the tool and supplied valid arguments. **vLLM did not execute the function.**

### LLM-05: Tool-result round trip

**Request:** A manually constructed assistant tool-call message followed by a `role: "tool"` message with `tool_call_id: "call_001"` and content `42`.

**Observed:** Assistant replied `The result of 12 + 30 is **42**.` with `finish_reason: "stop"`. Prompt tokens **82**, completion tokens **16**.

**Result:** PASS for consuming a tool result and producing a final reply. Real client-side execution was not tested.

### LLM-06: Streaming tool call

**Request:** The same function with `"stream": true`.

**Observed:** An initial `delta.tool_calls` chunk carried `name: "add_numbers"`. Argument fragments arrived separately:

```text
{"a": 
12, "b": 
30}
```

Combined arguments: `{"a": 12, "b": 30}`. Final chunk had `finish_reason: "tool_calls"`, followed by `data: [DONE]`.

**Result:** PASS. The model emits structured tool calls over SSE. This is important for coding-agent clients.

## 4. GPU and inference observations

The startup logs reported:

| Metric | Observed value | Interpretation |
| --- | --- | --- |
| Model-loading footprint | **11.79 GiB** | Reported by vLLM for loading the checkpoint. |
| Available KV cache memory | **4.15 GiB** | KV-cache allocation reported at initialization. |
| KV cache capacity | **75,190 tokens** | Estimated token capacity under that configuration. |
| Maximum concurrency at 4096 tokens | **18.36x** | KV-cache-based estimate, **not** proven user throughput. |
| GPU memory utilization setting | **0.80** | Allocation target, **not** live GPU-Util %. |
| Observed average generation throughput | **25.6 and 17.5 tokens/s** | Window-averaged log samples under light testing. |
| Waiting requests | **0** | No queueing in the observed log windows. |

The logs also indicate FP8 kernels, FlashAttention/FlashInfer, prefix caching, and chunked prefill were active. No out-of-memory error was observed in the shared logs.

**Important:** These figures are not an SLA or a concurrency benchmark. Actual capacity requires repeatable load tests covering request length, time-to-first-token (TTFT), output tokens/second, P95 latency, throughput, and failure rate.

## 5. FastAPI and repository validation

### API-01: Automated tests

Command:

```bash
python -m pytest -q
```

**Observed:** `3 passed, 1 warning` in **0.17 seconds**. Tests cover FastAPI health, mocked normal chat forwarding, and mocked streaming tool-call content.

The warning was `StarletteDeprecationWarning` about the installed `httpx`/`starlette.testclient` combination. This was non-blocking in the observed run; review dependency compatibility when upgrading.

**Limitation:** The tests use `httpx.MockTransport`. They do not perform real GPU inference, benchmark streaming timing, test disconnect cleanup, or exercise model discovery through FastAPI.

### API-02: Linting and formatting

```bash
python -m ruff check .
python -m ruff format --check src tests
```

**Observed after fixes:** `All checks passed!` and `13 files already formatted`.

An earlier issue occurred because a Bash script had been saved as `.py`; this is now `scripts/run_vllm.sh` in GitHub. Earlier `B008` warnings were handled by the project's Ruff configuration (`ignore = ["B008"]`).

### API-03: FastAPI proxy source inspection

- `GET /health` is implemented.
- `GET /v1/models` uses `service.list_model()` and the service defines `list_model()`; **the names match**.
- `POST /v1/chat/completions` forwards JSON requests and SSE responses.
- HTTPX is created once per application lifespan, with a 120-second default timeout and a 10-second connect timeout.
- Upstream connection and timeout failures map to HTTP **502** and **504**, respectively.

The team also shared a streaming completion transcript while working on FastAPI integration, but the excerpt does not show its requested URL. It is therefore **not sufficient to certify a live port-8001 end-to-end streaming test**.

## 6. Known limitations and follow-up checks

| Priority | Item | Status |
| --- | --- | --- |
| High | Verify `GET /v1/models` through port 8001 | Pending live evidence. |
| High | Verify chat and streamed tool calls through port 8001 | Pending full live evidence. |
| High | Add authentication and HTTPS before remote access | Not implemented. |
| High | Test actual OpenCode connection and tool execution | Not tested. |
| Medium | Test 502/504 upstream failures and streaming cancellation | Not yet covered by tests. |
| Medium | Benchmark TTFT, TPOT, throughput, and concurrent requests | Not performed. |
| Medium | Pin Docker image digest and model revision | Not done. |
| Low | Update README to reflect implemented FastAPI/vLLM integration | README is outdated. |
| Low | Remove `docs/` from `.gitignore` | Required before committing documentation. |

## 7. How to update this report

When a new test passes, record its date, Git revision, exact command, relevant output, and whether it ran **directly against vLLM**, **through FastAPI**, or **with mocked dependencies**. Never mark a planned test as passed solely because the corresponding code exists.

See [api.md](api.md) for manual request examples and [deployment.md](deployment.md) for environment setup.
