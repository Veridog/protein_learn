# LigandMPNN 安装指南

## 概述

LigandMPNN 是 ProteinMPNN 的升级版，训练时加入了配体（小分子、金属离子、核酸、辅因子等）的 3D 上下文。用于酶设计、金属结合蛋白设计等需要配体感知的任务。

- **仓库**：https://github.com/dauparas/LigandMPNN
- **论文**：Dauparas et al. (2023) "Atomic context-conditioned protein sequence design using LigandMPNN"
- **许可证**：MIT
- **依赖**：Python≥3.0, PyTorch, Numpy, Prody（比 ProteinMPNN 仅多 Prody）

## 环境

可复用现有的 `protein_design` conda 环境。不需要独立环境。

## 安装步骤

### 步骤 1：本地下载代码（需要 VPN）

```bash
cd ~/.tmp/protein_learn/tools
git clone https://github.com/dauparas/LigandMPNN.git ligandmpnn
```

### 步骤 2：本地下载模型权重

```bash
mkdir -p ~/.tmp/protein_learn/weights/ligandmpnn
cd ~/.tmp/protein_learn/weights/ligandmpnn

# 4 × ProteinMPNN 权重（~140 MB）
wget https://files.ipd.uw.edu/pub/ligandmpnn/proteinmpnn_v_48_002.pt &
wget https://files.ipd.uw.edu/pub/ligandmpnn/proteinmpnn_v_48_010.pt &
wget https://files.ipd.uw.edu/pub/ligandmpnn/proteinmpnn_v_48_020.pt &
wget https://files.ipd.uw.edu/pub/ligandmpnn/proteinmpnn_v_48_030.pt &

# 4 × LigandMPNN 权重（~140 MB）
wget https://files.ipd.uw.edu/pub/ligandmpnn/ligandmpnn_v_32_005_25.pt &
wget https://files.ipd.uw.edu/pub/ligandmpnn/ligandmpnn_v_32_010_25.pt &
wget https://files.ipd.uw.edu/pub/ligandmpnn/ligandmpnn_v_32_020_25.pt &
wget https://files.ipd.uw.edu/pub/ligandmpnn/ligandmpnn_v_32_030_25.pt &

# 1 × 侧链包装模型（~35 MB）
wget https://files.ipd.uw.edu/pub/ligandmpnn/ligandmpnn_sc_v_32_002_16.pt &
wait
```

### 步骤 3：上传到云端

```bash
# 代码
scp -P <port> -r ~/.tmp/protein_learn/tools/ligandmpnn root@connect.<region>.seetacloud.com:/root/autodl-tmp/tools/

# 权重
scp -P <port> -r ~/.tmp/protein_learn/weights/ligandmpnn root@connect.<region>.seetacloud.com:/root/autodl-tmp/weights/
```

### 步骤 4：在云端安装依赖并打补丁

```bash
conda activate protein_design
pip install prody

# NumPy 兼容性补丁（np.int 已从 NumPy 1.20+ 移除）
sed -i 's/dtype=np\.int)/dtype=int)/g' /root/autodl-tmp/tools/ligandmpnn/openfold/np/residue_constants.py
sed -i 's/dtype=np\.int,/dtype=int,/g' /root/autodl-tmp/tools/ligandmpnn/openfold/np/residue_constants.py
```

### 步骤 5：验证

```bash
conda activate protein_design
python -c "
import sys
sys.path.insert(0, '/root/autodl-tmp/tools/ligandmpnn')
from model_utils import ProteinMPNN
print('LigandMPNN import OK')
"
```

### 步骤 6：运行时测试（有 GPU 时）

```bash
conda activate protein_design
python /root/autodl-tmp/tools/ligandmpnn/run.py \
    --model_type "ligand_mpnn" \
    --seed 111 \
    --pdb_path /root/autodl-tmp/tools/ligandmpnn/inputs/1BC8.pdb \
    --out_folder /root/autodl-tmp/test_outputs/ligandmpnn_test \
    --checkpoint_ligand_mpnn /root/autodl-tmp/weights/ligandmpnn/ligandmpnn_v_32_010_25.pt
```

验证：`/root/autodl-tmp/test_outputs/ligandmpnn_test/` 下有 `.fa` 文件。

## 模型清单

| 模型                     | 文件                             | 大小     |
| ---------------------- | ------------------------------ | ------ |
| ProteinMPNN 0.02Å      | `proteinmpnn_v_48_002.pt`      | 6.4 MB |
| ProteinMPNN 0.10Å      | `proteinmpnn_v_48_010.pt`      | 6.4 MB |
| ProteinMPNN 0.20Å      | `proteinmpnn_v_48_020.pt`      | 6.4 MB |
| ProteinMPNN 0.30Å      | `proteinmpnn_v_48_030.pt`      | 6.4 MB |
| LigandMPNN 0.05Å/ctx25 | `ligandmpnn_v_32_005_25.pt`    | 11 MB  |
| LigandMPNN 0.10Å/ctx25 | `ligandmpnn_v_32_010_25.pt`    | 11 MB  |
| LigandMPNN 0.20Å/ctx25 | `ligandmpnn_v_32_020_25.pt`    | 11 MB  |
| LigandMPNN 0.30Å/ctx25 | `ligandmpnn_v_32_030_25.pt`    | 11 MB  |
| 侧链包装                   | `ligandmpnn_sc_v_32_002_16.pt` | 14 MB  |

**总计：约 80 MB**

## 与 ProteinMPNN 的区别

| 特性       | ProteinMPNN           | LigandMPNN               |
| -------- | --------------------- | ------------------------ |
| 路径       | `/tools/proteinmpnn/` | `/tools/ligandmpnn/`     |
| 入口脚本     | `protein_mpnn_run.py` | `run.py`                 |
| 配体感知     | ✗                     | ✓                        |
| 侧链包装     | ✗                     | ✓ (可选)                   |
| 多链设计     | ✓                     | ✓ (增强)                   |
| 固定/重设计残基 | 索引方式                  | 支持 `A23`、`B42D` 格式       |
| 对称设计     | ✗                     | ✓                        |
| 膜蛋白      | ✗                     | ✓ (全局/残基标签)              |
| 依赖       | -                     | 多一个 Prody                |
| 模型权重     | ~25 MB                | ~80 MB（含 ProteinMPNN 权重） |

## 使用方式

两个工具共存，不会混淆：

```bash
# 旧的（无配体）
cd /root/autodl-tmp/tools/proteinmpnn
python protein_mpnn_run.py --pdb_path ...

# 新的配体模式
python /root/autodl-tmp/tools/ligandmpnn/run.py \
    --model_type "ligand_mpnn" \
    --checkpoint_ligand_mpnn /root/autodl-tmp/weights/ligandmpnn/ligandmpnn_v_32_010_25.pt ...

# 新的当普通 MPNN 用（可替代旧的）
python /root/autodl-tmp/tools/ligandmpnn/run.py \
    --model_type "protein_mpnn" \
    --checkpoint_protein_mpnn /root/autodl-tmp/weights/ligandmpnn/proteinmpnn_v_48_020.pt ...
```

目录名、入口脚本名、参数体系都不一样，不会混淆。

## 注意事项

1. LigandMPNN 内部已包含 ProteinMPNN 功能，可以完全替代 ProteinMPNN
2. 需要使用配体时，输入 PDB 必须包含配体原子（HETATM 行）
3. 侧链包装（`--pack_side_chains`）需要额外的侧链模型
4. 权重来源 `files.ipd.uw.edu` 是 UW IPD 服务器，可能在部分网络环境下无需 VPN
