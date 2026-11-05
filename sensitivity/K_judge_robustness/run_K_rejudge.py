#!/usr/bin/env python3
"""Appendix K step 2 — re-adjudicate the frozen packets with a different judge.

Judge: gemini-3.8-flash — a system that never served as a judge anywhere in the
frozen pipeline (original judges: gpt-6-astra for 5 systems, claude-sonnet-5-5 for
gpt). The adjudicator instructions are byte-identical to the shipped rubric; only the
judge model changes. Batch = 40 rows; each batch gets ONE continuation call for any
rows missed on the first pass (same re-ask policy as the frozen runs). Raw judge
outputs are archived verbatim under judgments/.

Cost/scale: 9 batches (Task 2, 360 rows) + 12 batches (Task 3, 480 rows).
This run does NOT modify any frozen file; outputs feed only the sensitivity appendix.
"""
import json, time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
PKT = HERE / "packets"
JUD = HERE / "judgments"
JUD.mkdir(exist_ok=True)
API_BASE = __import__('os').environ['TEAMOROUTER_API_BASE']
KEY = __import__('os').environ['TEAMOROUTER_API_KEY']
JUDGE_NAME = "gemini-3.8-flash"


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def call(prompt, max_tokens=16000):
    for attempt in range(3):
        try:
            r = requests.post(f"{API_BASE}/v1beta/models/{JUDGE_NAME}:generateContent",
                              headers={"Content-Type": "application/json", "x-goog-api-key": KEY},
                              json={"contents": [{"parts": [{"text": prompt}]}],
                                    "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens}},
                              timeout=900)
            if r.status_code == 400 and "max" in r.text.lower() and max_tokens > 8000:
                max_tokens //= 2; continue
            r.raise_for_status()
            d = r.json()
            cands = d.get("candidates") or []
            if not cands:
                raise RuntimeError(f"no candidates: {json.dumps(d)[:200]}")
            return "".join(p.get("text", "") for p in cands[0]["content"]["parts"])
        except Exception as e:
            log(f"  attempt {attempt+1} error: {str(e)[:140]}")
            time.sleep(15 * (attempt + 1))
    return None


def parse_rows(text):
    """extract {key: [5 axis strings]} from judge output"""
    if not text: return {}
    lines = text.strip().splitlines()
    start = None
    for i, l in enumerate(lines):
        if l.strip().replace(" ", "").startswith("unit_id"): start = i; break
    if start is None: return {}
    rows = {}
    for l in lines[start + 1:]:
        s = l.strip()
        if not s or s.startswith("---"): continue
        parts = s.split("\t")
        if len(parts) < 6:
            parts += [""] * (6 - len(parts))
        key = parts[0].strip()
        if "@" in key and key not in rows:
            rows[key] = [p.strip() for p in parts[1:6]]
    return rows


def judge_batch(pkt_path, out_raw, out_tsv):
    expected = [l.split("\t")[0].strip() for l in pkt_path.read_text(encoding="utf-8").splitlines()
                if "@" in l and not l.startswith("unit_id")]
    text = call(pkt_path.read_text(encoding="utf-8"))
    out_raw.write_text(text or "API_FAILED", encoding="utf-8")
    rows = parse_rows(text)
    if len(rows) < len(expected):
        miss = sorted(set(expected) - set(rows))
        log(f"  {pkt_path.name}: missing {len(miss)}/{len(expected)} -> continuation")
        body = "\n".join(l for l in pkt_path.read_text(encoding="utf-8").splitlines()
                         if l.split("\t")[0].strip() in set(miss))
        cont = ("Your previous answer was missing some rows. Output ONLY the missing rows, "
                "same tab-separated format and header, one line per unit_id, nothing else.\n\n" + body)
        text2 = call(cont, max_tokens=8000)
        out_raw.with_suffix(".continuation_raw.txt").write_text(text2 or "API_FAILED", encoding="utf-8")
        rows.update(parse_rows(text2))
    with open(out_tsv, "w", encoding="utf-8") as f:
        f.write("unit_id\tmechanism_correct\tmediator_correct\tcausal_role_order_correct\t"
                "intervention_outcome_link_correct\tno_material_contradiction\n")
        for k in expected:
            v = rows.get(k)
            if v: f.write(k + "\t" + "\t".join(v) + "\n")
    log(f"  {pkt_path.name}: parsed {len(rows)}/{len(expected)} -> {out_tsv.name}")


def main():
    batches = sorted(PKT.glob("task2_rejudge_batch*.txt")) + sorted(PKT.glob("task3_rejudge_batch*.txt"))
    log(f"{len(batches)} batches, judge={JUDGE_NAME}")
    for p in batches:
        tag = p.stem
        out_raw = JUD / f"{tag}_raw.txt"
        out_tsv = JUD / f"{tag}_judgments.tsv"
        if out_tsv.exists() and sum(1 for _ in open(out_tsv)) >= 41:
            log(f"  {tag}: already done, skip")
            continue
        judge_batch(p, out_raw, out_tsv)
    log("K_REJUDGE_DONE")


if __name__ == "__main__":
    main()
