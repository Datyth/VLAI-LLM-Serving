# VLAI LLM Serving

A lightweight, self-hosted LLM API for coding assistants.

The goal of this project is to serve an LLM from a GPU server so that users can access it through tools such as **OpenCode**, without running the model on their own computers.

> **Project status:** Early development. The FastAPI backend and health endpoint are implemented. Model inference, OpenCode integration, and production deployment are planned next.

## How it works

```text
OpenCode / API Client
        |
        v
  FastAPI Backend
        |
        v
   LLM Service
        |
        v
 vLLM + GPU Model
```

- **FastAPI** provides the application API and will handle authentication and request routing.
- **vLLM** will run the language model and generate responses.
- **OpenCode** will run on the user's computer and connect to the server through the API.

The backend and inference server are designed to run as separate services.

## Tech stack

| Component | Technology |
| --- | --- |
| Backend | Python 3.12, FastAPI |
| Environment | Conda |
| Inference (planned) | vLLM, Qwen3.5-9B |
| HTTP client | HTTPX |
| Testing | pytest, Ruff |
| Deployment (planned) | Docker |

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/Datyth/VLAI-LLM-Serving.git
cd VLAI-LLM-Serving
```

### 2. Set up the Conda environment

Make sure Conda is installed, then run:

```bash
conda env create -f environment.yml
conda activate vlai-llm
python -m pip install -e ".[dev]"
```

### 3. Start the API

```bash
python -m uvicorn llm_api.main:app --reload --host 127.0.0.1 --port 8001
```

Open **http://127.0.0.1:8001/docs** to explore the API documentation.

### 4. Check the health endpoint

```bash
curl http://127.0.0.1:8001/health
```

Expected response:

```json
{"status": "ok"}
```

This confirms that the **FastAPI application** is running. It does not yet check GPU or model readiness.

## Run tests

```bash
python -m pytest -q
python -m ruff check .
```

For code formatting:

```bash
python -m ruff format src tests
```

## Project structure

```text
VLAI-LLM-Serving/
├── src/llm_api/
│   ├── main.py                 # FastAPI entry point
│   ├── api/routes/health.py    # Health endpoint
│   ├── core/                   # Shared configuration (future)
│   └── services/llm/          # LLM integration (future)
├── tests/                      # Automated tests
├── environment.yml            # Conda environment
├── pyproject.toml             # Python dependencies and tools
├── GUIDE.md                   # Development commands
└── README.md
```

## Roadmap

- [x] Create project structure and FastAPI application
- [x] Add a health endpoint and an automated test
- [ ] Deploy the model with vLLM on the GPU server
- [ ] Connect FastAPI to vLLM (including streaming)
- [ ] Connect OpenCode and test tool calling
- [ ] Add API authentication, HTTPS, and rate limiting
- [ ] Benchmark latency, throughput, and concurrent requests
- [ ] Add monitoring and document deployment

## Notes

- The current API is for **local development**. Do not expose the development server directly to the public internet.
- The model and GPU are **not required** to run the existing health endpoint and tests.
- For the intended deployment, the inference server will be secured behind the application API and network controls.

## Repository

[Datyth/VLAI-LLM-Serving](https://github.com/Datyth/VLAI-LLM-Serving)