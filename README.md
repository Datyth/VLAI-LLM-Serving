# VLAI LLM Serving

A lightweight, self-hosted LLM API for coding assistants. A shared NVIDIA GPU server runs the model, while clients such as **OpenCode** can use it without hosting model weights locally.

> **Status (26 October 2026):** Local development. Qwen3.5-9B inference, text streaming, and tool calling have been verified directly with vLLM. The FastAPI proxy is implemented and its mocked tests pass. Live end-to-end FastAPI verification and OpenCode integration are still pending. **Not ready for public access.**

## Architecture

```text
Coding client (OpenCode planned)
            |
            | OpenAI-style HTTP / SSE
            v
      FastAPI :8001
            |
            | HTTPX (JSON / SSE)
            v
        vLLM :8000
            |
            v
     Qwen3.5-9B FP8
       NVIDIA GPU
```

- **FastAPI** exposes `/health`, `/v1/models`, and `/v1/chat/completions` and forwards inference requests to vLLM.
- **vLLM** loads the model and handles inference, streaming, and tool-call generation.
- **OpenCode (planned)** runs on client machines and executes its own coding tools. The server does **not** execute shell commands or modify client files.

See [System Architecture](docs/architecture.md) for component boundaries and request flows.

## Tech stack

| Component | Current choice |
| --- | --- |
| Backend | Python 3.12, FastAPI, HTTPX |
| Python environment | Conda |
| Inference engine | vLLM `v0.32.0` (Docker) |
| Model | `RedHatAI/Qwen3.5-9B-FP8-dynamic` |
| Served model ID | `qwen3.5-9b` |
| Inference configuration | 4,096-token context, 80% GPU memory target |
| Tests and code quality | pytest, Ruff |

## Quick start (local development)

**Prerequisites:** Git, Conda, Docker with NVIDIA Container Toolkit, a compatible NVIDIA GPU/driver, and free disk space for the model. GPU inference requires a working Docker GPU runtime.

### 1. Clone and set up Python

```bash
git clone https://github.com/Datyth/VLAI-LLM-Serving.git
cd VLAI-LLM-Serving

conda env create -f environment.yml
conda activate vlai-llm
python -m pip install -e '.[dev]'
cp .env.example .env
```

Local settings in `.env.example`:

```dotenv
VLLM_BASE_URL=http://127.0.0.1:8000
VLLM_MODEL=qwen3.5-9b
VLLM_TIMEOUT_SECONDS=120
```

### 2. Start vLLM (terminal A)

```bash
bash scripts/run_vllm.sh
```

The script starts vLLM in a Docker container on `127.0.0.1:8000`, enables automatic tool calling, and stores downloaded model files in the host Hugging Face cache. Initial model loading can take some time.

Check the inference server:

```bash
curl -sS http://127.0.0.1:8000/v1/models | python -m json.tool
```

### 3. Start FastAPI (terminal B)

```bash
conda activate vlai-llm
python -m uvicorn llm_api.main:app --host 127.0.0.1 --port 8001 --reload
```

Check the application:

```bash
curl -sS http://127.0.0.1:8001/health
curl -sS http://127.0.0.1:8001/v1/models | python -m json.tool
```

`/health` returns `{"status":"ok"}` when FastAPI is running. It does **not** verify that vLLM or the GPU is ready. Swagger UI is available at <http://127.0.0.1:8001/docs>.

### 4. Test chat through FastAPI

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

Expected answer: `120`. For `"stream": true`, SSE, and tool-calling examples, see the [API Reference](docs/api.md).

## Tests and code quality

These automated tests use a **mock vLLM server**, so they run without a GPU:

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check src tests
```

The latest team-shared results were **3 passing tests** and clean Ruff checks. See the [Validation Report](docs/validation-report.md) for what has and has not been verified.

## Repository layout

```text
.
├── docs/                     # Team documentation
├── scripts/run_vllm.sh       # Manual vLLM Docker startup
├── src/llm_api/
│   ├── main.py               # FastAPI app and HTTPX lifecycle
│   ├── api/routes/           # Health and OpenAI-style endpoints
│   ├── core/config.py        # Environment configuration
│   └── services/llm/         # Async vLLM HTTP client
├── tests/                    # FastAPI and proxy tests
├── .env.example              # Local config template
├── environment.yml          # Conda environment
└── pyproject.toml            # Python dependencies / tooling
```

## Current progress

- [x] GPU access through Docker and Qwen3.5-9B FP8 deployment
- [x] Direct vLLM chat generation, text streaming, tool calling, and tool-result follow-up
- [x] FastAPI proxy for model listing and chat completions (JSON and SSE)
- [x] Mocked FastAPI tests and Ruff checks
- [ ] Complete live tests of FastAPI endpoints and streamed tool calls on port 8001
- [ ] Connect OpenCode and verify an actual coding-agent workflow
- [ ] Add API authentication, HTTPS, rate limiting, and quotas
- [ ] Add managed deployment, observability, and repeatable performance benchmarks

## Team documentation

| Document | Purpose |
| --- | --- |
| [Architecture](docs/architecture.md) | Components, request flow, and responsibilities |
| [API Reference](docs/api.md) | Endpoints, chat, streaming, tool calling, and errors |
| [Deployment Guide](docs/deployment.md) | Setup and local server operations |
| [Migration Guide](docs/migration.md) | Moving the system to a different GPU server |
| [Validation Report](docs/validation-report.md) | Test evidence, GPU observations, and open checks |

## Security note

This is a **localhost-only development setup**. The FastAPI proxy has no authentication, authorization, rate limiting, or HTTPS termination yet. Do not expose ports `8000` or `8001` to the public internet. Keep `.env`, credentials, and model artifacts out of Git.
