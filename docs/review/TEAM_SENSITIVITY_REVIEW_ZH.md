# 作者补充实验的接收、复核与论文整合

已接收桌面 sensitivity 文件夹的 83 个文件，包含抽样设计、21 批重判包及其原始回复、解析判断、L/M 计算脚本和结果。桌面源目录未修改；本地交付副本位于 team_sensitivity。审核不调用任何模型 API。

## 核验通过的结果

1. **K：** 360 条 Task 2、480 条 Task 3 manifest 中的原五维评分和 chain 均逐条对上当前冻结 MASTER。固定种子 20261017 重建的 Task 2 抽样清单与所提供设计完全一致。358/360 条 Task 2、480/480 条 Task 3 有有效新判断；全部 838 条解析结果与存档原始回复一致。
2. **L：** 按发布评分路径复跑，结果 JSON 与提供文件完全一致；另用前轮独立的原生 CSV 分析交叉核对 pooled / cardinality 接受率。仍是 19 个 singleton set、1 个双标签 set；没有记录只被第二标签额外接受。
3. **M：** 原脚本复跑，JSON 与提供文件完全一致。修正排名统计后，所有 point estimates、置信区间、配对差值及 source-level 结果均不变。所提供 GSE/DOI 分组和前轮 connected-source 分组，在这批数据上形成完全相同的 31 个 pair 分区。

## K 的主要数值

| Full-chain 指标 | Task 2（富集样本） | Task 3（全量） |
|---|---:|---:|
| 有效数 / 设计数 | 358 / 360 | 480 / 480 |
| Agreement | 96.4% | 89.8% |
| Cohen’s kappa | 0.927 | 0.783 |
| Original pass rate | 50.0% | 60.6% |
| Gemini pass rate | 52.5% | 64.2% |
| 变化 | +2.5 pp | +3.5 pp |
| Fail→pass / pass→fail | 11 / 2 | 33 / 16 |

Task 2 缺失记录：`T2U_0147@Grok-4.6@run4`（原 chain=1）和 `T2U_0150@Claude-Sonnet-5.5@run2`（原 chain=0）。排除它们，不补为失败，也不在本轮重新调用模型。

## 不能原样采用的说法与代码修正

### 1. 这次 Gemini 不是严格的系统身份盲评

实际 packet 的行号是 `unit_id@system@run`，明确暴露模型名称。原五维标签没有提供，但不能把 rubric 中的 “blinded adjudicator” 一句当作真正完成了身份遮蔽。

实际 packet 的列仅为 reasoning 与机制、mediator type/entity、topology、evidence-chain 五个参考字段。原始输入、预测答案不是独立列；部分回答自身重复了这些信息。不能把这次比较表述成已严格控制全部信息、只替换 judge。提供脚本使用相同指令前缀，但本目录未包含原 serving 脚本，无法独立验证其与原始 serving prompt 逐字节一致。

### 2. Task 2 的 +2.5 pp 是富集样本变化

30 pass / 30 fail 的人为配额使水平约为 50%；失败层又按不同轴选取，缺少可用的逐记录纳入概率。因此这不是总体通过率的 +2.5 pp，也不能用来支持总体排名。Task 3 全枚举的变化可直接描述当前任务总体。

### 3. Kendall 不能比较两份系统编号排列

所提供 `tau_b` 函数未处理 ties，且输入是两份排序列表中的系统编号，不是按同一系统对齐的分数或 rank。修正为对齐系统、保留 ties 的 Kendall tau-b 后：

- Task 3：**0.643**，替代提供文本中的 **0.333**。
- 原 judge 下 Claude/GLM 并列 4.5；新 judge 下 GPT/GLM 并列 2.5。不能强行列成无并列的第 2、3 名。
- 变化涉及中段排序，不只是 GPT/Gemini 首二互换。

### 4. M 的相邻翻转计数漏计

原脚本只有两个模型在某次重抽样排序中仍相邻时才计入倒置，漏掉已被第三个模型隔开的倒置。修正为每次直接比较同一对模型，同时统一 ties 的规则：

| Pair 等权统计 | 原报告 | 修正后 |
|---|---:|---:|
| Chain 完整严格顺序复现 | 53.5% | 52.76% |
| Joint 完整严格顺序复现 | 48.8% | 48.46% |
| Chain mean Kendall | 0.749 | 0.9242（正确 tau-b） |
| Joint mean Kendall | 0.756 | 0.9206（正确 tau-b） |
| Gemini 越过 Grok，chain | 22.6% | 28.70% |
| Gemini 越过 Grok，joint | 34.3% | 40.82% |

第一名份额并列平分后，GPT 为 99.94%（chain）／99.87%（joint）。以上都是重抽样描述频率，不是后验概率或普适排名保证；“published order” 在原脚本实际指 pair 等权次级估计的顺序，不是主表 joint BAcc 的完整顺序。

### 5. 不宜直接宣布 self-preference

Task 2 中 Gemini 原失败回答的 fail→pass 为 7/30，其他系统为 4/149；Task 3 为 6/25 与 27/164。这是系统相关的宽松判断信号。案例组成不同，且系统身份可见，不能从这些比例单独确证因果上的自偏好。论文按描述性关联报告。

### 6. Accepted-set 不等于已经穷尽生物学答案

14 个 entity/direction 组合在这个有限集合内没有冲突，只说明标签可由有限查找表复现，不证明生物学逆映射唯一。未来应采用 entity/direction 与 source 的留出评估，并评估解释以排查查表捷径。严格匹配至 accepted-set 的 142 条提升来自 100 条 canonical alias 与 42 条 RNA amendment，不是第二标签的多解救回。

## 与前轮独立-agent pilot 的关系

前轮 120 条 gpt-6.1-terra pilot 保留，未因结果不利而删除。其输入显式提供原问题、预测和 task-specific link，且系统身份被遮蔽；新 Gemini 包的显式字段不同、系统身份可见。因此两轮同时改变 judge 与信息接口，不能直接解释成纯 judge 的对照效应。Task 3 的 60 个 pilot cases 全部存在于新全枚举中，但样本重合仍无法消除接口混杂。

当前论文 K 以作者的 840 条设计为主要 archived reassessment，公开前轮 pilot 和两者适用范围。L 保留独立核验的完整 accepted sets 并增加有限查找结构的边界。M 同时报主表 joint BAcc 的 unit-weighted bootstrap 与作者的 pair 等权 chain/joint 次级指标，不把不同 estimand 混为一谈。

## 文件与调用安全

交付副本的 `run_K_rejudge.py` 已移除硬编码 API key 回退值及固定 relay endpoint，改为显式环境变量；原目录未动。本次没有 API 调用、GitHub 推送或仓库迁移。

`reviewed/team_judge_audit.json`、逐条 TSV、`M_CORRECTED_RANKING.json` 和 `verification_report.json` 是本次核验的派生结果；原 outputs/HTML 保留作作者提供的存档，其中原排名统计未被悄悄覆盖。论文应引用 corrected/reviewed 结果。

## 当前稿件

标题摘要为第 1 页，正文结束于第 11 页，参考文献第 12–13 页，附录 S1–S16，总计 29 页。七张原图、Results 3.1–3.4、主表 36 个数字保留。桌面原稿未改。迁往 DREAM-virtual-cell 前仍须作者明确确认。
