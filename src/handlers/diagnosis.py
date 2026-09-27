"""Symptom-based decision support: the user describes symptoms (or pastes a
report) in free text, we find the most similar historical cases, and the LLM
synthesises what conditions those cases had, how they were treated, and what
recovery measures were recorded.

This is decision *support*, not a diagnosis — the prompt forces a disclaimer.
"""
from src import config
from src.retrieval.retriever import RecordStore, VectorIndex

DISCLAIMER = "This is not a medical diagnosis. Please consult a qualified doctor."


def _brief(record: str, limit: int = 1100) -> str:
    return record[:limit] + ("..." if len(record) > limit else "")


def _extract_section(record: str, *names: str) -> str:
    """Pull out named '## Section' blocks to keep the context focused."""
    out = []
    current, buf = None, []
    for line in record.splitlines():
        if line.startswith("## "):
            if current and buf and any(n.lower() in current.lower() for n in names):
                out.append("## " + current + "\n" + "\n".join(buf))
            current, buf = line[3:].strip(), []
        elif current is not None:
            buf.append(line)
    if current and buf and any(n.lower() in current.lower() for n in names):
        out.append("## " + current + "\n" + "\n".join(buf))
    return "\n\n".join(out)


def analyze_symptoms(
    description: str,
    respond,
    store: RecordStore,
    index: VectorIndex,
    k: int | None = None,
    extra: str = "",
) -> dict:
    """description: free-text symptoms / pasted report. extra: 'Age 45, male' etc."""
    k = k or config.DIAGNOSIS_TOP_K
    hits = index.similar(description, k=k)
    if not hits:
        return {
            "answer": ("I couldn't find any similar cases in the records. "
                       "Try describing the symptoms in more detail."),
            "citations": [],
            "patient_ids": [],
            "similar": [],
            "intent": "diagnosis_support",
        }

    context_parts, citations, similar = [], [], []
    for sim_pid, score in hits:
        sim_record = store.load(sim_pid)
        if not sim_record:
            continue
        similar.append({"patient_id": sim_pid, "score": round(score, 3)})
        focused = _extract_section(
            sim_record, "diagnosis", "treatment", "medication", "outcome", "plan"
        )
        context_parts.append(
            f"--- Similar case {sim_pid} (relevance score {score:.2f}) ---\n"
            f"{_brief(focused or sim_record)}"
        )
        citations.append(
            {"patient_id": sim_pid, "section": "Similar case",
             "excerpt": (focused or sim_record)[:220]}
        )

    who = f"Patient details: {extra}.\n" if extra else ""
    question = (
        f"{who}Reported symptoms / case description:\n{description}\n\n"
        f"Based on the {len(context_parts)} similar historical cases below, "
        "what conditions did those cases have, how were they treated, and what "
        "should this person watch out for?"
    )
    answer = respond(
        question,
        "\n\n".join(context_parts),
        instructions=config.DIAGNOSIS_SYSTEM_PROMPT,
    )
    if DISCLAIMER not in answer:
        answer = answer.rstrip() + "\n\n" + DISCLAIMER

    return {
        "answer": answer,
        "citations": citations,
        "patient_ids": [],
        "similar": similar,
        "intent": "diagnosis_support",
    }
