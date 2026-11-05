# Worked example: one unit through the full pipeline (Task 2, unit T2U_0010)

| File | Content |
|---|---|
| `1_prompt_instruction_header.txt` | The instruction header of the Task 2 prompt (identical for every unit and every closed-book system). |
| `2_input_unit.jsonl` | The unit's input line, exactly as it appears among the 193 JSONL lines of the prompt. |
| `3_model_response_row.tsv` | Claude-Sonnet-5.5's response to this unit (run 1, verbatim row from the predictions file). |
| `4_adjudication_row.tsv` | The five-axis adjudication record for this unit-run. |
| `5_gold_annotation.tsv` | The evaluator-only gold annotation (mechanism class, mediator, causal topology, expected direction). |

Pipeline: the model receives the instruction header plus the input line, and returns a
tab-separated row (`unit_id`, `predicted_direction`, `mechanism_reasoning`). The response
is then scored (direction vs gold) and adjudicated on five axes against the gold annotation.

For this unit the response passes the full five-axis chain (1,1,1,1,1) with the correct
direction, which is why it is used as the worked example in the paper.

To rescore it yourself:

```
python3 evaluation_/scoring/score_model_outputs.py \
    --bundle evaluation_ --task task2 \
    --predictions runs/claude/run1/task2_predictions.tsv \
    --output /tmp/x.json
```
