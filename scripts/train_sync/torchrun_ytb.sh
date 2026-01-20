#!/bin/bash

# ================= 配置区域 =================
# 设置使用的 GPU 数量 (例如 2 张卡)
NUM_GPUS=8


# 关闭 NCCL shared memory（最关键）
export NCCL_SHM_DISABLE=1
# 强烈建议：关闭 IB（容器里几乎都会出问题）
# export NCCL_IB_DISABLE=1
# 指定网卡（避免 NCCL 选到奇怪的 interface）
export NCCL_SOCKET_IFNAME=lo
# Debug（第一次建议开）
export NCCL_DEBUG=INFO

# 设置你的环境变量 (请根据本机实际路径修改这些变量)
# 原脚本中使用了这些变量，如果不设置会报错
CKPT_ROOT="/inspire/hdd/project/video-generation/public/jzhan/AnyTokenizer/ckpts/Syncformer/official"

export SCRATCH="output"
export CKPT_ROOT="/inspire/hdd/project/video-generation/public/jzhan/AnyTokenizer/ckpts/Syncformer/official"
export NOW=$(date +"%Y-%m-%dT%H-%M-%S")
export WANDB_MODE=offline


# ================= 运行命令 =================
# --standalone: 单机模式，自动处理 master_addr/port
# --nproc_per_node: 使用的 GPU 数量


torchrun \
  --rdzv_backend=c10d \
  --rdzv_endpoint=localhost:29400 \
  --nproc_per_node=$NUM_GPUS \
    main.py \
    start_time="$NOW" \
    config="./configs/sync.yaml" \
    logging.logdir="$SCRATCH/vladimir/logs/sync/sync_models/" \
    logging.use_wandb=True \
    model.params.vfeat_extractor.params.ckpt_path="${CKPT_ROOT}/vggsound/pretrain/epoch_best.pt" \
    model.params.afeat_extractor.params.ckpt_path="${CKPT_ROOT}/vggsound/pretrain/epoch_best.pt" \
    training.patience=10

