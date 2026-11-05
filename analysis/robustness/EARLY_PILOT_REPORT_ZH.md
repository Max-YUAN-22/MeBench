# 新增实验 K–M：实际结果与使用边界

三项分析已完成并写入当前论文。正文仍为第 2–11 页，标题摘要第 1 页，参考文献第 12–13 页；原附录 A–J 保留，新增 K–M 为 S11–S16。整份 PDF 共 29 页。七张原图和 Results 3.1–3.4 保留，原主表 36 个数值不变。正文只更新 Discussion 的附录指引和 Limitations 中与新证据直接相关的两处表述。

## A / Appendix K：第二自动 judge 的敏感性

从 Task 2/3 共 5,112 条记录中抽取 120 条：每个任务 60 条，每个系统/任务 10 条。按原 mechanism、mediator、causal role、chain 的联合状态分层，共 73 个非空层；层内无放回随机抽样，种子 20261105。因为特意覆盖错误状态，不能把原始样本比例直接当成全体比例，使用已知抽样概率的倒数加权，并同时公开原始样本结果。

实际第二 judge 配置为 **gpt-6.1-terra**，通过无对话历史继承的独立 Codex agent 完成六批真实语义重评。盲评输入不含被评系统、运行编号、unit ID 或原判断，只提供匿名输入、回答、理由、原参考机制及原五维 rubric。没有外部模型 API 凭据，因此这不是原实验供应商 API 的复跑，也不是人工实验。对部分原判断而言，它仍属于 GPT 模型家族；精确服务 checkpoint、温度未独立记录。这些限制均已写入论文。

| 指标（抽样概率加权） | Task 2 | Task 3 |
|---|---:|---:|
| Full-chain 总体一致率 | 91.0% | 59.9% |
| Cohen’s kappa | 0.772 | 0.284 |
| 原 full-chain pass rate | 76.8% | 60.6% |
| 新 judge 的估计 pass rate | 69.7% | 21.8% |
| 估计变化 | −7.1 pp | −38.9 pp |
| Full-chain 点排名 Spearman | 0.600 | −0.580 |

五维分别的一致率和 kappa、每个系统的变化以及两个可追溯分歧示例均在 Appendix K。Task 3 最大分歧位于 intervention–outcome link：加权一致率仅 36.8%。这可能涉及对依赖遗漏、方法匹配、作用方向的不同执行尺度，需要专家裁决，不能据此断言新 judge 一定正确。

**可写：** 当前评分对 judge 选择存在敏感性，尤其 Task 3；需要进一步明确方法恢复、兼容干预与机制正确性之间的边界。**不可写：** 自动 judge 已被生物学验证，或者排名已得到稳健确认。每个系统/任务仅 10 条，若干层只有一个抽样观测，新排名只是探索性的加权点估计，不替换主表，也没有可靠的设计方差区间。

公开材料包括盲评包、rubric、原始 120 条重评、身份映射、抽样概率、协议和文件哈希。复算脚本读取已存档重评，不会声称重新调用模型。

## B / Appendix L：Task 3 的 accepted sets

直接读取冻结标注，没有新增生物标签。

- 20 个单位中，19 个 accepted set 的基数为 1；1 个基数为 2，canonicalization 后仍如此。
- 多标签单位是 `T3VP_0003`：TWIST1–HOXD10，miR-10b 被干预，方向 up，标签为 `inhibition` 与 `sponge_inhibition`。
- 现有 480 条回答中，没有任何一条仅因第二个 accepted label 而被救回；set 与首个标签的匹配结果相同。首标签只用于任意 singleton 敏感性比较，不被当作唯一生物真值。
- 全部模型合计：canonical alias 使 100 条 literal mismatch 被接受；已披露的 RNA amendment 再使 42 条被接受。
- 六个系统的 literal / canonical / amended 准确率、按基数分组表现、全部 20 个 accepted sets 均已公开。

