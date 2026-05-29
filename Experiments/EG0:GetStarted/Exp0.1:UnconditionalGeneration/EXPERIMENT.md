# Exp0.1 — 无条件生成：端到端全管线

## 目标

跑通完整管线 `RFdiffusion → ProteinMPNN → ESMFold → 筛选`，生成 100 个 de novo 蛋白质，并建立基本的实验流程和输出管理习惯。

## 背景

这是最简单的全管线实验。所有步骤在 "无条件" 模式下运行——只指定长度，不给任何结构约束。目标是：

1. 验证管线能从头跑到尾（不做筛选的上游步骤如果出问题，下游更复杂实验也会出问题）
2. 积累一批输出数据，供 Exp0.2（质量指标）和 Exp0.3（工具对比）使用

## 管线步骤

```
Step 1                Step 2               Step 3               Step 4
RFdiffusion  ──→  ProteinMPNN  ──→  ESMFold          ──→  质量筛选
 100 backbone      100×8 seqs          800 预测             56 backbones 通过
 (50-200aa)         (采样)             (自洽性验证)           (pLDDT+Rg阈值)
```

### Step 1: 生成 Backbone（RFdiffusion）

```bash
conda activate protein_design
cd /root/autodl-tmp/tools/rfdiffusion
EXP_DIR=/root/autodl-tmp/Experiments/EG0:GetStarted/Exp0.1:UnconditionalGeneration
mkdir -p $EXP_DIR/outputs
python scripts/run_inference.py \
    'contigmap.contigs=[50-200]' \
    inference.output_prefix=$EXP_DIR/outputs/rfdiffusion/ \
    inference.num_designs=100 \
    inference.write_trajectory=false \
    inference.deterministic=false
```

关键参数：

- `[50-200]` — 长度在 50 到 200 之间均匀采样
- `num_designs=100` — 生成 100 个独立的 backbone
- `write_trajectory=false` — 不保存扩散过程（省磁盘）

### Step 2: 序列设计（ProteinMPNN）

对每个 backbone 生成 8 条序列采样（推荐温度 0.1）：

```bash
conda activate protein_design
cd /root/autodl-tmp/tools/proteinmpnn
EXP_DIR=/root/autodl-tmp/Experiments/EG0:GetStarted/Exp0.1:UnconditionalGeneration

for i in $(seq 0 99); do
    python protein_mpnn_run.py \
        --pdb_path $EXP_DIR/outputs/rfdiffusion/_${i}.pdb \
        --out_folder $EXP_DIR/outputs/proteinmpnn/design_${i}/ \
        --num_seq_per_target 8 \
        --sampling_temp 0.1 \
        --seed $((42 + i))
done
```

### Step 3: 结构验证（ESMFold）

对 100×8 = 800 条序列逐一折叠验证：

```bash
conda activate protein_design
EXP_DIR=/root/autodl-tmp/Experiments/EG0:GetStarted/Exp0.1:UnconditionalGeneration
python fold_all.py \          # ← 需要自己写这个脚本
    --fasta_dir $EXP_DIR/outputs/proteinmpnn/ \
    --output_dir $EXP_DIR/outputs/esmfold/ \
    --model esmfold_v1
```

### Step 4: 筛选

筛选标准（基于 Bennett et al. 和 Watson et al. 的实践）：

| 指标                                   | 阈值        |
| ------------------------------------ | --------- |
| pLDDT (平均)                           | > 80      |
| pLDDT (最低残基)                         | > 70      |
| scRMSD (vs RFdiffusion backbone, 可选) | < 2 Å     |
| Rg / Rg_expected                     | 0.8 - 1.2 |

保留同时满足所有标准的序列。

## 输出结构

```
ExperimentDir/                          ← 即本目录
├── EXPERIMENT.md
├── fold_all.py                         ← 批折叠脚本（本实验内）
└── outputs/
    ├── rfdiffusion/
    │   ├── _0.pdb
    │   ├── _0.trb
    │   └── ...
    ├── proteinmpnn/
    │   ├── design_0/
    │   │   ├── seqs/design_0.fa
    │   │   └── ...
    │   └── ...
    ├── esmfold/
    │   ├── design_0_seqs_seq0.pdb
    │   └── ...
    └── filtered/
        ├── summary.csv           # 所有成功折叠设计的指标汇总表
        └── pass_list.txt          # 通过筛选的设计 ID
```

## 期望产出

- `outputs/rfdiffusion/`：100 个 backbone（`.pdb` + `.trb`）
- `outputs/proteinmpnn/`：800 条序列
- `outputs/esmfold/`：800 个预测结构
- `outputs/filtered/summary.csv`：设计 ID、序列、pLDDT、Rg、通过与否
- `outputs/filtered/pass_list.txt`：通过筛选的设计 ID
- 通过筛选的 backbone 数量（预期 30-60 个）
- 运行时间统计：各步骤耗时

## 注意

outputs/ 不要现在删——Exp0.2 和 Exp0.3 需要引用这些数据。等整个 EG0 结束后统一清理。

- Exp0.2 将用这批数据练习质量指标提取
- Exp0.3 将在同一批序列上对比 ESMFold 和 Boltz-2

## 技术要点

- **磁盘管理**：800 个 PDB 约 200-400 MB，放 `/root/autodl-tmp/`
- **批处理**：ESMFold 推理建议用 Python 一次性加载 model 后循环，而不是反复启动脚本
- **温度选择**：ProteinMPNN 的温度越低（0.1），序列越保守、Recovery Rate 越高
