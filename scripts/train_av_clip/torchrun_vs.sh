#!/bin/bash

NUM_GPUS=$1
echo $NUM_GPUS

export NOW=$(date +"%Y-%m-%dT%H-%M-%S")
export WANDB_MODE=offline

torchrun \
  --rdzv_backend=c10d \
  --rdzv_endpoint=localhost:29400 \
  --nproc_per_node=$NUM_GPUS \
    main.py \
    start_time="$NOW" \
    config="./configs/segment_avclip.yaml" \
    logging.use_wandb=True \
    training.patience=10

