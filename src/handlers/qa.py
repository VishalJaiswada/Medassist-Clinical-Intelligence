"""Clinical question answering: single-patient and multi-patient."""
from concurrent.futures import ThreadPoolExecutor

from src.retrieval import chunker, reranker
from src.retrieval.retriever import RecordStore, normalise_id


def answer_single(patient_id: str, question: str, respond, store: RecordStore) -> dict:
    """Answer a question about one patient, grounded in their record."""
    pid = normalise_id(patient_id)
    record = store.load(pid)
    if record is None:
        return {
            "answer": f"No record found for patient {pid}.",
            "citations": [],
            "patient_ids": [pid],
        }

    chunks = chunker.chunk_record(record)
    top = reranker.rerank(question, chunks, top_n=2)
    context = "\n\n".join(c["text"] for c in top)
    answer = respond(question, context)

    return {
        "answer": answer,
        "citations": [
            {"patient_id": pid, "section": c["title"], "excerpt": c["text"][:220]}
            for c in top
        ],
        "patient_ids": [pid],
    }


def answer_multi(patient_ids: list[str], question: str, respond, store: RecordStore) -> dict:
    """Answer per patient in parallel, then combine into a comparison."""
    pids = [normalise_id(p) for p in patient_ids]

    def _one(pid: str) -> dict:
        return answer_single(pid, f"{question} (for patient {pid})", respond, store)

    with ThreadPoolExecutor(max_workers=min(len(pids), 4)) as pool:
        results = list(pool.map(_one, pids))

    per_patient, citations = [], []
    for pid, r in zip(pids, results):
        citations.extend(r["citations"])
        per_patient.append(f"--- Patient {pid} ---\n{r['answer']}")

    combined = respond(
        f"Compare and combine these per-patient answers into one clear response. "
        f"Original question: {question}",
        "\n\n".join(per_patient),
    )
    return {"answer": combined, "citations": citations, "patient_ids": pids}
