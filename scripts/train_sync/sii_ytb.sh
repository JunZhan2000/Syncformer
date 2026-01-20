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
export NCCL_TIMEOUT=1800
export TORCH_NCCL_BLOCKING_WAIT=1

# 关闭 NCCL shared memory
# export NCCL_SHM_DISABLE=1
# 指定网卡（多机时建议使用实际网卡名，如 eth0, ib0 等，而不是 lo）
# export NCCL_SOCKET_IFNAME=eth0
# export NCCL_DEBUG=INFO
# export NCCL_ASYNC_ERROR_HANDLING=1
# export NCCL_DEBUG_SUBSYS=ALL
# export TORCH_DISTRIBUTED_DEBUG=DETAIL

# 如果集群支持 InfiniBand，注释掉下面这行；如果不支持或有问题，保留它
# export NCCL_IB_DISABLE=1

# ================= 训练配置 =================
CKPT_ROOT="/inspire/hdd/project/video-generation/public/jzhan/AnyTokenizer/ckpts/Syncformer/official"

export SCRATCH="output"
export NOW=$(date +"%Y-%m-%dT%H-%M-%S")
export WANDB_MODE=offline

# ================= 运行训练 =================
torchrun \
  --nnodes ${NNODES} \
  --nproc-per-node ${NPROC_PER_NODE} \
  --node_rank ${NODE_RANK} \
  --master_addr ${MASTER_ADDR} \
  --master_port ${MASTER_PORT} \
  main.py \
    start_time="$NOW" \
    config="./configs/sync.yaml" \
    logging.logdir="$SCRATCH/vladimir/logs/sync/sync_models/" \
    logging.use_wandb=True \
    model.params.vfeat_extractor.params.ckpt_path="${CKPT_ROOT}/vggsound/pretrain/epoch_best.pt" \
    model.params.afeat_extractor.params.ckpt_path="${CKPT_ROOT}/vggsound/pretrain/epoch_best.pt" \
    training.patience=10