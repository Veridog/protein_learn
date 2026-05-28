# AutoDL 拷贝实例已知问题

## 现象

在 AutoDL 上执行"拷贝实例"操作后，以下内容会丢失：

| 丢失项                               | 影响                                                |
| --------------------------------- | ------------------------------------------------- |
| `pip install -e .` 产生的 egg-link   | `rfdiffusion`、`fair-esm` 等 develop 安装的模块无法 import |
| `python setup.py install` 产生的 egg | `se3_transformer` 模块丢失                            |
| 手动创建到 site-packages 的 symlink     | `openfold/openfold` 符号链接消失                        |
| 对 site-packages 中文件的直接修改          | ESM 补丁（trunk.py / esmfold.py / pretrained.py）全部还原 |
| conda 环境下的 `pip install` 的包       | 部分包丢失（如 `e3nn`、`opt_einsum`、`wandb` 等），并非全部       |

## 根因分析

AutoDL 的拷贝实例机制可能是基于文件系统快照或镜像复制。写时复制（CoW）方案下：

- 磁盘上持久化的文件（如 `/root/autodl-tmp/` 下的代码和权重）能完整保留
- 但运行时产生的链接（symlink、egg-link）和环境元数据可能因 inode 级别复制策略而丢失

## 修复脚本（拷贝实例后执行）

```bash
# 1. OpenFold symlink
source /root/miniconda3/etc/profile.d/conda.sh && conda activate protein_design
ln -sf /root/autodl-tmp/tools/openfold/openfold $(python -c "import site; print(site.getsitepackages()[0])")/openfold

# 2. SE3Transformer
cd /root/autodl-tmp/tools/rfdiffusion/env/SE3Transformer
python setup.py install

# 3. RFDiffusion egg-link
cd /root/autodl-tmp/tools/rfdiffusion
pip install -e .

# 4. ESM patches（见 AGENTS.md 步骤）
# trunk.py: dataclass import + mutable default
# esmfold.py: dataclass import + mutable default
# pretrained.py: 本地加载权重 + weights_only=False

# 5. 模型权重 symlink
cd /root/autodl-tmp/tools/rfdiffusion
mkdir -p models && for f in *.pt; do ln -sf ../$f models/$f; done
```

## 时间戳

2026-05-28：首次发现并记录
