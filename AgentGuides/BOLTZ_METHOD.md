# Boltz-2 安装方法

## 概述

Boltz-2（v2.2.1）通过 PyPI 发布，`pip install boltz[cuda]` 即可一键安装全部依赖。**无需编译器、无需补丁、无需手动处理依赖冲突。** 唯一需要手动处理的是模型权重（~5.9 GB）的下载和缓存位置。

**前置条件**：下载权重需要**美国节点的 VPN**（HuggingFace 国内无法直接访问）。Agent 应在执行下载前通过 `curl -s https://ipinfo.io/json` 确认当前 IP 在美国。pip 安装环节需要**阿里云镜像**加速。

## 与 protein_design 环境的关系

Boltz-2 **不能**装进 `protein_design` 环境。原因：
- Boltz-2 依赖 PyTorch 2.12.0+cu130，而 `protein_design` 环境用的是镜像自带的 PyTorch 2.8.0+cu128
- 两个 PyTorch 版本共存会导致不可预料的 CUDA 库冲突
- Boltz-2 从 PyPI 安装时会**自动拉取**对应版本的 `torch`、`triton`、`nvidia-cuda-*` 等全套依赖

因此 Boltz-2 需要**独立的 conda 环境**。

## 步骤 1：创建独立 conda 环境（直接进数据盘）

```bash
conda create -n boltz python=3.11 -y
```

```bash
mv /root/miniconda3/envs/boltz /root/autodl-tmp/tools/boltz
```

```bash
ln -s /root/autodl-tmp/tools/boltz /root/miniconda3/envs/boltz
```

> **为什么是 3.11 而不是 clone base 的 3.12**：Boltz-2 的 PyPI wheel 对 Python 3.11 兼容性最好。用 clone 会带入 base 环境的大量包，容易冲突。

## 步骤 2：安装 boltz

```bash
conda activate boltz
```

```bash
pip install boltz[cuda] -i https://mirrors.aliyun.com/pypi/simple/
```

> **为什么需要 `[cuda]`**：`pip install boltz[cuda]` 比 `pip install boltz` 多了三个包：
> - `cuequivariance-ops-cu12` — CUDA 加速的等变运算
> - `cuequivariance-ops-torch-cu12` — PyTorch 绑定的 CUDA 等变运算
> - `cuequivariance-torch` — PyTorch 等变运算封装
>
> 不加 `[cuda]` 的 CPU 版本速度极慢（官方文档说 "significantly slower"），必须加 `[cuda]`。

`pip install boltz` 会自动安装以下关键依赖（无需手动指定）：

| 包 | 版本 | 说明 |
|---|---|---|
| `boltz` | 2.2.1 | 主包 |
| `torch` | 2.12.0+cu130 | PyTorch（自动从 PyPI 拉取 CUDA 13.0 版本） |
| `triton` | 3.7.0 | GPU kernel 编译器 |
| `cuequivariance` | 0.10.0 | CUDA equivariance ops |
| `cuequivariance-ops-cu12` | 0.10.0 | 同上 |
| `cuequivariance-ops-torch-cu12` | 0.10.0 | 同上 |
| `cuequivariance-torch` | 0.10.0 | 同上 |
| `pytorch-lightning` | 2.5.0 | 训练框架 |
| `rdkit` | 2026.3.2 | 化学信息学 |
| `biopython` | 1.84 | 生物信息学 |
| `gemmi` | 0.6.5 | 结构生物学 |
| `fairscale` | 0.4.13 | FSDP |
| `dm-tree` | 0.1.8 | 树结构 |
| `modelcif` | 1.2 | mmCIF |
| `numba` | 0.61.0 | JIT 编译 |

> **关键发现**：`pip install boltz[cuda]` 会**自动拉取 torch 2.12.0 的 CUDA 13.0 版本**。不需要手动装 PyTorch，也不需要装任何 NVIDIA CUDA 工具包。整个过程是纯 pip，无需 conda install。注意必须加 `[cuda]`，否则缺 cuequivariance CUDA ops 包。

## 步骤 3：配置模型缓存（避免占系统盘）

Boltz-2 默认将权重下载到 `~/.boltz/`，这在系统盘上。需要 symlink 到数据盘：

```bash
mkdir -p /root/autodl-tmp/weights/boltz
```

```bash
rm -rf ~/.boltz
```

```bash
ln -sf /root/autodl-tmp/weights/boltz ~/.boltz
```

## 步骤 4：下载模型权重

权重来源：HuggingFace `boltz-community/boltz-2`

需要下载 3 个部分（约 5.9 GB）：

