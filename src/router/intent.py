"""Intent classification: fast keyword rules first, embedding similarity
against reference examples as a fallback.

Keyword-first keeps the common cases instant (no 400 MB model load just to
classify a question); the embedding model is only loaded for ambiguous input.
"""
import re

from src import config

INTENTS = (
    "single_qa",
    "multi_qa",
    "summarization",
    "similar_patient",
    "diagnosis_support",
)

REFERENCE_EXAMPLES = {
    "single_qa": [
        "What is the diagnosis for patient P001?",
        "What medications is patient P002 taking?",
        "What are the lab results for patient P003?",
        "When was patient P004 admitted?",
        "What is the treatment plan for patient P005?",
    ],
    "multi_qa": [
        "Compare the diagnoses of patients P001 and P002.",
        "What are the treatment plans for patients P003 and P004?",
        "Which patient has worse lab results, P001 or P005?",
        "Compare patients P002 and P006.",
    ],
    "summarization": [
        "Summarize the report for patient P001.",
        "Give me an overview of patient P002's record.",
        "What are the key points from patient P003's file?",
        "Summarise the discharge summary for patient P004.",
    ],
    "similar_patient": [
        "Find patients similar to patient P001.",
        "Who has a similar diagnosis as patient P002?",
        "Show patients with the same condition as patient P003.",
        "Find cases similar to patient P004.",
    ],
    "diagnosis_support": [
        "I have fever, cough and chest pain for 5 days, what could it be?",
        "What disease causes high blood sugar and frequent urination?",
        "I am suffering from headache and dizziness, what should I do?",
        "My father has swelling in his legs and feels tired all the time.",
        "Here is my report: elevated creatinine and low hemoglobin. What does it mean?",
    ],
}

# (keywords, intent) — checked in order; first match wins
KEYWORD_RULES = [
    (("summar", "overview", "key points", "discharge summary"), "summarization"),
    (("similar", "same condition", "like patient"), "similar_patient"),
    (("compare", "versus", " vs ", "between", "which patient"), "multi_qa"),
    (("i have", "i am suffering", "i'm suffering", "my father", "my mother",
      "my wife", "my husband", "symptom", "what could it be", "what disease",
      "what does it mean", "suffering from", "complains of", "i feel"),
     "diagnosis_support"),
]


class IntentClassifier:
    def __init__(self):
        self._model = None
        self._ref_embeds = None

    def _embed_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(config.EMBEDDING_MODEL)
        return self._model

    def _reference_embeddings(self):
        if self._ref_embeds is None:
            model = self._embed_model()
            self._ref_embeds = {
                intent: model.encode(examples, convert_to_tensor=True)
                for intent, examples in REFERENCE_EXAMPLES.items()
            }
        return self._ref_embeds

    def _keyword_match(self, question: str) -> str | None:
        q = question.lower()
        for keywords, intent in KEYWORD_RULES:
            if any(k in q for k in keywords):
                return intent
        return None

    def _embedding_match(self, question: str) -> str:
        from sentence_transformers import util

        model = self._embed_model()
        q_emb = model.encode(question, convert_to_tensor=True)
        best_intent, best_score = "single_qa", -1.0
        for intent, ref_embeds in self._reference_embeddings().items():
            score = util.cos_sim(q_emb, ref_embeds).max().item()
            if score > best_score:
                best_intent, best_score = intent, score
        return best_intent

    def classify(self, question: str) -> str:
        # 1) fast path: keywords (no model load)
        hit = self._keyword_match(question)
        if hit:
            # "similar to patient P001" with 2+ IDs is still a comparison
            if hit == "similar_patient":
                ids = re.findall(r"\bP\d+\b", question.upper())
                if len(ids) >= 2:
                    return "multi_qa"
            return hit
        # 2) embedding similarity for ambiguous phrasing
        try:
            return self._embedding_match(question)
        except Exception:
            pass  # offline / model unavailable
        # 3) last resort: ID-count heuristic
        ids = re.findall(r"\bP\d+\b", question.upper())
        return "multi_qa" if len(ids) >= 2 else "single_qa"
