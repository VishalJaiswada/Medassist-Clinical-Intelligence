"""Structured summarization of patient reports."""
from src.retrieval.retriever import RecordStore, normalise_id

SUMMARY_INSTRUCTION = (
    "Write a concise, structured summary for a busy clinician. "
    "Use exactly these sections, but only include a section if the record contains it. "
    "Never invent details that are not in the record.\n"
    "### Patient Summary\n"
    "#### Patient Information\n#### Reason for Admission\n#### Medical History\n"
    "#### Key Findings\n#### Diagnosis\n#### Treatment Plan\n#### Follow-up"
)


def summarize(patient_id: str, respond, store: RecordStore) -> dict:
    pid = normalise_id(patient_id)
    record = store.load(pid)
    if record is None:
        return {
            "answer": f"No record found for patient {pid}.",
            "citations": [],
            "patient_ids": [pid],
        }
    answer = respond(SUMMARY_INSTRUCTION, record)
    return {
        "answer": answer,
        "citations": [{"patient_id": pid, "section": "Full record", "excerpt": record[:220]}],
        "patient_ids": [pid],
    }


def summarize_many(patient_ids: list[str], respond, store: RecordStore) -> dict:
    parts, citations, pids = [], [], []
    for pid in patient_ids:
        r = summarize(pid, respond, store)
        pids.append(normalise_id(pid))
        citations.extend(r["citations"])
        parts.append(f"===== Patient {normalise_id(pid)} =====\n{r['answer']}")
    return {"answer": "\n\n".join(parts), "citations": citations, "patient_ids": pids}
