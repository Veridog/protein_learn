# 🧬 蛋白质设计任务大全：从入门到精通

> 基于管线：`RFDiffusion → ProteinMPNN → ESMFold/Boltz-2 → ESM`

---

## 📊 难度标尺

| 级别    | 含义  | 标志                          |
| ----- | --- | --------------------------- |
| ⭐     | 入门  | 改一行参数就能跑，成功率 >70%           |
| ⭐⭐    | 初级  | 需要理解 contig 语法，成功率 30-70%   |
| ⭐⭐⭐   | 中级  | 需要组合多个功能或自定义配置文件，成功率 5-30%  |
| ⭐⭐⭐⭐  | 高级  | 需要写新代码/脚本，或需要特殊工具版本，成功率 <5% |
| ⭐⭐⭐⭐⭐ | 专家  | 前沿课题，论文级难度，需要大量实验验证         |

---

## 一、Binder Design（蛋白质-蛋白质结合物设计）🫂

这是 RFdiffusion **最成熟**的条件生成功能，Nature 2023 的明星应用。

| #   | 任务                     | 描述                                        | 难度    | 关键参数                                                  |
| --- | ---------------------- | ----------------------------------------- | ----- | ----------------------------------------------------- |
| 1   | **基础 Binder 设计**       | 给定靶蛋白 + hotspot 残基，生成 de novo 结合蛋白        | ⭐⭐    | `ppi.hotspot_res`, `contigmap.contigs=[A1-N/0 L1-L2]` |
| 2   | **β-strand 配对 Binder** | 强制 binder 与靶标的 edge β-strand 形成配对 β-sheet | ⭐⭐⭐   | `Complex_beta` 权重 + 自定义 conditioning tensor           |
| 3   | **柔性肽段 Binder**        | 靶标只有二级结构信息，无 3D 坐标（Fold Conditioning）     | ⭐⭐⭐   | `contigmap.contigs=[A1-N/0 L1-L2]`, target 仅需二级结构指定   |
| 4   | **多表位 Binder**         | 同时靶向同一蛋白的多个不相邻位点                          | ⭐⭐⭐   | 多个 hotspot 组合 + 多段 contig                             |
| 5   | **部分固定 Binder**        | 已有部分结合结构（如已知 CDR），只设计其余部分                 | ⭐⭐⭐   | motif scaffolding + binder 混合 contig                  |
| 6   | **多链靶标 Binder**        | 靶标是多聚体或复合物（如 spike trimer）                | ⭐⭐⭐   | 多链 target PDB + hotspot 跨链                            |
| 7   | **膜蛋白 Binder**         | 靶向跨膜蛋白（如 GPCR）的胞外区域                       | ⭐⭐⭐⭐  | 需要膜蛋白结构模型，成功率低                                        |
| 8   | **正交 Binder 组**        | 设计多个互不交叉反应的 binder 组（如正交信号通路）             | ⭐⭐⭐⭐⭐ | 需要多轮设计 + 特异性筛选                                        |

### 管线步骤

```
RFDiffusion（生成 backbone）→ ProteinMPNN（序列设计）→ Boltz-2（验证结合）
→ 筛选：iPAE < 10, pLDDT > 85, binder RMSD < 2Å
```

---

## 二、Motif Scaffolding（功能基序支架）🏗️

将已知功能位点（催化残基、结合位点）嵌入全新的蛋白骨架中。RFdiffusion 在此任务上显著超越传统方法。

