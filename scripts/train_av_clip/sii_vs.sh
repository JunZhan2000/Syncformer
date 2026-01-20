#!/bin/bash

# ================= 环境初始化 =================
source /inspire/hdd/project/video-generation/public/jzhan/env/.bashrc
which python
conda activate synchformer2  # 根据实际环境名修改
which python

cd /inspire/hdd/project/video-generation/public/jzhan/AnyTokenizer/Synchformer  # 根据实际路径修改

# ================= 分布式环境变量映射 =================
export MASTER_ADDR=${PET_MASTER_ADDR}
export MASTER_PORT=${PET_MASTER_PORT}

NNODES=${PET_NNODES}
NPROC_PER_NODE=${PET_NPROC_PER_NODE}
NODE_RANK=${PET_NODE_RANK}

WORLD_SIZE=$((NNODES * NPROC_PER_NODE))

echo "==== Distributed config ===="
echo "NNODES: ${NNODES}"
echo "NPROC_PER_NODE: ${NPROC_PER_NODE}"
echo "NODE_RANK: ${NODE_RANK}"
echo "MASTER_ADDR: ${MASTER_ADDR}"
echo "MASTER_PORT: ${MASTER_PORT}"
echo "WORLD_SIZE: ${WORLD_SIZE}"

# ================= NCCL 配置 =================
export NCCL_IB_TIMEOUT=30
# export NCCL_TIMEOUT=1800
export NCCL_TIMEOUT=120
export TORCH_NCCL_BLOCKING_WAIT=1
export NCCL_IB_DISABLE=1


export NOW=$(date +"%Y-%m-%dT%H-%M-%S")
export WANDB_MODE=offline

torchrun \
  --nnodes ${NNODES} \
  --nproc-per-node ${NPROC_PER_NODE} \
  --node_rank ${NODE_RANK} \
  --master_addr ${MASTER_ADDR} \
  --master_port ${MASTER_PORT} \
  main.py \
    start_time="$NOW" \
    config="./configs/segment_avclip.yaml" \
    logging.use_wandb=True \
    training.patience=10

