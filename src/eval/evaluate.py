"""Evaluation harness for MedAssist.

Runs three suites and saves metrics to src/eval/results.json:

1. Intent routing      — offline, no API key needed.
2. Retrieval accuracy  — needs the FAISS index (python -m src.indexing.build_index).
   For each patient we query with their admission symptoms and check the
   correct record comes back top-1, plus a symptom-checker retrieval test.
3. End-to-end QA       — needs an LLM API key; runs the original question set.

Note: all evaluation here is on the bundled *synthetic* records. The MERA
project this was inspired by additionally evaluates on de-identified
MIMIC-IV-Note records, which require credentialed access and are not
included here.

Run:  python -m src.eval.evaluate
"""
import json
import time
from datetime import datetime
from pathlib import Path

from src.chatbot.engine import MedAssistEngine
from src.handlers import diagnosis
from src.router.intent import IntentClassifier

INTENT_TESTS = [
    ("What is the diagnosis for patient P001?", "single_qa"),
    ("What medications is patient P007 taking?", "single_qa"),
    ("Compare patients P001 and P005.", "multi_qa"),
    ("Which patient has worse labs, P002 or P009?", "multi_qa"),
    ("Summarize the report for patient P003.", "summarization"),
    ("Give me an overview of patient P008's record.", "summarization"),
    ("Find patients similar to patient P004.", "similar_patient"),
    ("Who has the same condition as patient P006?", "similar_patient"),
    ("I have fever and dry cough for 4 days, what could it be?", "diagnosis_support"),
    ("My father has swelling in his legs and feels tired.", "diagnosis_support"),
    ("What disease causes high blood sugar and frequent urination?", "diagnosis_support"),
]

QA_TESTS = [
    {"question": "What is the diagnosis for patient P001?", "expect_ids": ["P001"]},
    {"question": "What medications is patient P002 taking?", "expect_ids": ["P002"]},
    {"question": "Summarize the report for patient P003.", "expect_ids": ["P003"]},
    {"question": "Find patients similar to patient P004.", "expect_ids": ["P004"]},
    {"question": "Compare patients P001 and P005.", "expect_ids": ["P001", "P005"]},
    {"question": "What are the lab results for patient P006?", "expect_ids": ["P006"]},
]


def _section(record: str, title: str) -> str:
    """Extract the text of a '## Title' section."""
    lines, capture, buf = record.splitlines(), False, []
    for line in lines:
        if line.startswith("## "):
            if capture:
                break
            capture = line[3:].strip().lower() == title.lower()
        elif capture:
            buf.append(line)
    return "\n".join(buf).strip()


def suite_intent() -> dict:
    clf = IntentClassifier()
    rows = []
    for question, expected in INTENT_TESTS:
        t0 = time.perf_counter()
        got = clf.classify(question)
        rows.append({
            "question": question, "expected": expected, "got": got,
            "correct": got == expected,
            "elapsed_s": round(time.perf_counter() - t0, 3),
        })
    acc = sum(r["correct"] for r in rows) / len(rows)
    return {"accuracy": round(acc, 3), "tests": rows}


def suite_retrieval(engine: MedAssistEngine) -> dict:
    """Admission symptoms -> correct patient must be the top hit."""
    if not engine.index.ready:
        return {"skipped": "vector index not built"}
    rows = []
    for pid in engine.store.list_ids():
        record = engine.store.load(pid)
        symptoms = _section(record, "Reason for Admission")
        if not symptoms:
            continue
        t0 = time.perf_counter()
        hits = engine.index.similar(symptoms, k=3)
        top1 = hits[0][0] if hits else None
        rows.append({
            "patient_id": pid, "top1": top1,
            "correct": top1 == pid,
            "elapsed_s": round(time.perf_counter() - t0, 3),
        })

    # Symptom-checker path: stub the LLM, verify retrieval + disclaimer
    diag_rows = []
    for pid in engine.store.list_ids()[:4]:
        record = engine.store.load(pid)
        symptoms = _section(record, "Reason for Admission")
        if not symptoms:
            continue
        t0 = time.perf_counter()
        r = diagnosis.analyze_symptoms(
            symptoms,
            respond=lambda q, ctx, instructions=None: "stub",
            store=engine.store, index=engine.index, k=5,
        )
        found = any(s["patient_id"] == pid for s in r["similar"])
        diag_rows.append({
            "patient_id": pid, "source_in_top5": found,
            "disclaimer_present": diagnosis.DISCLAIMER in r["answer"],
            "elapsed_s": round(time.perf_counter() - t0, 3),
        })

    acc = sum(r["correct"] for r in rows) / len(rows) if rows else 0
    dacc = sum(r["source_in_top5"] for r in diag_rows) / len(diag_rows) if diag_rows else 0
    return {
        "top1_accuracy": round(acc, 3),
        "symptom_checker_recall@5": round(dacc, 3),
        "retrieval_tests": rows,
        "symptom_checker_tests": diag_rows,
    }


def suite_qa(engine: MedAssistEngine) -> dict:
    rows = []
    for item in QA_TESTS:
        t0 = time.perf_counter()
        try:
            r = engine.ask(item["question"])
            rows.append({
                "question": item["question"],
                "intent": r.get("intent"),
                "patient_ids": r.get("patient_ids"),
                "expected_ids_found": set(item["expect_ids"]) <= set(r.get("patient_ids", [])),
                "has_citations": bool(r.get("citations")),
                "elapsed_s": round(time.perf_counter() - t0, 1),
                "answer": r.get("answer"),
            })
            engine.reset()
        except Exception as e:  # noqa: BLE001
            rows.append({"question": item["question"], "error": str(e)})
    passed = sum(1 for r in rows
                 if r.get("expected_ids_found") and r.get("has_citations"))
    avg_t = [r["elapsed_s"] for r in rows if "elapsed_s" in r]
    return {
        "passed": f"{passed}/{len(rows)}",
        "avg_latency_s": round(sum(avg_t) / len(avg_t), 1) if avg_t else None,
        "tests": rows,
    }


def main() -> None:
    engine = MedAssistEngine()
    report = {"run_at": datetime.now().isoformat(), "data": "synthetic records"}

    print("1/3 intent routing…", flush=True)
    report["intent_routing"] = suite_intent()
    print(f"    accuracy: {report['intent_routing']['accuracy']}")

    print("2/3 retrieval accuracy…", flush=True)
    report["retrieval"] = suite_retrieval(engine)
    if "skipped" in report["retrieval"]:
        print(f"    skipped ({report['retrieval']['skipped']})")
    else:
        print(f"    top-1: {report['retrieval']['top1_accuracy']}, "
              f"symptom recall@5: {report['retrieval']['symptom_checker_recall@5']}")

    print("3/3 end-to-end QA (needs LLM key)…", flush=True)
    report["end_to_end_qa"] = suite_qa(engine)
    print(f"    passed: {report['end_to_end_qa']['passed']}, "
          f"avg latency: {report['end_to_end_qa']['avg_latency_s']}s")

    out = Path(__file__).parent / "results.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nFull report saved to {out}")


if __name__ == "__main__":
    main()