| #   | 任务                        | 描述                         | 难度    | 关键参数                             |
| --- | ------------------------- | -------------------------- | ----- | -------------------------------- |
| 9   | **单体 Motif 支架**           | 提取 PDB 中一段功能残基，生成不同骨架包裹它   | ⭐⭐    | `contigmap.contigs=[L1/Ax-y/L2]` |
| 10  | **多段不连续 Motif 支架**        | 多个功能片段被不同长度的 linker 隔开     | ⭐⭐⭐   | 复杂 contig：`[L1/Ax-y/L2/Ba-b/L3]` |
| 11  | **Active Site 精确支架（小基序）** | 仅 3-5 个残基的极小催化位点           | ⭐⭐⭐⭐  | 需要 `Complex_active_site` 模型      |
| 12  | **含辅助因子的支架**              | 支架需同时容纳金属离子、辅因子（NAD、ATP 等） | ⭐⭐⭐⭐  | 需要 RFdiffusionAA                 |
| 13  | **含底物分子的支架**              | 扩散过程中底物分子存在，避免空间冲突         | ⭐⭐⭐⭐  | 需要 RFdiffusionAA 或 RFdiffusion3  |
| 14  | **条件性折叠支架**               | 只有特定条件下（pH、配体结合）才折叠的支架     | ⭐⭐⭐⭐⭐ | 需要多状态设计                          |

### 管线步骤

```
从 PDB 提取 motif → RFdiffusion 支架生成 → ProteinMPNN 序列设计
→ Boltz-2 验证 motif 恢复精度（RMSD < 1Å）
```

---

## 三、Enzyme Design（酶设计）⚗️

蛋白质设计的"圣杯" — 难度极高，但回报巨大。

| #   | 任务             | 描述                            | 难度    | 关键工具                                             |
| --- | -------------- | ----------------------------- | ----- | ------------------------------------------------ |
| 15  | **环区重构酶设计**    | 保留天然酶的大部分，仅替换活性位点环区           | ⭐⭐⭐   | RFdiffusion partial diffusion                    |
| 16  | **酶活性位点支架**    | 将已知催化 motif 嵌入完全不同的 scaffold  | ⭐⭐⭐⭐  | RFdiffusion motif scaffolding + `active_site` 模型 |
| 17  | **全原子酶设计**     | 底物 + 辅因子 + 催化残基一起扩散           | ⭐⭐⭐⭐  | RFdiffusionAA + LigandMPNN                       |
| 18  | **金属酶设计**      | 设计含金属离子（Zn²⁺、Fe²⁺、Cu²⁺等）的活性位点 | ⭐⭐⭐⭐  | RFdiffusion3 + LigandMPNN                        |
| 19  | **新化学反应催化酶**   | 催化自然界不存在的反应                   | ⭐⭐⭐⭐⭐ | RFdiffusion2/3 + 量子化学过渡态                         |
| 20  | **人工金属酶（ArM）** | 将合成催化剂（如 Ru 配合物）嵌入 de novo 蛋白 | ⭐⭐⭐⭐⭐ | RFdiffusion + Rosetta FastDesign + 定向进化          |
| 21  | **多步级联酶**      | 设计多个酶串联完成多步反应                 | ⭐⭐⭐⭐⭐ | 需多个设计 + 底物通道设计                                   |

### 酶设计特别注意事项

- **成功率极低**：原始 RFdiffusion 酶设计率 ~6.5%，EnhancedMPNN 可提到 ~17.6%
- **必须用 LigandMPNN**（而非普通 ProteinMPNN）设计含配体位点的序列
- **推荐先做环区重构**，再逐步挑战全 de novo

---

## 四、Symmetric Oligomer Design（对称寡聚体设计）🔷

RFdiffusion 原生支持，可生成环状、二面体、四面体对称结构。

