"""Patient similarity search: find cases similar to a given patient."""
from src import config
from src.retrieval.retriever import RecordStore, VectorIndex, normalise_id


def _brief(record: str, limit: int = 900) -> str:
    return record[:limit] + ("..." if len(record) > limit else "")


def find_similar(
    patient_id: str, respond, store: RecordStore, index: VectorIndex,
    k: int | None = None,
) -> dict:
    pid = normalise_id(patient_id)
    record = store.load(pid)
    if record is None:
        return {
            "answer": f"No record found for patient {pid}.",
            "citations": [],
            "patient_ids": [pid],
            "similar": [],
        }

    k = k or config.TOP_K_SIMILAR
    hits = index.similar(record, k=k, exclude=pid)
    if not hits:
        return {
            "answer": "No similar patients found in the index.",
            "citations": [],
            "patient_ids": [pid],
            "similar": [],
        }

    context_parts, citations, similar = [], [], []
    for sim_pid, score in hits:
        sim_record = store.load(sim_pid)
        if not sim_record:
            continue
        similar.append({"patient_id": sim_pid, "score": round(score, 3)})
        context_parts.append(f"--- Similar patient {sim_pid} ---\n{_brief(sim_record)}")
        citations.append(
            {"patient_id": sim_pid, "section": "Full record", "excerpt": sim_record[:220]}
        )

    answer = respond(
        f"These patients have the most similar records to patient {pid}. "
        f"Summarise how each is similar and how each differs (diagnosis, key findings, treatment).",
        f"Reference patient {pid}:\n{_brief(record)}\n\n" + "\n\n".join(context_parts),
    )
    return {
        "answer": answer,
        "citations": citations,
        "patient_ids": [pid],
        "similar": similar,
    }
