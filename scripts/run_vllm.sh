#!/bin/bash

sudo docker run --rm -it \
  --name vlai-vllm \
  --gpus all \
  --shm-size=4g \
  -p 127.0.0.1:8000:8000 \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
  vllm/vllm-openai:v0.32.0 \
  RedHatAI/Qwen3.5-9B-FP8-dynamic \
  --served-model-name qwen3.5-9b \
  --language-model-only \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.80 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder