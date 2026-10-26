# Migration Guide

**Project:** VLAI LLM Serving  
**Reference:** [`dc9dec5`](https://github.com/Datyth/VLAI-LLM-Serving/commit/dc9dec5d9875d0b5ec8a6db5efa042d8f7ddb202)  
**Scope:** Move the current single-GPU development deployment to another server.

## 1. What needs to move?

| Item | Where it lives | Action |
| --- | --- | --- |
| Application and startup script | GitHub repository | Clone the same Git revision. |
| Python dependencies | `environment.yml`, `pyproject.toml` | Recreate the Conda environment. |
| vLLM runtime | Docker image | Pull the same image tag or pinned digest. |
| Model weights | Host Hugging Face cache | Re-download or copy the cache if appropriate. |
| Local settings | `.env` (not committed) | Recreate securely on the new host. |
| Runtime logs and measurements | Local terminal/monitoring | Save any required evidence separately. |

**No model weights are stored in Git, and Docker containers are not the source of truth for deployment configuration.**

## 2. Record the old server configuration

On the old server, save these values in an internal migration note:

```bash
git rev-parse HEAD
nvidia-smi
sudo docker ps
sudo docker image inspect vllm/vllm-openai:v0.32.0 \
  --format '{{index .RepoDigests 0}}'
sudo docker inspect vlai-vllm \
  --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

Also record the actual startup command, model ID, context limit, GPU memory target, and whether the model checkpoint has been pinned to a specific revision. The current script references the model repository without a fixed revision, so exact model reproducibility is not yet guaranteed.

Keep secrets out of these notes. **Never copy `.env` into GitHub.**

## 3. Prepare the new host

1. Install a compatible NVIDIA driver and confirm `nvidia-smi` works.
2. Install Docker Engine and NVIDIA Container Toolkit.
3. Verify Docker can see the GPU:

   ```bash
   sudo docker run --rm --gpus all \
     nvidia/cuda:13.2.0-base-ubuntu24.04 nvidia-smi
   ```

4. Install Conda, Git, and enough disk space for the model.
5. Clone the project and check out the intended Git revision:

   ```bash
   git clone https://github.com/Datyth/VLAI-LLM-Serving.git
   cd VLAI-LLM-Serving
   git checkout <recorded-commit-sha>
   conda env create -f environment.yml
   conda activate vlai-llm
   python -m pip install -e '.[dev]'
   cp .env.example .env
   ```

Edit `.env` only if the new host uses different endpoints. For same-host local development, use `VLLM_BASE_URL=http://127.0.0.1:8000`.

## 4. Restore the inference service

The easiest path is to let Hugging Face download model weights again:

```bash
bash scripts/run_vllm.sh
```

If transferring a cached model instead, copy the host Hugging Face cache into the **same intended host cache directory**, with correct ownership and permissions. Do not copy `/root/.cache/huggingface` from inside the temporary container unless you have confirmed that is where files actually reside. The script binds `$HOME/.cache/huggingface` on the host to that container path.

If an HF access token is required, supply it as a secret through the runtime environment, never in the repository.

## 5. Validate before switching users

Keep the old server available while testing the new one.

```bash
# Direct inference service
curl -sS http://127.0.0.1:8000/v1/models | python -m json.tool

# FastAPI backend (start it in a second terminal first)
python -m uvicorn llm_api.main:app \
  --host 127.0.0.1 --port 8001 --reload
```

Then, in another terminal:

```bash
curl -sS http://127.0.0.1:8001/health
curl -sS http://127.0.0.1:8001/v1/models | python -m json.tool
python -m pytest -q
python -m ruff check .
```

Also repeat the three manual checks in [api.md](api.md): normal chat, streaming text, and a streamed tool call. Confirm the generated JSON arguments can be assembled. Watch `nvidia-smi` for GPU memory and errors.

The current `/health` endpoint only checks FastAPI, so **do not use it as the only readiness check**.

## 6. Cutover and rollback

**Cutover** (once networking and security are implemented): route new client traffic to the tested new server, verify responses and latency, then retire the old server only after confidence is established.

**Rollback:** restore the previous API destination to the old server. Keep its configuration, model cache, and running service available until migration is complete.

For today's localhost-only deployment, there is **no remote traffic cutover procedure** yet. Do not expose the new server directly on a public IP just to test migration.

## 7. Migration checklist

- [ ] Record Git revision, Docker image digest, model revision, launch settings.
- [ ] Confirm GPU access on the destination host.
- [ ] Clone source, recreate Conda environment and local `.env`.
- [ ] Restore/download model and start vLLM.
- [ ] Verify direct model discovery and generated chat response.
- [ ] Verify FastAPI model list, streaming, and tool-call handling.
- [ ] Run automated tests and inspect GPU metrics.
- [ ] Keep a tested rollback path until the replacement is stable.