| 系统 | Literal set | Canonical set | Amended set |
|---|---:|---:|---:|
| GPT | 35.0% | 60.0% | 70.0% |
| Claude | 30.0% | 45.0% | 45.0% |
| Gemini | 30.0% | 48.8% | 63.8% |
| GLM | 41.3% | 63.8% | 63.8% |
| Grok | 25.0% | 40.0% | 60.0% |
| Biomni | 55.0% | 83.8% | 91.3% |

**解释边界：** 已标注多解不等于穷尽所有生物学可行干预；singleton set 也不证明逆映射唯一。当前 exact–accepted 差距主要来自归一化及已披露评分修正，不能都归因于多解。基数为 2 的组只有一个生物单位，每个系统四次运行不能视作四个独立实验。

## C / Appendix M：pair 与来源聚类 bootstrap

Task 2 的 168 个 pair、193 个 intervention units。进行 20,000 次 pair bootstrap；每次抽中的 pair 保留全部单位和四次运行，六个系统共用相同抽样。主指标仍是原发表口径的 unit-weighted joint balanced accuracy，不悄悄改为 pair 等权。

来源标识覆盖全部 193 个单位。合并 DOI/PMCID 同文别名后有 36 篇论文；为避免跨来源 pair 被拆开，将共享 pair 连接的论文合并为 31 个不重叠来源 component，再进行 20,000 次 bootstrap。最大 component 包含 99 个单位和 99 个 pair，分别占 51.3% 和 58.9%，因此来源独立性非常有限。

| 系统 | 原 joint BAcc | Pair 95% CI | 来源 component 95% CI |
|---|---:|---:|---:|
| GPT | 78.3% | [68.9, 86.8] | [55.1, 91.0] |
| Claude | 74.2% | [64.6, 83.3] | [49.2, 88.0] |
| Gemini | 72.8% | [63.6, 81.4] | [51.6, 85.4] |
| GLM | 52.8% | [46.3, 59.5] | [28.9, 64.7] |
| Grok | 73.7% | [64.5, 82.2] | [48.3, 87.2] |
| Biomni | 68.5% | [60.6, 76.4] | [43.5, 81.3] |

GPT–Claude 配对差值为 **+4.06 pp**。Pair 区间 **[+0.19, +8.61]**；来源 component 区间 **[−1.36, +14.32]**。后一项跨零，因此不能声称在两种依赖假设下都确认 GPT 优势。原六系统完整严格排序分别在 36.35% / 18.96% 的重抽样中保留。GPT 的第一名份额为 97.97% / 88.54%（并列平分），这些是重抽样描述频率，不是后验概率或假设检验 p 值。

新增矢量 Figure S3 同时显示两类区间，图例置于绘图区外。来源 component 清单、全部重抽样估计、六系统排名和配对差值可逐项核查。区间条件于原标签、原 judge 及四次已观测运行，不包含 judge 不确定性。

## 复现与审核状态

本地仓库 `scripts/` 提供：

```
python3 scripts/prepare_judge_sample.py --output judge_sample_regenerated
python3 scripts/analyze_judge_robustness.py --output judge_metrics_output
python3 scripts/analyze_task3_accepted_sets.py --output robustness_output
python3 scripts/cluster_bootstrap.py --output robustness_output
python3 scripts/render_cluster_figure.py --analysis robustness_output/cluster_bootstrap_analysis.json --output paper/revision/figs
```

后两个统计/绘图入口需要 `scripts/requirements_robustness.txt` 中的依赖；judge 汇总和 accepted-set 分析使用 Python 标准库与发布评分代码。前三项分别是重建抽样、重算存档 judge 结果、重算 accepted sets，均不调用外部模型。

已检查：固定抽样及盲评包完全一致；移植脚本结果在浮点精度内一致；全部 bootstrap 数组重现；Task 3 480 条接受判断与主表完全一致；原始 603 个运行/评分文件未改；9,216 条记录审计及主表 36 格复算再次通过。修改前后 PDF 前九页逐像素相同。正文与新增页均已渲染检查，参考文献从 12 页开始。

未推送或迁移。仍需作者审阅新结果、judge 执行边界及原指标口径；迁往 DREAM-virtual-cell 前必须再次取得作者明确确认。