| #   | 任务                         | 描述                                 | 难度    | 关键参数                                                  |
| --- | -------------------------- | ---------------------------------- | ----- | ----------------------------------------------------- |
| 22  | **Cyclic 寡聚体（环状 C2-Cn）**   | 设计自组装的环状蛋白复合物                      | ⭐⭐    | `--config-name symmetry`, `inference.symmetry=cyclic` |
| 23  | **Dihedral 寡聚体（二面体 Dn）**   | 两组环对称组合                            | ⭐⭐    | `inference.symmetry=dihedral`                         |
| 24  | **Tetrahedral 寡聚体（四面体 T）** | 12 个亚基的四面体对称                       | ⭐⭐    | `inference.symmetry=tetrahedral`                      |
| 25  | **对称 Motif 支架**            | 在对称寡聚体上精确定位功能基序                    | ⭐⭐⭐⭐  | motif 需先按对称轴预处理                                       |
| 26  | **蛋白纳米笼（Nanocage）**        | 设计中空蛋白笼（如病毒样颗粒）                    | ⭐⭐⭐⭐⭐ | 需参数化几何 + RFdiffusion                                  |
| 27  | **准对称大组装体**                | 1-组分准对称组装（hexon + penton），直径 >68nm | ⭐⭐⭐⭐⭐ | 前沿论文级（Nature 2026）                                    |
| 28  | **两分组分蛋白笼**                | 两组不同蛋白共组装成笼                        | ⭐⭐⭐⭐⭐ | 需设计两个正交界面                                             |
| 29  | **pH 响应性纤维**               | 依赖 pH 自组装/解聚的蛋白纳米纤维                | ⭐⭐⭐⭐⭐ | 需埋藏多个组氨酸网络                                            |

---

## 五、Partial Diffusion（部分扩散 / 设计多样化）🔄

在已有设计上做局部改进，而不是从头生成。

| #   | 任务                       | 描述                        | 难度  | 关键参数                         |
| --- | ------------------------ | ------------------------- | --- | ---------------------------- |
| 30  | **Binder 亲和力优化**         | 已有 binder 基础上扩散多样化，筛选更强结合 | ⭐⭐  | `diffuser.parial_T`, 固定大部分结构 |
| 31  | **Binder 特异性改造**         | 保持对靶标结合，消除脱靶结合            | ⭐⭐⭐ | partial diffusion + 负选择      |
| 32  | **环区重设计**                | 仅重新设计蛋白质表面环区（如 CDR loops） | ⭐⭐  | contig 指定可扩散区域               |
| 33  | **多区域同时多样化**             | 多个不相邻的区域同时扩散              | ⭐⭐⭐ | 多段 contig + `inpaint_seq`    |
| 34  | **Fold Conditioning 扩散** | 给定拓扑约束下的多样化               | ⭐⭐⭐ | 二级结构 conditioning            |

---

## 六、Antibody & Nanobody Design（抗体设计）🛡️

蛋白质设计最活跃的应用领域之一。

| #   | 任务                        | 描述                          | 难度    | 关键工具                            |
| --- | ------------------------- | --------------------------- | ----- | ------------------------------- |
| 35  | **CDR 环重设计**              | 给定抗体框架，重新设计 CDR loops 提高亲和力 | ⭐⭐⭐   | Partial diffusion + ProteinMPNN |
| 36  | **De Novo 纳米抗体 (VHH) 设计** | 从零设计针对特定抗原表位的单域抗体           | ⭐⭐⭐⭐  | RFdiffusion binder + 框架模板       |
| 37  | **De Novo scFv 设计**       | 从头设计完整的单链抗体                 | ⭐⭐⭐⭐⭐ | 需要配对 VH-VL 设计                   |
| 38  | **双特异性抗体设计**              | 同时结合两个不同靶标的抗体               | ⭐⭐⭐⭐⭐ | 需要多靶标条件                         |
| 39  | **TCR（T 细胞受体）设计**         | 设计识别 pMHC 的 TCR             | ⭐⭐⭐⭐  | motif scaffolding + hotspot     |
| 40  | **多价中和抗体**                | 对称支架 + 多个结合域精确排列            | ⭐⭐⭐⭐  | symmetric motif scaffolding     |

---

## 七、Cyclic/Macrocyclic Peptide Design（环肽设计）🔗

RFpeptides（RFdiffusion 的环肽扩展，Rettie et al., 2025 发表）。

