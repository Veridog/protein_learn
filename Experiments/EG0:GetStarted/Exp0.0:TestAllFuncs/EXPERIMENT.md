# Exp0.0 — 环境验证：逐一测试所有工具

## 目标

确认 RFdiffusion、ProteinMPNN、ESMFold、Boltz-2 四个工具全部可 import 且能完成最小推理。不和管线耦合，每个单独跑。

## 背景

环境搭建过程中可能出各种隐蔽问题：

- 某个 import 过但实际推理时报 CUDA 版本不匹配
- 权重路径错误导致静默失败
- 不同 conda 环境之间有污染

这些要在进入正经实验前排除。

## 任务

### 1. RFdiffusion — 最小单体生成

```bash
conda activate protein_design
cd /root/autodl-tmp/tools/rfdiffusion
mkdir -p /root/autodl-tmp/Experiments/EG0:GetStarted/Exp0.0:TestAllFuncs/outputs
python scripts/run_inference.py 'contigmap.contigs=[50-50]' \
    inference.output_prefix=/root/autodl-tmp/Experiments/EG0:GetStarted/Exp0.0:TestAllFuncs/outputs/rfdiffusion/test \
    inference.num_designs=1
```

验证：实验目录下的 `outputs/rfdiffusion/` 中有 `.pdb` 文件，且残基数为 50。

### 2. ProteinMPNN — 对 RFdiffusion 输出设计序列

```bash
conda activate protein_design
cd /root/autodl-tmp/tools/proteinmpnn
python protein_mpnn_run.py \
    --pdb_path /root/autodl-tmp/Experiments/EG0:GetStarted/Exp0.0:TestAllFuncs/outputs/rfdiffusion/test_0.pdb \
    --out_folder /root/autodl-tmp/Experiments/EG0:GetStarted/Exp0.0:TestAllFuncs/outputs/proteinmpnn/ \
    --num_seq_per_target 1
```

验证：`outputs/proteinmpnn/seqs/` 下有 `.fa` 文件。

### 3. ESMFold — 对 MPNN 序列预测结构

```bash
conda activate protein_design
python -c "
import esm, torch
model = esm.pretrained.esmfold_v1()
model = model.eval().cuda()
EXP_DIR = '/root/autodl-tmp/Experiments/EG0:GetStarted/Exp0.0:TestAllFuncs'
with open(f'{EXP_DIR}/outputs/proteinmpnn/seqs/test_0.fa') as f:
    lines = f.readlines()
    seq = lines[3].strip()  # 第4行才是 ProteinMPNN 设计的序列（跳过 backbone G 链）
with torch.no_grad():
    output = model.infer_pdb(seq)
import os; os.makedirs(f'{EXP_DIR}/outputs/esmfold', exist_ok=True)
with open(f'{EXP_DIR}/outputs/esmfold/test.pdb', 'w') as f:
    f.write(output)
"
```

验证：`outputs/esmfold/test.pdb` 存在，残基数与输入序列一致。

### 4. Boltz-2 — 对同一序列预测结构

```bash
conda activate boltz
EXP_DIR=/root/autodl-tmp/Experiments/EG0:GetStarted/Exp0.0:TestAllFuncs
mkdir -p $EXP_DIR/outputs/boltz
cat > $EXP_DIR/outputs/boltz/test.yaml << EOF
version: 1
sequences:
  - protein:
      id: A
      sequence: $(sed -n '4p' $EXP_DIR/outputs/proteinmpnn/seqs/test_0.fa)
      msa: empty
EOF
boltz predict $EXP_DIR/outputs/boltz/test.yaml \
    --out_dir $EXP_DIR/outputs/boltz/ \
    --output_format pdb \
    --sampling_steps 10 \
    --diffusion_samples 1
```

验证：`outputs/boltz/` 下有 `.pdb` 文件。

## 期望产出

- `outputs/rfdiffusion/test_0.pdb`：RFdiffusion 生成的 50 残基蛋白质
- `outputs/proteinmpnn/seqs/test_0.fa`：ProteinMPNN 设计的序列
- `outputs/esmfold/test.pdb`：ESMFold 预测的结构
- `outputs/boltz/test.pdb`：Boltz-2 预测的结构
- `verify_all.py`（本目录下）：一键验证脚本，后续任何新环境可重跑
- 若失败：错误信息 + 修复记录 → 写入 `AgentGuides/Situations/`