| 文件 | 大小 | 用途 | URL |
|---|---|---|---|
| `boltz2_conf.ckpt` | 2.0 GB | 结构预测主模型 | [HF](https://huggingface.co/boltz-community/boltz-2/resolve/main/boltz2_conf.ckpt) |
| `boltz2_aff.ckpt` | 2.2 GB | 亲和力预测模型 | [HF](https://huggingface.co/boltz-community/boltz-2/resolve/main/boltz2_aff.ckpt) |
| `mols.tar` | ~1.8 GB（解压后） | CCD 小分子字典 | [HF](https://huggingface.co/boltz-community/boltz-2/resolve/main/mols.tar) |

### 本地下载（需要美国节点的 VPN）

> **AI Agent 注意事项**：下载前先通过 `curl -s https://ipinfo.io/json` 检测当前 IP 是否在美国。如果不是美国节点，**必须提醒用户切换到美国 VPN** 后再继续，否则 HuggingFace 下载会失败或极慢。

```bash
mkdir -p ~/.tmp/protein_learn/weights/boltz
```

```bash
wget -O ~/.tmp/protein_learn/weights/boltz/boltz2_conf.ckpt \
    https://huggingface.co/boltz-community/boltz-2/resolve/main/boltz2_conf.ckpt &
wget -O ~/.tmp/protein_learn/weights/boltz/boltz2_aff.ckpt \
    https://huggingface.co/boltz-community/boltz-2/resolve/main/boltz2_aff.ckpt &
wget -O ~/.tmp/protein_learn/weights/boltz/mols.tar \
    https://huggingface.co/boltz-community/boltz-2/resolve/main/mols.tar &
wait
```

```bash
tar xf ~/.tmp/protein_learn/weights/boltz/mols.tar -C ~/.tmp/protein_learn/weights/boltz/
```

### 上传到云端

```bash
scp -P <port> ~/.tmp/protein_learn/weights/boltz/boltz2_conf.ckpt \
    root@connect.<region>.seetacloud.com:/root/autodl-tmp/weights/boltz/
```

```bash
scp -P <port> ~/.tmp/protein_learn/weights/boltz/boltz2_aff.ckpt \
    root@connect.<region>.seetacloud.com:/root/autodl-tmp/weights/boltz/
```

```bash
scp -P <port> ~/.tmp/protein_learn/weights/boltz/mols.tar \
    root@connect.<region>.seetacloud.com:/root/autodl-tmp/weights/boltz/
```

```bash
# 在云端解压
ssh("tar xf /root/autodl-tmp/weights/boltz/mols.tar -C /root/autodl-tmp/weights/boltz/")
```

### 备选方案：在云端直接下载

如果云端能访问 HuggingFace，也可以直接运行 boltz 让它自动下载：

```bash
conda activate boltz
```

```bash
export BOLTZ_CACHE=/root/autodl-tmp/weights/boltz
```

```bash
python -c "from boltz.main import download_boltz2; from pathlib import Path; download_boltz2(Path('/root/autodl-tmp/weights/boltz'))"
```

> 注意：mols.tar 包含 45,227 个小文件（约 1.8 GB），解压后体积基本不变。下载和解压都很耗时（约 10-20 分钟），建议用 screen。

## 步骤 5：验证安装

```bash
conda activate boltz
```

```bash
python -c "import boltz; print('Boltz version:', boltz.__version__)"
```

```bash
python -c "from boltz.model.models.boltz2 import Boltz2; print('Boltz2 model OK')"
```

```bash
python -c "from boltz.data.module.inferencev2 import Boltz2InferenceDataModule; print('Data module OK')"
```

```bash
python -c "import torch; print('PyTorch', torch.__version__, 'CUDA', torch.version.cuda)"
```

预期输出：
```
Boltz version: 2.2.1
Boltz2 model OK
Data module OK
PyTorch 2.12.0 CUDA 13.0
```

在无 GPU 模式下 `torch.cuda.is_available()` 返回 `False` 是正常的。

### 有 GPU 时运行测试

```bash
mkdir -p /root/autodl-tmp/test_outputs
```

```bash
echo ">test" > /root/autodl-tmp/test.fasta
echo "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG" >> /root/autodl-tmp/test.fasta
```

```bash
boltz predict \
    --model boltz2 \
    --cache /root/autodl-tmp/weights/boltz \
    --out_dir /root/autodl-tmp/test_outputs \
    --sampling_steps 50 \
    --diffusion_samples 1 \
    /root/autodl-tmp/test.fasta
```

> `boltz predict` CLI 也可直接使用：先 `conda activate boltz`，然后 `boltz predict --help` 查看完整参数。

## 无补丁！与 ESMFold 的对比

| 项目 | ESMFold | Boltz-2 |
|---|---|---|
| 安装方式 | 从源码 pip install | `pip install boltz[cuda]`（PyPI） |
| PyTorch 版本 | 2.8.0（镜像自带） | 2.12.0（pip 自动拉取） |
| CUDA 编译器 | 需要 nvcc | 不需要 |
| 额外依赖 | OpenFold 源码+5 处补丁 | 无 |
| fair-esm 补丁 | 3 文件 4 处改动 | 无 |
| 权重来源 | Facebook Research（dl.fbaipublicfiles.com） | HuggingFace |
| 环境 | 共用 protein_design | 独立 boltz 环境 |
| 安装难度 | 极高（通宵才能搞定） | 低（一条 pip install） |

## 注意事项

1. **必须用独立环境**：Boltz-2 拉取的 torch 2.12.0 与镜像自带的 2.8.0 不兼容
2. **Python 3.11**：不要用 3.12，PyPI wheel 兼容性最好
3. **不要 clone base**：clone 会带入基础环境的 torch 等包，产生版本冲突
4. **环境必须放数据盘**：完整 boltz 环境约 8-10 GB，系统盘装不下
5. **无 GPU 下 import 较慢**：PyTorch 2.12.0 在无 GPU 模式下初始化 CUDA 绑定时可能需要 30-60 秒，这是正常的
6. **mols/ 目录有 45,227 个小文件**：`scp -r` 上传会很慢，建议传 `mols.tar` 后在云端解压
