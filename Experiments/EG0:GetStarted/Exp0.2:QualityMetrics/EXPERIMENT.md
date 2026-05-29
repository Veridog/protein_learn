# Exp0.2 — 质量指标：理解与可视化

## 目标

学习从 RfDiffusion / ProteinMPNN / ESMFold 输出中提取关键质量指标，建立筛选直觉。这是后续 **65 个实验的通用基础能力**。

## 背景

无条件生成跑出来后，你会得到：

| 来源              | 产物                      | 关键文件             |
| --------------- | ----------------------- | ---------------- |
| RfDiffusion     | backbone PDB + metadata | `*.pdb`, `*.trb` |
| ProteinMPNN     | 序列 + scores             | `*.fa`, `seqs/`  |
| ESMFold/Boltz-2 | 预测结构 + 置信度              | `*.pdb`, `*.npz` |

**输入数据**：本实验读取 Exp0.1 的输出，路径为 `../Exp0.1:UnconditionalGeneration/outputs/`。

你需要能够从中提取并判断：

## 质量指标一览

### RfDiffusion 自评指标（在 `.trb` 文件中）

| 指标                | 含义                                     | 好的范围  |
| ----------------- | -------------------------------------- | ----- |
| `scRMSD`          | self-consistency RMSD：扩散轨迹终点 vs AF2 预测 | < 2 Å |
| `plddt`           | 平均 pLDDT（AF2 预测）                       | > 80  |
| `pae_interaction` | 链间 PAE（binder 设计时）                     | < 10  |
| `rmsd`            | binder RMSD（binder 设计时）                | < 2 Å |

### ESMFold / Boltz-2 指标

| 指标                             | 含义           | 好的范围              |
| ------------------------------ | ------------ | ----------------- |
| `pLDDT`                        | 每个残基的预测置信度   | > 80（平均），> 70（最低） |
| `PAE`（predicted aligned error） | 残基对之间的位置误差估计 | 对角线带状 < 5         |
| `iPAE` / `pae_interaction`     | 链间 PAE       | < 10              |

### 结构几何指标（从 PDB 计算）

| 指标                                  | 含义               | 好的范围                 |
| ----------------------------------- | ---------------- | -------------------- |
| Rg（radius of gyration）              | 结构紧凑度            | ~ 2.5 × N^0.34（天然蛋白） |
| 接触数（contacts）                       | 残基间 8Å 以内的 Cβ 对数 | 与长度正相关               |
| 疏水表面积                               | 暴露的非极性面积         | 不应过大（避免聚集）           |
| SAP（spatial aggregation propensity） | 聚集倾向             | < 45                 |

## 任务

1. **解析 `.trb` 文件**：RFdiffusion 的每个输出 PDB 旁边都有一个 `.trb` 文件（pickle 格式）。写代码读取它，打印所有键和关键值。

2. **从 ESMFold 输出提取 pLDDT 和 PAE**：ESMFold 的 `infer_pdb()` 除了 PDB 字符串外，也能返回 pLDDT 数组和 PAE 矩阵。写代码提取它们。

3. **计算结构几何指标**：给定一个 PDB 文件，写代码计算：
   
   - 半径 of gyration（Rg = sqrt(1/N * Σ(r_i - r_center)^2)）
   - 接触数（Cβ-Cβ 距离 < 8Å）

4. **批量评估 Exp0.1 的输出**：用以上工具分析你在 Exp0.1 生成的所有设计，输出汇总表格和分布图。

5. **建立筛选阈值**：基于分布，设定合理的通过/淘汰标准。

## 期望产出

- 本目录下的 `metrics.py`：可复用的 Python 模块，包含上述所有提取函数
- `outputs/evaluation_report.csv`：对 Exp0.1 所有设计的指标汇总
- `outputs/distributions.png`（或类似）：关键指标分布图
- 对"什么是好设计"形成直觉

## 参考

- RFdiffusion 论文 Fig. S3-S5 展示了典型的质量指标分布
- Bennett et al. (2023) 定义了 binder 筛选标准：pAE_interaction < 10, pLDDT > 85, ΔΔG < -30