| #   | 任务               | 描述             | 难度   | 关键参数                                                |
| --- | ---------------- | -------------- | ---- | --------------------------------------------------- |
| 41  | **环肽单体设计**       | 生成可自折叠的环状肽     | ⭐⭐   | `inference.cyclic=True`, `inference.cyc_chains='a'` |
| 42  | **环肽 Binder 设计** | 设计靶向特定蛋白的环肽结合物 | ⭐⭐⭐  | cyclic + hotspot + binder contig                    |
| 43  | **多环肽设计**        | 多个环状链的设计       | ⭐⭐⭐  | `inference.cyc_chains='ab'` 等                       |
| 44  | **细胞穿透环肽**       | 兼具穿透性和结合性的环肽   | ⭐⭐⭐⭐ | 需细胞实验验证                                             |

---

## 八、Metal-Binding Protein Design（金属结合蛋白设计）🔩

| #   | 任务             | 描述                       | 难度    | 关键工具                                   |
| --- | -------------- | ------------------------ | ----- | -------------------------------------- |
| 45  | **简单金属结合位点设计** | 设计 His/Cys 配位的 Zn²⁺ 结合蛋白 | ⭐⭐⭐⭐  | symmetric motif scaffolding + 金属位点 PDB |
| 46  | **多金属簇设计**     | 铁硫簇、双金属中心等               | ⭐⭐⭐⭐⭐ | RFdiffusion2/3                         |
| 47  | **重金属结合肽**     | 环保修复用的 Cd²⁺、Cu²⁺ 结合肽     | ⭐⭐⭐   | Metalorian 等专用工具                       |
| 48  | **金属响应开关蛋白**   | 金属结合触发构象变化的蛋白            | ⭐⭐⭐⭐⭐ | 需多状态设计                                 |

---

## 九、Sequence-Only / Property-Focused Design（序列/性质优化）🔬

利用 ESM 模型进行性质预测和优化。

| #   | 任务            | 描述                    | 难度    | 关键工具                      |
| --- | ------------- | --------------------- | ----- | ------------------------- |
| 49  | **溶解度优化**     | 提高 de novo 蛋白的可溶性表达   | ⭐⭐    | ProteinMPNN + ESM logits  |
| 50  | **热稳定性优化**    | 提高 Tm 值               | ⭐⭐    | ESM 突变效应预测                |
| 51  | **免疫原性预测**    | 评估设计的 MHC 呈递潜力        | ⭐⭐    | ESM 嵌入 + 下游分类器            |
| 52  | **正交序列对设计**   | 设计互不交叉反应的同源蛋白对        | ⭐⭐⭐   | ProteinMPNN 多轮设计          |
| 53  | **条件性降解标签**   | 设计含 degron 的条件性不稳定性蛋白 | ⭐⭐⭐   | 序列设计 + 降解信号               |
| 54  | **翻译后修饰位点引入** | 引入磷酸化/糖基化/泛素化位点       | ⭐⭐⭐   | 结合序列约束的 ProteinMPNN       |
| 55  | **生物传感器蛋白**   | 配体结合产生可检测信号的蛋白        | ⭐⭐⭐⭐  | 构象变化 + 报告域融合              |
| 56  | **蛋白逻辑门**     | AND/OR/NOT 逻辑响应多个输入   | ⭐⭐⭐⭐⭐ | 多输入构象耦合设计                 |
| 57  | **荧光蛋白重设计**   | 改变激发/发射波长或亮度          | ⭐⭐⭐   | Partial diffusion + 发色团约束 |

---

## 十、Advanced & Emerging Tasks（前沿课题）🚀

