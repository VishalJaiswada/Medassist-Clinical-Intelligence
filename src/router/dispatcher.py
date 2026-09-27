"""Route a classified question to the right handler."""
from src.handlers import diagnosis, qa, similarity, summarizer


def dispatch(intent: str, question: str, patient_ids: list[str], deps: dict) -> dict:
    """deps: {'respond': fn, 'store': RecordStore, 'index': VectorIndex}."""
    respond, store, index = deps["respond"], deps["store"], deps["index"]

    # Two or more patients mentioned -> treat as multi-patient question
    if len(patient_ids) >= 2 and intent == "single_qa":
        intent = "multi_qa"

    if intent == "diagnosis_support":
        return diagnosis.analyze_symptoms(question, respond, store, index)

    if intent == "similar_patient" and len(patient_ids) == 1:
        return similarity.find_similar(patient_ids[0], respond, store, index)

    if intent == "single_qa" and len(patient_ids) == 1:
        return qa.answer_single(patient_ids[0], question, respond, store)

    if intent == "multi_qa" and len(patient_ids) >= 2:
        return qa.answer_multi(patient_ids, question, respond, store)

    if intent == "summarization" and patient_ids:
        if len(patient_ids) == 1:
            return summarizer.summarize(patient_ids[0], respond, store)
        return summarizer.summarize_many(patient_ids, respond, store)

    return {
        "answer": (
            "I couldn't understand that. Try one of these:\n"
            "- 'What is the diagnosis for patient P001?'\n"
            "- 'Summarize the report for patient P002.'\n"
            "- 'Find patients similar to patient P003.'\n"
            "- 'Compare patients P001 and P004.'\n"
            "- Or describe symptoms: 'I have fever and cough for 4 days, what could it be?'"
        ),
        "citations": [],
        "patient_ids": patient_ids,
        "intent": "unknown",
    }
