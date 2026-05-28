## 概述

你是一个 AI agent，帮用户在一台**全新的电脑**上从零搭建 AI for Protein Design 实验环境，服务对象是一台**新的 AutoDL 云主机**。用户可能会提出不相关的问题，比如“请给我20种氨基酸的性质表格”，此时你不需要按照此文件执行，只有用户明确提出“协助我从头配置好环境”类似的表达的时候才按下面的步骤执行。

**你的职责**：

1. 帮用户安装 `opencode-ssh-session` 插件和 skill
2. 引导用户在网页上完成云主机的创建和首次登录
3. 帮用户配置 SSH 密钥免密登录（之后你就能接管了）
4. 通过 `ssh_connect` 连接云主机，之后所有操作你自动完成

**本指南将安装以下工具**：ProteinMPNN、RFDiffusion、ESMFold、Boltz-2

**你可以用的工具**：

- 本地 `bash` — 安装 npm 包、生成密钥、执行 `scp`、`git clone` 等本地操作
- `ssh_connect` / `ssh` / `ssh_info` / `ssh_disconnect` — 操控云主机（来自 opencode-ssh-session 插件）
- `ssh_upload` / `ssh_download` — 小文件传输（< 1MB，base64 编码，不适合大文件或目录）
- `question` — 向用户提问确认。只要你有点不确定，请千万不要吝啬于向用户提问。用户给出的最坏的答案也只会是“我不知道”。但在提问的时候，一定要让用户掌握充分的信息，比如把现状讲解明白。

**重要规则**：当遇到意外情况，你执行的命令与本文档所述不同（例如打了一个新补丁、用了不同的版本、跳过了某一步），**必须**将差异记录到项目根目录的 `CHANGELOG.md` 中。格式：时间戳 + 原步骤 + 实际执行内容 + 原因。

---

## 关于 GPU 可用性

AutoDL 支持 **"有 GPU 开机"** 和 **"无 GPU 开机"** 两种模式。SSH 能连上但 `nvidia-smi` 不可用 / `/dev/nvidia*` 不存在 / `torch.cuda.is_available()` 返回 `False`，**不是 bug，是无 GPU 启动的正常状态**。无 GPU 模式价格更低，适合代码开发、import 验证等不需要 GPU 的工作。

Agent 的行为准则：

- **代码验证（import、语法检查等）**：在无 GPU 模式下完成即可，不需要 GPU
- **实际推理 / 运行时测试**：需要用户切换到有 GPU 模式，Agent 应提醒用户
- **检测到无 GPU 时**：不要惊惶，继续当前能做的验证工作。所有 `import` 验证通过后，告知用户"可以上 GPU 了"
- **判别方法**：`torch.cuda.is_available()` 为 `False` 即当前无 GPU

---

## 关于长时间 SSH 下载 / 安装任务

`pip install` 大包（如 torch 500MB+）、`wget` 大文件、conda 环境创建等可能超过 SSH 工具默认超时（2分钟）。对于此类可能超过 2 分钟的任务，**必须使用 screen 在云端后台运行**，就像跑蛋白质设计推理任务一样。

```bash
# 不要直接用 ssh() 跑长时间任务，而是：
screen -dmS <session_name> bash -c 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate <env> && <long_command> 2>&1 | tee /tmp/<log_name>.log'
```

然后用 `tail -f /tmp/<log_name>.log` 轮询进度。

---

## 步骤 0：安装 opencode-ssh-session 插件和 Skill

> 这是你**最先要做的**。没有这个插件，后续所有 SSH 操作都无法进行。

### 0.1 安装插件

```bash
npm install -g opencode-ssh-session
```

### 0.2 注册到 opencode.json

检查 `~/.config/opencode/opencode.json`，在 `"plugin"` 数组中添加 `"opencode-ssh-session"`：

```json
{
  "plugin": ["opencode-ssh-session"]
}
```

如果已有其他 plugin，追加即可，不要覆盖。

