# Local Deployment Guide

**Project:** VLAI LLM Serving  
**Reference:** [`dc9dec5`](https://github.com/Datyth/VLAI-LLM-Serving/commit/dc9dec5d9875d0b5ec8a6db5efa042d8f7ddb202)  
**Status:** Tested development setup on one NVIDIA GPU. Not a production deployment.

## 1. Current environment

The initial tests were performed on an Ubuntu 24.04 workstation with an **NVIDIA RTX PRO 4000 Blackwell (about 24 GB VRAM)**, NVIDIA driver **595.84**, Docker with NVIDIA GPU access, and Python **3.12** in Conda.

| Item | Configuration |
| --- | --- |
| vLLM image | `vllm/vllm-openai:v0.32.0` |
| Model checkpoint | `RedHatAI/Qwen3.5-9B-FP8-dynamic` |
| API model name | `qwen3.5-9b` |
| Context limit | 4096 tokens |
| GPU memory target | 0.80 |
| Reasoning parser | `qwen3` |
| Tool-call parser | `qwen3_coder` |
| vLLM host port | `127.0.0.1:8000` |
| FastAPI host port | `127.0.0.1:8001` |

The model revision is **not pinned** in the script and the Docker image uses a tag rather than an immutable digest. Pin both before relying on the deployment for reproducible production rollouts.

## 2. Prerequisites

Install and verify:

- NVIDIA GPU driver (`nvidia-smi` should work on the host).
- Docker Engine and NVIDIA Container Toolkit (follow their official Ubuntu installation instructions).
- Conda or Miniconda.
- Git and sufficient disk space for the model checkpoint and Docker images.

Confirm GPU access inside Docker:

```bash
sudo docker run --rm --gpus all \
  nvidia/cuda:13.2.0-base-ubuntu24.04 nvidia-smi
```

The CUDA image tag is the one used for the initial GPU smoke test. On another machine, choose a compatible image and NVIDIA driver.

## 3. Get the source and Python environment

```bash
git clone https://github.com/Datyth/VLAI-LLM-Serving.git
cd VLAI-LLM-Serving

conda env create -f environment.yml
conda activate vlai-llm
python -m pip install -e '.[dev]'

cp .env.example .env
```

The development `.env` should contain:

```dotenv
VLLM_BASE_URL=http://127.0.0.1:8000
VLLM_MODEL=qwen3.5-9b
VLLM_TIMEOUT_SECONDS=120
```

Do not commit `.env`, tokens, SSH keys, or model weights.

## 4. Start vLLM (terminal A)

```bash
bash scripts/run_vllm.sh
```

The script starts vLLM in the foreground with `--rm -it`, maps the GPU, and mounts the host Hugging Face cache:

```text
$HOME/.cache/huggingface  ->  /root/.cache/huggingface
```

The cache persists after the container stops, so restarting normally does **not** require downloading all model weights again.

Wait until the server reports startup completion, then check:

```bash
curl -sS http://127.0.0.1:8000/v1/models | python -m json.tool
```

Expected model ID: `qwen3.5-9b`.

To stop the named container from another terminal:

```bash
sudo docker stop vlai-vllm
```

If a container with that name is still running, stop it before launching another instance.

## 5. Start FastAPI (terminal B)

Activate the Conda environment in a separate shell:

```bash
conda activate vlai-llm
python -m uvicorn llm_api.main:app \
  --host 127.0.0.1 --port 8001 --reload
```

`--reload` is for development only.

Verify the application:

```bash
curl -sS http://127.0.0.1:8001/health
curl -sS http://127.0.0.1:8001/v1/models | python -m json.tool
```

For a minimal inference test through FastAPI:

```bash
curl -sS http://127.0.0.1:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3.5-9b","messages":[{"role":"user","content":"What is 5 factorial?"}],"max_tokens":128,"chat_template_kwargs":{"enable_thinking":false}}' \
  | python -m json.tool
```

Expected answer: 120. See [api.md](api.md) for streaming and tool-calling examples.

## 6. Check resources and run tests

```bash
# Live GPU memory/utilization
watch -n 1 nvidia-smi

# Docker CPU/host-memory use
sudo docker stats vlai-vllm

# vLLM operational metrics
curl -sS http://127.0.0.1:8000/metrics | head -n 20

# Backend tests and linting
python -m pytest -q
python -m ruff check .
python -m ruff format --check src tests
```

The observed local test run passed **3 pytest tests**, with one non-blocking Starlette deprecation warning. The tests mock vLLM, so they do not replace a live inference check.

## 7. Troubleshooting

| Symptom | Check |
| --- | --- |
| `docker: command not found` | Install Docker Engine. |
| Docker cannot see GPU | Check `nvidia-smi`, NVIDIA Container Toolkit, Docker runtime setup. |
| Port 8000 already allocated / container name conflict | Inspect `sudo docker ps`, stop the previous `vlai-vllm` container. |
| FastAPI returns 502 | Check that vLLM is running and `VLLM_BASE_URL` matches. |
| FastAPI returns 504 | Check vLLM logs, request length, GPU load, and timeout configuration. |
| Request ends with `finish_reason: length` | Increase `max_tokens` if the 4096-token context budget permits. |
| Model downloads again | Verify the Hugging Face cache bind mount and the host user running Docker. |

## 8. Security and production TODO

**Do not expose the current service to the internet.** Both ports are local-only, and FastAPI has no API-key verification, HTTPS, or request limits.

Before team-wide access, add authentication, HTTPS at a gateway, access controls, rate limits, monitoring, and a managed restart policy. Docker Compose and OpenCode end-to-end integration are planned, not yet part of this deployment.

For a new server, follow [migration.md](migration.md).