| #   | 任务                  | 描述                       | 难度    | 来源                         |
| --- | ------------------- | ------------------------ | ----- | -------------------------- |
| 58  | **多状态蛋白设计**         | 可在两种折叠状态间切换的蛋白           | ⭐⭐⭐⭐⭐ | 前沿                         |
| 59  | **别构蛋白设计**          | 远处结合小分子调控活性位点的蛋白         | ⭐⭐⭐⭐⭐ | 前沿                         |
| 60  | **蛋白-DNA/RNA 结合设计** | 设计特异性结合核酸的蛋白             | ⭐⭐⭐⭐⭐ | 需核酸感知版扩散模型                 |
| 61  | **膜蛋白 de novo 设计**  | 设计跨膜螺旋蛋白                 | ⭐⭐⭐⭐⭐ | 前沿                         |
| 62  | **蛋白-小分子对接设计**      | 设计特异性结合药物小分子的蛋白          | ⭐⭐⭐⭐  | LigandMPNN + RFdiffusionAA |
| 63  | **疫苗免疫原设计**         | 设计能诱导特定抗体的免疫原（如 HIV Env） | ⭐⭐⭐⭐⭐ | 多表位呈现                      |
| 64  | **自组装 2D 晶格**       | 蛋白亚基排列成 2D 晶体            | ⭐⭐⭐⭐⭐ | 对称设计扩展                     |
| 65  | **蛋白基药物递送载体**       | 设计可控释放的药物载体蛋白笼           | ⭐⭐⭐⭐⭐ | 纳米笼 + 刺激响应                 |

---

## 🎯 推荐学习路径

根据你已完成**无条件生成**的情况，建议按以下顺序进阶：

```
1. ⭐⭐  基础 Binder 设计          ← 下一步建议
2. ⭐⭐  单体 Motif 支架
3. ⭐⭐  Cyclic 对称寡聚体
4. ⭐⭐  Partial Diffusion 环区重设计
5. ⭐⭐⭐ β-strand Binder / 柔性肽 Binder
6. ⭐⭐⭐ 多段 Motif 支架
7. ⭐⭐⭐⭐ 酶活性位点支架（环区重构先做）
8. ⭐⭐⭐⭐ 对称 Motif 支架
9. ⭐⭐⭐⭐ De Novo 纳米抗体
10. ⭐⭐⭐⭐⭐ 全 De Novo 酶设计
```

### 每个任务的标准验证管线

```
1. RFdiffusion → 生成 N 个 backbone（建议 N=100-1000）
2. ProteinMPNN → 每个 backbone 生成 1-8 个序列
3. ESMFold/Boltz-2 → 结构自洽性验证
4. 筛选 → pLDDT, RMSD, PAE, 接触数, 半径 of gyration
5. ESM → 功能/性质评估（溶解度、稳定性等）
```

---

## 📝 难度判定依据

| 因素                                             | 影响       |
| ---------------------------------------------- | -------- |
| RFdiffusion 原生支持                               | ⭐⭐（只改参数） |
| 需要组合多个 RFdiffusion 功能                          | ⭐⭐⭐      |
| 需要特殊模型（RFdiffusionAA, active_site, RFpeptides） | ⭐⭐⭐      |
| 需要写 Python 脚本预处理/后处理                           | ⭐⭐⭐      |
| 需要额外工具（LigandMPNN, Rosetta, 量子化学）              | ⭐⭐⭐⭐     |
| 实验成功率极低、领域前沿                                   | ⭐⭐⭐⭐⭐    |
| 需要迭代多轮设计-验证                                    | ⭐⭐⭐⭐+    |

---

## 📚 参考文献

1. Watson et al. (2023) "De novo design of protein structure and function with RFdiffusion" — *Nature*
2. Bennett et al. (2023) "Improving de novo protein binder design with deep learning" — *Nature Communications*
3. Rettie, Juergens, Adebomi et al. (2025) "Accurate de novo design of high-affinity protein-binding macrocycles using deep learning" — *Nature Chemical Biology*
4. Liu et al. (2024) "Improved protein binder design using β-pairing targeted RFdiffusion" — *Nature Communications*
5. Krishna et al. (2024) "Generalized biomolecular modeling and design with RoseTTAFold All-Atom" — *Science*
6. Shen et al. (2024) "De novo design of pH-responsive self-assembling helical protein filaments" — *Nature Nanotechnology*
7. Yeh et al. (2023) "De novo design of luciferases using deep learning" — *Nature*
8. Dauparas et al. (2022) "Robust deep learning-based protein sequence design using ProteinMPNN" — *Science*
