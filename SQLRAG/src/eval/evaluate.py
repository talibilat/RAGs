
from __future__ import annotations
"""Simple offline/online evaluation runner for the SQL chat pipeline."""
import json
import argparse
import re
from statistics import mean

from agent.chat_sql import answer_question


def extract_numbers(text: str):
    return [float(x.replace(',', '')) for x in re.findall(r"[-+]?\d[\d,]*\.?\d*", text)]


def approx_equal(a: float, b: float, tol: float = 1e-6, rel: float = 0.02) -> bool:
    if a == b:
        return True
    if abs(a - b) <= tol:
        return True
    return abs(a - b) <= rel * max(abs(a), abs(b))


def run_eval(examples_path: str):
    with open(examples_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for ex in data:
        q = ex["question"]
        expected = ex.get("expected_numbers", [])
        ans = answer_question(q)
        got = extract_numbers(ans)
        if expected:
            hits = sum(1 for e in expected if any(approx_equal(e, g) for g in got))
            recall = hits / len(expected)
        else:
            recall = None
        cites = len(re.findall(r"\[\d+\]", ans))
        results.append({"q": q, "answer": ans, "recall": recall, "cites": cites})

    recalls = [r["recall"] for r in results if r["recall"] is not None]
    avg_recall = mean(recalls) if recalls else None
    cite_rate = sum(1 for r in results if r["cites"] > 0) / len(results)

    return {"avg_recall": avg_recall, "cite_rate": cite_rate, "results": results}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--examples", type=str, required=True)
    args = ap.parse_args()

    out = run_eval(args.examples)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