### 0.3 安装 Skill

从 GitHub 克隆仓库，将 skill 复制到全局 skills 目录：

```bash
git clone https://github.com/PedroKlein/opencode-ssh-session /tmp/opencode-ssh-session
mkdir -p ~/.config/opencode/skills/ssh-remote-dev
cp /tmp/opencode-ssh-session/examples/skills/ssh-remote-dev/SKILL.md ~/.config/opencode/skills/ssh-remote-dev/SKILL.md
```

### 0.4 安装 Commands

```bash
mkdir -p ~/.config/opencode/commands
cp /tmp/opencode-ssh-session/examples/commands/ssh.md ~/.config/opencode/commands/ssh.md
cp /tmp/opencode-ssh-session/examples/commands/ssh-status.md ~/.config/opencode/commands/ssh-status.md
```

安装完成后，**提醒用户重启 OpenCode** 使插件生效。并告知重启之后通过"/session"命令能找回到刚才的对话。然后继续下一步。

### 0.5 修正 SKILL.md 中的文件传输指引

SKILL.md 原版有两处需要修改，否则会误导 AI 在传输大文件时让用户手动操作，而不是自己执行 `scp`。

用 `Edit` 工具修改 `~/.config/opencode/skills/ssh-remote-dev/SKILL.md`：

**修改 1**：工具列表中为 ssh_upload / ssh_download 添加限制说明

原内容：

```
- `ssh_upload` — Transfer a local file to the remote host
- `ssh_download` — Transfer a remote file to the local machine
```

改为：

```
- `ssh_upload` — Transfer a local file to the remote host (small files < 1MB only, base64)
- `ssh_download` — Transfer a remote file to the local machine (small files < 1MB only, base64)
```

**修改 2**：大文件传输策略，不要建议用户手动操作，而是让 AI 自己执行 scp

原内容：

```
**Large files (> 1MB):** The base64 encoding adds ~33% overhead. For very large files, suggest the user use `scp` or `rsync` directly outside of OpenCode.
```

改为：

```
**Large files (> 1MB):** The base64 encoding adds ~33% overhead. Use the local `bash` tool to run `scp` or `rsync` directly. Run `ssh_info` first to get the current host and port, then construct the `scp` or `rsync` command. Do NOT ask the user to do this manually — you can execute it yourself.
```

---

## 步骤 1：创建云主机

# 

### 1.1 注册

