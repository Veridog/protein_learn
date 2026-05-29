# Exp0.3 — 工具对比：ESMFold vs Boltz-2

## 目标

在同一批序列上对比 ESMFold 和 Boltz-2 的预测结果，建立对两个工具的直觉：它们的精度、速度、一致性和适用场景。

## 背景

你的管线里有两个结构验证工具：

- **ESMFold**：基于语言模型的单序列结构预测（GPU，~30s/蛋白）
- **Boltz-2**：基于扩散的结构预测，支持多链和配体（GPU，但更重）

它们的预测不完全一致。了解差异才能知道在不同的设计任务中该信任哪个。

## 实验设计

### 输入

**输入数据**：来自 Exp0.1 的 100 个生成 backbone + 对应的 MPNN 序列（路径 `../Exp0.1:UnconditionalGeneration/outputs/`）。选取 20-30 个代表性样本（避免浪费时间）。

### 对比维度

| 维度            | 测量方法                             |
| ------------- | -------------------------------- |
| **pLDDT 一致性** | 同一条序列，两个工具预测的每个残基 pLDDT 的相关性     |
| **结构一致性**     | 两个预测结构的 Cα RMSD（TM-align 或直接叠加）  |
| **PAE 一致性**   | PAE 矩阵的整体相关性                     |
| **可设计性判断**    | 以哪个为标准来判断 "该 backbone 是否可被设计" 不同 |
| **速度**        | 单次推理时间                           |
| **内存**        | 峰值显存占用                           |

### 关键问题

1. 两个工具对同一序列给出的 pLDDT 差多少？是否系统性偏差？
2. 两者的结构预测 RMSD 有多大？差异集中在环区还是核心二级结构？
3. 如果用 "pLDDT > 80" 作为筛选标准，两个工具筛选出的设计重叠率多高？
4. 对小蛋白（<100aa）vs 大蛋白（>200aa），表现差异如何？
5. Boltz-2 能否处理 ESMFold 无法处理的情况（例如多链、含非标准残基）？

## 任务

1. 从 Exp0.1 输出中挑选 30 个长度不同的 backbone
2. 对每个 backbone，选 1 个最优 MPNN 序列
3. 分别用 ESMFold 和 Boltz-2 预测结构
4. 提取 pLDDT、PAE、结构坐标
5. 计算对比指标并可视化
6. 写一个简短报告：什么时候用哪个工具？

## 期望产出

- `outputs/plddt_scatter.png`：pLDDT 散点图（ESMFold vs Boltz-2）
- `outputs/rmsd_distribution.png`：结构 RMSD 分布
- `outputs/comparison.csv`：所有对比数据
- `outputs/report.md`：结论性总结（< 1 页）

## 技术要点

### ESMFold 推理

```python
import esm
model = esm.pretrained.esmfold_v1()
model = model.eval().cuda()
with torch.no_grad():
    output = model.infer_pdbs([seq1, seq2, ...])
# output 包含 pdb, plddt, pae
```

### Boltz-2 推理

```bash
# 对每条序列生成 YAML input
cat > input.yaml << EOF
version: 1
sequences:
  - protein:
      id: A
      sequence: <序列>
      msa: empty
EOF
boltz predict input.yaml --out_dir ./output --output_format pdb
```

或通过 Python API 直接调用。

## 参考

- ESMFold: Lin et al. (2023) "Evolutionary-scale prediction of atomic-level protein structure with a language model"
- Boltz-2: 使用 Python API 内省 `boltz.model.models.boltz2.Boltz2` 获取置信度输出
