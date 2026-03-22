#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

EPOCHS=${EPOCHS:-20}
NUM_WORKERS=${NUM_WORKERS:-4}
VALIDATION_SPLIT=${VALIDATION_SPLIT:-0.1}
EXTRA_ARGS=${EXTRA_ARGS:-}
DEVICE_ARG=${DEVICE_ARG:-}

run() {
  local output_dir=$1
  shift

  echo "==> Running $output_dir"
  # shellcheck disable=SC2086
  uv run python -m cifar10_speedrun_agentic     --output-dir "$output_dir"     --epochs "$EPOCHS"     --num-workers "$NUM_WORKERS"     --validation-split "$VALIDATION_SPLIT"     $DEVICE_ARG     "$@"     $EXTRA_ARGS
}

run artifacts/baseline_run_001   --batch-size 128

run artifacts/lr_0p05_run_001   --batch-size 128   --learning-rate 0.05

run artifacts/lr_0p2_run_001   --batch-size 128   --learning-rate 0.2

run artifacts/bs_64_run_001   --batch-size 64

run artifacts/bs_256_run_001   --batch-size 256

run artifacts/label_smoothing_0p1_run_001   --batch-size 128   --label-smoothing 0.1

run artifacts/resnext50_32x4d_run_001   --batch-size 128   --model-name resnext50_32x4d

run artifacts/adamw_run_001   --batch-size 128   --optimizer-name adamw

run artifacts/muon_run_001   --batch-size 128   --optimizer-name muon
