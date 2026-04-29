#!/bin/bash
set -e

MODEL_DIR="/app/model"
ONNX_FILE="$MODEL_DIR/maildefender.onnx"

if [ ! -f "$ONNX_FILE" ]; then
    echo "[entrypoint] Model not found — downloading from Hugging Face Hub..."

    if [ -z "$HF_MODEL_REPO" ]; then
        echo "[entrypoint] ERROR: HF_MODEL_REPO env var not set."
        exit 1
    fi

    python3 - <<EOF
from huggingface_hub import snapshot_download
import os

snapshot_download(
    repo_id=os.environ["HF_MODEL_REPO"],
    local_dir="/app/model",
    repo_type="model",
    token=os.environ.get("HF_TOKEN"),
    ignore_patterns=[
        "checkpoint-*",
        "*.safetensors",
        "training_args.bin",
        "optimizer.pt",
        "rng_state.pth",
        "scaler.pt",
        "scheduler.pt",
        "trainer_state.json",
    ],
)
print("[entrypoint] Model downloaded successfully.")
EOF

else
    echo "[entrypoint] Model found — skipping download."
fi

exec uvicorn api.main:app --host 0.0.0.0 --port 8001