引导用户访问 [AutoDL 官网](https://www.autodl.com)，注册并充值。

### 1.2 选择配置

在"算力市场"页面：

- **区域**：推荐北京 B 区（网络较稳定）
- **GPU**：筛选 RTX 5090（32GB 显存）
- 任选一台有 1 卡空闲的主机，点击"x 卡可租"
- **计费模式**：按量计费
- **GPU 数量**：1
- **数据盘**：无需扩容（默认 50GB 足够）
- **镜像**：基础镜像 `PyTorch2.8.0+Python3.12(ubuntu22.04)+CUDA12.8`

点击创建并开机。

**向用户提问确认**：你选择的区域是哪个？RTX 5090 在哪些区域有货？用户回答后继续。

### 1.3 等待就绪

创建后约 1 分钟，实例状态变为"运行中"。"SSH 登录"栏出现登录指令和密码。

---

## 步骤 2：首次登录云主机（用户手动操作）

> **此时你还无法代劳**——SSH 密码登录需要交互式输入密码，`ssh_connect` 不支持。用户需要先在自己的终端完成首次登录和密钥配置。

告知用户按以下步骤操作：

1. **打开一个新的本地终端窗口**（不占 OpenCode 的终端）

2. 从 AutoDL 网页"控制台"→"容器实例"→对应实例的 **"SSH 登录"栏**，复制**登录指令**。粘贴到终端，回车。
   
   > 注意：终端里的粘贴是 `Ctrl+Shift+V`（不是 `Ctrl+V`）。

3. 首次登录会提示：
   
   ```
   The authenticity of host '...' can't be established.
   Are you sure you want to continue connecting (yes/no)?
   ```
   
   输入 `yes` 回车。

4. 提示 `root@...'s password:` 时，从网页**"SSH 登录"栏复制密码**，粘贴到终端，回车。
   
   > 终端不会显示密码字符（不会出现 `****`），粘贴完直接回车即可。

5. 登录成功后，终端会显示一段系统信息（欢迎信息、磁盘说明、CPU/GPU/内存规格）。看到这些说明登录成功。

---

## 步骤 3：配置 SSH 密钥（你在本地操作）

现在你在本地帮用户生成密钥，然后给出一个命令让用户粘贴到云主机终端即可。

### 3.1 生成密钥（本地 bash）

先检查是否已有密钥：

```bash
ls ~/.ssh/id_*
```

如果**没有** `id_ed25519` 或 `id_ed25519.pub`，则生成：

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
```

然后用 `Read` 工具读取公钥内容：

```
~/.ssh/id_ed25519.pub
```

### 3.2 让用户把公钥写入云主机

把以下内容（将公钥嵌入）告诉用户，让用户**在已登录的云主机终端**中粘贴执行：

```bash
mkdir -p ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA..." >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

> `echo` 后面引号内的是刚从 `~/.ssh/id_ed25519.pub` 读到的公钥内容。**不要用 `...` 省略，必须粘贴完整的一行**。

完成后告诉用户：密钥已配置，现在可以用 `/ssh` 命令了。

---

## 步骤 4：接入 OpenCode

让用户输入 `/ssh` 命令触发连接。例如用户输入：

```
/ssh -p 33534 root@connect.bjb2.seetacloud.com
```

你收到 host 和 port 后，执行：

```
ssh_connect(host="root@connect.<region>.seetacloud.com", options="-p <port>")
```

连接成功后，用 `ssh_info` 确认，然后跑：

```bash
hostname && uptime && echo "gpu:" && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
```

报告结果给用户。从此之后，所有云端操作你通过 `ssh()` 自动完成。

---

## 文件传输策略（Agent 请记住）

| 场景                             | 方法                                                              |
| ------------------------------ | --------------------------------------------------------------- |
| 单个小文件 (< 1MB)                  | `ssh_upload` / `ssh_download`                                   |
| 目录、大文件                         | 本地 `bash` 执行 `scp -r`。**执行前先 `ssh_info` 获取 host/port**，避免忘记连接参数 |
| 代码可从 GitHub clone              | `ssh()` 在云端直接 `git clone`，最省事                                   |
| 美国源的权重大文件（如 Facebook Research） | 始终在**有美国 VPN 的本地 bash**中下载，然后本地 bash 执行 `scp` 上传到云端             |

> `scp` 示例（从 ssh_info 提取 port 和 host 后拼）：
> 
> ```bash
> scp -P 33534 -r ~/.tmp/protein_learn/tools/xxx root@connect.bjb2.seetacloud.com:/root/autodl-tmp/tools/
> ```

## 执行前确认

在开始任何下载步骤前，向用户提问确认：

> 你是否连接了美国节点的 VPN？后续需要从 GitHub 和 Facebook Research 下载代码及模型权重，国内网络可能无法直接访问。

只有用户确认 VPN 可用后才继续。

## 环境配置

### 安装 Screen（必需）

SSH 连接断开会杀掉正在运行的任务。用 Screen 保持后台运行。

```bash
apt-get update && apt-get install -y screen
```

所有长任务用 screen 运行：

```bash
screen -dmS <session_name> bash -c '<command>'
```

### 搭建 protein_design 虚拟环境

```bash
conda create -n protein_design --clone base -y
source ~/.bashrc
conda activate protein_design
```

注意：`conda activate` 的效果通过 `ssh()` 的持久化 session 保持，后续命令不需要重复激活。

## ProteinMPNN

无 GPU 依赖，仅需源代码。

### 本地下载（需要 VPN）

```bash
mkdir -p ~/.tmp/protein_learn/data/esm_weights
wget -O ~/.tmp/protein_learn/data/esm_weights/esmfold_3B_v1.pt https://dl.fbaipublicfiles.com/fair-esm/models/esmfold_3B_v1.pt &
wget -O ~/.tmp/protein_learn/data/esm_weights/esm2_t36_3B_UR50D.pt https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t36_3B_UR50D.pt &
wget -O ~/.tmp/protein_learn/data/esm_weights/esm2_t36_3B_UR50D-contact-regression.pt https://dl.fbaipublicfiles.com/fair-esm/regression/esm2_t36_3B_UR50D-contact-regression.pt &
wait
```

### 上传到云端

ProteinMPNN 代码量不大，直接在本地用 `scp -r` 上传。先用 `ssh_info` 确认 host/port：

```bash
# 本地 bash：
ssh("mkdir -p /root/autodl-tmp/tools/proteinmpnn")
scp -P <port> -r ~/.tmp/protein_learn/tools/proteinmpnn/* root@connect.<region>.seetacloud.com:/root/autodl-tmp/tools/proteinmpnn/
```

> 备选方案：如果云端能直接访问 GitHub，用 `ssh("cd /root/autodl-tmp/tools && git clone https://github.com/dauparas/ProteinMPNN.git proteinmpnn")` 更省事。

### 验证

```bash
ssh("conda activate protein_design && cd /root/autodl-tmp/tools/proteinmpnn && python -c \"from protein_mpnn_utils import ProteinMPNN; print('OK')\"")
```

若报 `ModuleNotFoundError`，缺什么就 `pip install` 什么。

## RFDiffusion

最复杂的环节。需要 CUDA 编译器、DGL、SE3Transformer 编译。

### 本地下载代码和权重（需要 VPN）

```bash
mkdir -p ~/.tmp/protein_learn/tools
cd ~/.tmp/protein_learn/tools
git clone https://github.com/RosettaCommons/RFdiffusion.git rfdiffusion
```

下载权重（~4.6 GB，每个约 461 MB，共 10 个）：

```bash
cd ~/.tmp/protein_learn/tools/rfdiffusion
bash scripts/download_models.sh ~/.tmp/protein_learn/tools/rfdiffusion/models
```

### 上传到云端

代码+权重体积较大。先用 `ssh_info` 确认 host/port，然后本地 bash 执行 scp：

```bash
# 本地 bash（从 ssh_info 获取 port 和 host）：
scp -P <端口> -r ~/.tmp/protein_learn/tools/rfdiffusion root@connect.<区域>.seetacloud.com:/root/autodl-tmp/tools/
```

### 在云端安装依赖

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

### 编译 SE3Transformer 并安装 RFDiffusion

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

### 运行时测试

```bash
cd /root/autodl-tmp/tools/rfdiffusion
python scripts/run_inference.py 'contigmap.contigs=[100-100]' \
    inference.output_prefix=/root/autodl-tmp/test_outputs/uncond \
    inference.num_designs=2
```

输出 PDB 文件于 `/root/autodl-tmp/test_outputs/`，有 `*.pdb` 即成功。

## ESMFold

ESMFold 需要三个组件：fair-esm 源码（2.0.1，自带 ESMFold）、OpenFold 源码（提供底层 folding 模块）、3 个模型权重文件（~7.9 GB）。需要打多个补丁后才能工作。

### 本地下载源码和权重（需要 VPN）

```bash
mkdir -p ~/.tmp/protein_learn/{tools,weights/esm_weights}

# OpenFold（必须 commit 4b41059，否则 key 名不匹配）
cd ~/.tmp/protein_learn/tools
git clone https://github.com/aqlaboratory/openfold.git
cd openfold && git checkout 4b41059694619831a7db195b7e0988fc4ff3a307

# fair-esm 源码（版本 2.0.1 定义在 esm/version.py 中，pip install 时自动读取）
cd ~/.tmp/protein_learn/tools
git clone https://github.com/facebookresearch/esm.git esm
# v2.0.1 的 trunk.py / esmfold.py 有 mutable default 的 Python 3.12 兼容性 bug，
# 需在云端安装后手动修复补丁，不要在本地下手改。

# 权重（~7.9 GB, 3 个文件）
cd ~/.tmp/protein_learn/weights/esm_weights
wget https://dl.fbaipublicfiles.com/fair-esm/models/esmfold_3B_v1.pt &
wget https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t36_3B_UR50D.pt &
wget https://dl.fbaipublicfiles.com/fair-esm/regression/esm2_t36_3B_UR50D-contact-regression.pt &
wait
```

### 上传源码和权重到云端

> 权重体积较大（~7.9GB）。先用 `ssh_info` 确认 host/port，然后本地 bash 执行 scp：

```
scp -P <端口> -r ~/.tmp/protein_learn/tools/openfold root@connect.<区域>.seetacloud.com:/root/autodl-tmp/tools/
scp -P <端口> -r ~/.tmp/protein_learn/tools/esm root@connect.<区域>.seetacloud.com:/root/autodl-tmp/tools/
scp -P <端口> -r ~/.tmp/protein_learn/data/esm_weights root@connect.<区域>.seetacloud.com:/root/autodl-tmp/weights/
```

### 重定向模型缓存到数据盘

```bash
# torch.hub 默认下载到 ~/.cache/torch/hub/checkpoints/（系统盘）
# 把它 symlink 到数据盘，避免 30GB 系统盘被权重撑爆
rm -rf ~/.cache/torch/hub/checkpoints
ln -sf /root/autodl-tmp/weights/esm_weights ~/.cache/torch/hub/checkpoints
```

这样 ESMFold（3 个权重）和 ESM-2（将来下载的模型）都自动落在数据盘上。

### 在云端安装依赖和 fair-esm

```bash
conda activate protein_design

# 安装 ESMFold 依赖
pip install dm-tree modelcif biotite biopython einops scipy omegaconf ml_collections

# 从本地源码安装 fair-esm（2.0.1）
pip install /root/autodl-tmp/tools/esm/
```

### 打 OpenFold 补丁（5 处）

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

### 打 fair-esm 补丁（3 个文件，共 4 处改动）

```bash
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

### 验证

```bash
python -c "import esm; esm.pretrained.esmfold_v1(); print('ESMFold OK')"
```

如需实际推理测试：

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

## 注意事项

1. **大文件传输**：`ssh_upload` / `ssh_download` 使用 base64 编码，仅适合 <1MB 的小文件。对于代码库和权重（几百 MB 到几 GB），使用本地 `bash` 工具执行 `scp`，执行前先用 `ssh_info` 获取 host 和端口。
2. **长任务用 screen**：任何超过 2 分钟的任务用 `screen -dmS <name> bash -c '<cmd>'` 在云端后台运行，避免 SSH session 超时。
3. **环境持久性**：`conda activate` 在 ssh session 中持久有效，不需要每个命令重复激活。但如果用 screen，需要在 screen 的命令中显式 `source ~/.bashrc && conda activate protein_design && ...`。
4. **系统盘空间**：始终注意 `/` 系统盘只有 30GB。`pip install` 的缓存、torch hub 的模型等默认都会下到系统盘，需要及时清理或重定向到数据盘。
5. **记录偏差**：当遇到意外情况，你执行的命令与本文档所述不同（例如打了一个新补丁、用了不同的版本、跳过了某一步），**必须**将差异记录到项目根目录的 `CHANGELOG.md` 中。格式：时间戳 + 原步骤 + 实际执行内容 + 原因。这有助于日后回顾和改进文档。

## Boltz-2

Boltz-2 通过 PyPI 发布，`pip install boltz[cuda]` 一键安装全部依赖。**无需编译器、无需补丁。** 唯一需要手动处理的是权重下载（~5.9 GB）和缓存位置。

关键点：

- **必须用独立 conda 环境**（python=3.11，不能 clone base）——它自动拉取 torch 2.12.0+cu130，与 `protein_design` 的 torch 2.8.0 冲突
- **环境必须放数据盘**（完整环境 8-10 GB），通过 symlink 实现
- pip 安装**必须用阿里云镜像**加速
- 权重来源 HuggingFace，**本地下载需要美国节点的 VPN**。Agent 执行下载前应通过 `curl -s https://ipinfo.io/json` 自行检测 IP 是否在美国，不是则提醒用户切换
- 因为已经有一个conda虚拟环境了，加上base环境，再加上各种缓存，很容易导致**系统盘无可用空间**。记住，**已经装好**的各种东西的缓存可以删除。

### 创建独立环境并移到数据盘

```bash
conda create -n boltz python=3.11 -y
```

```bash
mv /root/miniconda3/envs/boltz /root/autodl-tmp/tools/boltz
```

```bash
ln -s /root/autodl-tmp/tools/boltz /root/miniconda3/envs/boltz
```

### 安装 boltz

```bash
conda activate boltz
```

```bash
pip install boltz[cuda] -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

> `pip install boltz[cuda]` 自动拉取 torch 2.12.0+cu130、triton、cuequivariance、rdkit、pytorch-lightning 等全套依赖，不需要手动装任何东西。`[cuda]` 必须加，缺少它则三个 cuequivariance CUDA ops 包不会安装，模型推理速度极慢。

### 配置模型缓存（symlink 到数据盘）

```bash
mkdir -p /root/autodl-tmp/weights/boltz
```

```bash
rm -rf ~/.boltz
```

```bash
ln -sf /root/autodl-tmp/weights/boltz ~/.boltz
```

> Boltz-2 默认将权重下载到 `~/.boltz/`（系统盘）。symlink 后所有下载自动落到数据盘。

### 本地下载权重（需要美国节点的 VPN）

> Agent 必须先通过 `curl -s https://ipinfo.io/json` 检测 IP 是否在美国，不是则向用户提问确认。

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

权重文件说明：

| 文件                 | 大小      | 用途                          |
| ------------------ | ------- | --------------------------- |
| `boltz2_conf.ckpt` | 2.0 GB  | 结构预测主模型                     |
| `boltz2_aff.ckpt`  | 2.2 GB  | 亲和力预测模型                     |
| `mols.tar`（解压后）    | ~1.8 GB | CCD 小分子字典（45,227 个 .pkl 文件） |

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

> mols/ 有 45,227 个小文件，`scp -r` 上传极慢，务必传 `mols.tar` 后在云端解压。

### 验证

```bash
ssh("conda activate boltz && python -c \"import boltz; print('Boltz version:', boltz.__version__)\"")
```

```bash
ssh("conda activate boltz && python -c \"from boltz.model.models.boltz2 import Boltz2; print('Boltz2 model OK')\"")
```

```bash
ssh("conda activate boltz && python -c \"import torch; print('PyTorch', torch.__version__, 'CUDA', torch.version.cuda)\"")
```

预期输出 `PyTorch 2.12.0 CUDA 13.0`。在无 GPU 模式下 `torch.cuda.is_available()` 返回 `False` 是正常的。

### 有 GPU 时运行测试

```bash
mkdir -p /root/autodl-tmp/test_outputs
```

```bash
echo ">test" > /root/autodl-tmp/test.fasta
echo "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG" >> /root/autodl-tmp/test.fasta
```

```bash
conda activate boltz && boltz predict \
    --model boltz2 \
    --cache /root/autodl-tmp/weights/boltz \
    --out_dir /root/autodl-tmp/test_outputs \
    --sampling_steps 50 \
    --diffusion_samples 1 \
    /root/autodl-tmp/test.fasta
```
