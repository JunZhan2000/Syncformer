#!/bin/bash

NUM_GPUS=8

export NOW=$(date +"%Y-%m-%dT%H-%M-%S")
export WANDB_MODE=offline

torchrun \
  --rdzv_backend=c10d \
  --rdzv_endpoint=localhost:29400 \
  --nproc_per_node=$NUM_GPUS \
    main.py \
    start_time="$NOW" \
    config="./configs/sync.yaml" \
    logging.use_wandb=True \
    training.patience=10

