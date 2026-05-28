## 概述

本文档记录从头配置 AI for Protein Design 课程实验环境的完整步骤。遵循此文档，任何人在任何一台新的 AutoDL 云主机上均可复现。

---

2026.05.29注：本项目今日起完全实现**Agent自动化**。此MANUAL文件用于保存历史。Boltz-2 的 conda 环境被放置在数据盘，并在系统盘使用Symlink实现挂载。

---

**磁盘策略**：系统盘 `/` (30 GB) 仅放 conda 环境；数据盘 `/root/autodl-tmp/` (50 GB) 放代码、权重、输出。

**工具清单**：ProteinMPNN、RFDiffusion、ESMFold、Boltz-2。

## 环境配置操作流程

### 创建云主机

使用 [AutoDL](https://www.autodl.com)。

1. 注册并充值。

2. 在"算力市场"中选北京B区，滤出 RTX 5090，任选一台有空闲 GPU 的主机，点击"x卡可租"。

3. 按量计费，GPU 数量 1，数据盘无需扩容，镜像选 **基础镜像: PyTorch2.8.0+Python3.12(ubuntu22.04)+CUDA12.8**。

4. 创建并开机。

点击界面右上角"控制台"→"容器实例"，查看实例状态。约等 1 分钟后状态变为"运行中"，"SSH登录"栏出现登录指令和密码。

### SSH 登录云主机

在本地新建终端：

1. 复制网页上的"登录指令"，粘贴到终端运行。
   
   > 终端里复制是 `Ctrl+Shift+C`，粘贴是 `Ctrl+Shift+V`。直接 `Ctrl+C` 会终止当前进程。

2. 首次登录提示 `yes/no`，输入 `yes` 回车。

3. 提示输入密码时，复制网页上的密码粘贴进去。
   
   > 终端不显示密码字符（不会出现 `****`），粘贴完直接回车即可。

登录成功后出现欢迎信息：

```
目录说明:
╔═════════════════╦════════╦════╦═════════════════════════════════════════════════════════════════════════╗
║目录             ║名称    ║速度║说明                                                                     ║
╠═════════════════╬════════╬════╬═════════════════════════════════════════════════════════════════════════╣
║/                ║系 统 盘║一般║实例关机数据不会丢失，可存放代码等。会随保存镜像一起保存。               ║
║/root/autodl-tmp ║数 据 盘║ 快 ║实例关机数据不会丢失，可存放读写IO要求高的数据。但不会随保存镜像一起保存 ║
║/root/autodl-fs  ║文件存储║一般║可以实现多实例间的文件同步共享，不受实例开关机和保存镜像的影响。         ║
╚═════════════════╩════════╩════╩═════════════════════════════════════════════════════════════════════════╝
CPU ：25 核心
内存：90 GB
GPU ：NVIDIA GeForce RTX 5090, 1
存储：
  系 统 盘/               ：1% 53M/30G
  数 据 盘/root/autodl-tmp：1% 24K/50G
  文件存储/root/autodl-fs ：7% 13G/200G
```

**重要**：系统盘仅 30 GB，大文件（代码、权重、输出）一律放数据盘 `/root/autodl-tmp/`。

### 安装 Screen（必需）

SSH 连接断开会杀掉所有正在运行的任务。用 Screen 保持后台运行。

```bash
apt-get update && apt-get install -y screen
```

详见 [AutoDL 文档](https://www.autodl.com/docs/daemon)。

### 安装 OpenCode（可选）

在云端直接与 AI 协作，省去本地和云端来回复制的麻烦。

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 24
npm -v && node -v
npm install -g opencode-ai@latest
```

### 搭建 protein_design 虚拟环境

```bash
conda create -n protein_design --clone base -y
source ~/.bashrc
conda activate protein_design
```

所有工具共用此环境。

### ProteinMPNN

无 GPU 依赖，仅需源代码。

#### 本地下载（有 VPN）

```bash
mkdir -p /home/d9sus4/protein_learn/tools
git clone https://github.com/dauparas/ProteinMPNN.git /home/d9sus4/protein_learn/tools/proteinmpnn
```

#### 上传到云端

```bash
scp -P <端口> -r /home/d9sus4/protein_learn/tools/proteinmpnn/ root@connect.<区域>.seetacloud.com:/root/autodl-tmp/tools/
```

#### 验证

```bash
conda activate protein_design
cd /root/autodl-tmp/tools/proteinmpnn
python -c "from protein_mpnn_utils import ProteinMPNN; print('OK')"
```

若报 `ModuleNotFoundError`，缺什么就 `pip install` 什么。

### RFDiffusion

最复杂的环节。需要 CUDA 编译器、DGL、SE3Transformer 编译。

#### 本地下载代码和权重（有 VPN）

```bash
cd /home/d9sus4/protein_learn/tools
git clone https://github.com/RosettaCommons/RFdiffusion.git rfdiffusion
```

下载权重（~4.6 GB，每个约 461 MB，共 10 个）：

```bash
cd /home/d9sus4/protein_learn/tools/rfdiffusion
bash scripts/download_models.sh
```

#### 上传到云端

```bash
scp -P <端口> -r /home/d9sus4/protein_learn/tools/rfdiffusion root@connect.<区域>.seetacloud.com:/root/autodl-tmp/tools/
```

#### 在云端安装依赖

确保 `protein_design` 已激活。

```bash
conda install -c nvidia/label/cuda-12.8.0 cuda-nvcc -y
pip install --no-deps dgl==2.4.0+cu124 -f https://data.dgl.ai/wheels/torch-2.4/cu124/repo.html
pip install hydra-core pyrsistent pandas packaging pydantic pyyaml
```

验证：

```bash
nvcc --version
python -c "import dgl; print('DGL', dgl.__version__)"
```

应分别显示 CUDA 版本和 `DGL 2.4.0+cu124`。

> **为什么 `--no-deps`**：DGL 的元数据写死了 `torch<=2.4`，但实测 2.8 上能用。dgl >=2.4 才修复了 graphbolt 自动导入废弃 torchdata 的问题，而 torch-2.8 索引下的 DGL 版本更老会触发此 bug。

#### 编译 SE3Transformer 并安装 RFDiffusion

```bash
cd /root/autodl-tmp/tools/rfdiffusion/env/SE3Transformer

# 去除版本锁定，避免与新版本 PyTorch 冲突
sed -i -E 's/==[^[:space:]]+//g' requirements.txt

# 删除 dllogger（NVIDIA 内部包，GitHub 从国内无法访问）
sed -i '/dllogger/d' requirements.txt

pip install --no-cache-dir -r requirements.txt
python setup.py install

# 安装 RFDiffusion 自身
cd /root/autodl-tmp/tools/rfdiffusion
pip install -e .
```

验证：

```bash
python -c "import rfdiffusion; print('OK')"
```

#### 运行时测试

需要按量计费模式开机（GPU 可用）。无卡模式下可验证 import 但无法推理。

```bash
cd /root/autodl-tmp/tools/rfdiffusion
python scripts/run_inference.py 'contigmap.contigs=[100-100]' \
    inference.output_prefix=/root/autodl-tmp/test_outputs/uncond \
    inference.num_designs=2
```

输出 PDB 文件于 `/root/autodl-tmp/test_outputs/`，有 `*.pdb` 即成功。

### ESMFold

ESMFold 需要三个组件：fair-esm 源码（2.0.1，自带 ESMFold）、OpenFold 源码（提供底层 folding 模块）、3 个模型权重文件（~7.9 GB）。需要打多个补丁后才能工作。

#### 本地下载源码和权重（有 VPN）

```bash
# OpenFold（必须 commit 4b41059，否则 key 名不匹配）
cd /home/d9sus4/protein_learn/tools
git clone https://github.com/aqlaboratory/openfold.git
cd openfold && git checkout 4b41059694619831a7db195b7e0988fc4ff3a307

# fair-esm 源码（版本 2.0.1 定义在 esm/version.py 中，pip install 时自动读取）
cd /home/d9sus4/protein_learn/tools
git clone https://github.com/facebookresearch/esm.git esm
# 注意：v2.0.1 的 trunk.py / esmfold.py 有 mutable default 的 Python 3.12 兼容性 bug，
# 需在云端手动修复，不要在本地下手改。

# 权重（~7.9 GB, 3 个文件）
mkdir -p /home/d9sus4/protein_learn/data/esm_weights
cd /home/d9sus4/protein_learn/data/esm_weights
wget https://dl.fbaipublicfiles.com/fair-esm/models/esmfold_3B_v1.pt &
wget https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t36_3B_UR50D.pt &
wget https://dl.fbaipublicfiles.com/fair-esm/regression/esm2_t36_3B_UR50D-contact-regression.pt &
wait
```

#### 上传到云端

```bash
scp -P <端口> -r /home/d9sus4/protein_learn/tools/openfold root@connect.<区域>.seetacloud.com:/root/autodl-tmp/tools/
scp -P <端口> -r /home/d9sus4/protein_learn/tools/esm root@connect.<区域>.seetacloud.com:/root/autodl-tmp/tools/
scp -P <端口> -r /home/d9sus4/protein_learn/data/esm_weights root@connect.<区域>.seetacloud.com:/root/autodl-tmp/weights/
```

#### 重定向模型缓存到数据盘

```bash
# torch.hub 默认下载到 ~/.cache/torch/hub/checkpoints/（系统盘）
# 把它 symlink 到数据盘，避免 30GB 系统盘被权重撑爆
rm -rf ~/.cache/torch/hub/checkpoints
ln -sf /root/autodl-tmp/weights/esm_weights ~/.cache/torch/hub/checkpoints
```

这样 ESMFold（3 个权重）和 ESM-2（将来下载的模型）都自动落在数据盘上。

#### 在云端安装依赖和 fair-esm

```bash
conda activate protein_design

# 安装 ESMFold 依赖
pip install dm-tree modelcif biotite biopython einops scipy omegaconf ml_collections

# 从本地源码安装 fair-esm（2.0.1）
pip install /root/autodl-tmp/tools/esm/
```

#### 打 OpenFold 补丁（5 处）

```bash
cd /root/autodl-tmp/tools/openfold

# 清空 3 个 __init__.py，防止循环导入
echo "" > openfold/__init__.py
echo "" > openfold/model/__init__.py
echo "import importlib" > openfold/utils/__init__.py

# CUDA kernel import 包 try/except（两处）
sed -i 's/^attn_core_inplace_cuda = importlib.import_module("attn_core_inplace_cuda")$/try:\n    attn_core_inplace_cuda = importlib.import_module("attn_core_inplace_cuda")\nexcept ModuleNotFoundError:\n    attn_core_inplace_cuda = None/' \
    openfold/model/structure_module.py \
    openfold/utils/kernel/attention_core.py

# 符号链接到 site-packages
ln -sf /root/autodl-tmp/tools/openfold/openfold $(python -c "import site; print(site.getsitepackages()[0])")/openfold
```

#### 打 fair-esm 补丁（3 个文件，共 4 处改动）

```bash
# 一键打所有 fair-esm 补丁
python -c "
import site, os
sp = site.getsitepackages()[0]
e = os.path.join(sp, 'esm', 'esmfold', 'v1')

# 1. trunk.py: dataclass import + mutable default
f = os.path.join(e, 'trunk.py')
with open(f) as fh: c = fh.read()
c = c.replace('from dataclasses import dataclass', 'from dataclasses import dataclass, field')
c = c.replace('structure_module: StructureModuleConfig = StructureModuleConfig()', 'structure_module: StructureModuleConfig = field(default_factory=StructureModuleConfig)')
with open(f, 'w') as fh: fh.write(c)

# 2. esmfold.py: dataclass import + mutable default
f = os.path.join(e, 'esmfold.py')
with open(f) as fh: c = fh.read()
c = c.replace('from dataclasses import dataclass', 'from dataclasses import dataclass, field')
c = c.replace('trunk: T.Any = FoldingTrunkConfig()', 'trunk: T.Any = field(default_factory=FoldingTrunkConfig)')
with open(f, 'w') as fh: fh.write(c)

# 3. pretrained.py: 本地加载权重 + weights_only=False
f = os.path.join(sp, 'esm', 'pretrained.py')
with open(f) as fh: c = fh.read()
old = '''    try:
        data = torch.hub.load_state_dict_from_url(url, progress=False, map_location=\"cpu\")
    except RuntimeError:
        fn = Path(url).name
        data = torch.load(
            f\"{torch.hub.get_dir()}/checkpoints/{fn}\",
            map_location=\"cpu\",
        )
    except urllib.error.HTTPError as e:
        raise Exception(f\"Could not load {url}, check if you specified a correct model name?\")'''
new = '''    if \"esmfold_3B\" in url:
        path = \"/root/autodl-tmp/weights/esm_weights/esmfold_3B_v1.pt\"
    elif \"contact-regression\" in url:
        path = \"/root/autodl-tmp/weights/esm_weights/esm2_t36_3B_UR50D-contact-regression.pt\"
    elif \"esm2\" in url:
        path = \"/root/autodl-tmp/weights/esm_weights/esm2_t36_3B_UR50D.pt\"
    else:
        path = url.split(\"/\")[-1]
    data = torch.load(path, map_location=\"cpu\", weights_only=False)'''
c = c.replace(old, new)
with open(f, 'w') as fh: fh.write(c)

print('ESM patches applied')
"
```

> **pretrained.py 补丁说明**：原代码通过 `torch.hub.load_state_dict_from_url` 下载权重到 `~/.cache/torch/hub/checkpoints/`，PyTorch 2.8 默认 `weights_only=True` 导致老 checkpoint 加载失败。补丁改为直接从本地路径加载并显式传 `weights_only=False`。

#### 验证

```bash
python -c "import esm; esm.pretrained.esmfold_v1(); print('ESMFold OK')"
```

如需实际推理测试（GPU 可用时）：

```bash
mkdir -p /root/autodl-tmp/test_outputs
python -c "
import esm, torch
model = esm.pretrained.esmfold_v1()
model = model.eval().cuda()
seq = 'MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG'
with torch.no_grad():
    output = model.infer_pdb(seq)
with open('/root/autodl-tmp/test_outputs/esmfold_test.pdb', 'w') as f:
    f.write(output)
print('PDB written')
"
```
