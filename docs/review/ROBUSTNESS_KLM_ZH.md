# 当前 K–M 的实验来源与结论

当前论文已整合作者新提供的 sensitivity 文件夹，并保留前轮独立-agent pilot。完整审计、代码修正和边界见《sensitivity核验说明.md》。正文 2–11 页、参考文献 12–13 页、附录 S1–S16；PDF 共 29 页。

| 附录 | 当前使用的证据 | 主要结果与解释 |
|---|---|---|
| K | 作者提供的 Gemini relay 重判：T2 360 条设计、358 条有效；T3 全量 480 条。另保留前轮 120 条独立-agent pilot | Gemini full-chain agreement 为 96.4% / 89.8%，kappa 0.927 / 0.783。T2 +2.5 pp 仅为富集样本变化；T3 +3.5 pp 为当前全量任务变化。正确的 T3 Kendall tau-b 为 0.643。 |
| L | 冻结 accepted sets，480 条原回答；两套实现交叉核验 | 19 个 singleton、1 个双标签；第二标签没有额外救回回答。Literal→accepted 提升是 100 条 aliases + 42 条 RNA amendment。 |
| M | 主表 joint BAcc 的 20,000 次 pair/source bootstrap；作者 pair 等权 chain/joint 的 10,000 次次级分析 | 不同 estimand 分开报告。主指标 GPT−Claude 为 +4.06 pp，来源区间 [−1.36,+14.32] 跨零。次级 chain/joint 配对差为 +3.1/+2.6 pp。修正了排名相关与漏计翻转，point/CI 不变。 |

Gemini 包的系统身份可见，原始输入与预测并非独立显式列；与前轮身份隐藏、显式输入更完整的 pilot 并非纯模型替换对照。两轮结论应解释为 judge/接口敏感性，而非生物学正确性的验证。两轮的包、判断、映射及协议都保留，可独立检查。

当前结果加强了 benchmark 的可审查性：既保留机制依赖、作用方向和终点正确性分离的研究价值，也明确了评分接口、有限逆推标签和来源集中对结论的限制。没有完成的人工验证和训练实验仍按未完成表述。

本地仓库除原复现入口外，新增：

```
python3 scripts/audit_team_sensitivity.py --root . --source sensitivity --output sensitivity/reviewed
python3 scripts/compute_M_corrected.py --root . --output sensitivity/reviewed
python3 sensitivity/L_accepted_set/compute_L.py
```

这些命令仅重算存档结果，不调用模型。原 `sensitivity/*/outputs` 是收到的存档，排名数字以 `sensitivity/reviewed` 和当前论文为准。前轮 pilot 的完整包在 `analysis/revision_robustness`；主指标 bootstrap 也在该目录。

未推送、未迁移；迁移前仍需作者确认。
