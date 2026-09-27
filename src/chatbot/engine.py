"""MedAssistEngine — the single entry point for asking questions.

Usage:
    engine = MedAssistEngine()
    result = engine.ask("What is the diagnosis for patient P001?")
    print(result["answer"])

    result = engine.analyze_symptoms("fever and cough for 4 days", age=34, sex="male")
"""
import re
import time

from src import config
from src.chatbot.llm import get_llm
from src.chatbot.memory import Conversation
from src.handlers import diagnosis
from src.retrieval.retriever import RecordStore, VectorIndex, normalise_id
from src.router import dispatcher
from src.router.intent import IntentClassifier


class MedAssistEngine:
    def __init__(self):
        self.store = RecordStore()
        self.index = VectorIndex()
        self.classifier = IntentClassifier()
        self._llm = None
        self._conversation = None
        self._pending_ids: list[str] = []

    # -- lazy LLM so importing the engine never needs an API key ----------
    @property
    def conversation(self) -> Conversation:
        if self._conversation is None:
            self._llm = get_llm()
            self._conversation = Conversation(self._llm)
            if self._pending_ids:
                self._conversation.last_patient_ids = self._pending_ids
                self._pending_ids = []
        return self._conversation

    # -- patient ID handling ----------------------------------------------
    @staticmethod
    def extract_ids(question: str) -> list[str]:
        raw = re.findall(r"\bP\s?(\d{1,4})\b", question.upper())
        seen = []
        for num in raw:
            pid = normalise_id(f"P{num}")
            if pid not in seen:
                seen.append(pid)
        return seen

    # -- main API ----------------------------------------------------------
    def ask(self, question: str) -> dict:
        t0 = time.perf_counter()
        question = question.strip()
        if not question:
            return {"answer": "Please ask a question.", "citations": [],
                    "patient_ids": [], "intent": "unknown", "elapsed_s": 0.0}

        intent = self.classifier.classify(question)
        patient_ids = self.extract_ids(question)
        # follow-up: reuse patient(s) from memory — except for symptom checks,
        # which are about the user, not a stored patient. Don't create the LLM
        # just to peek at memory.
        if (not patient_ids and intent != "diagnosis_support"
                and self._conversation is not None):
            patient_ids = self._conversation.last_patient_ids

        deps = {
            # lazy: the LLM (and API key) is only needed when a handler
            # actually calls respond()
            "respond": lambda q, ctx, instructions=None: self.conversation.respond(
                q, ctx, instructions=instructions),
            "store": self.store,
            "index": self.index,
        }
        result = dispatcher.dispatch(intent, question, patient_ids, deps)
        result["intent"] = result.get("intent", intent)

        if result.get("patient_ids"):
            if self._conversation is not None:
                self._conversation.last_patient_ids = result["patient_ids"]
            else:
                self._pending_ids = result["patient_ids"]  # applied on first use
        result["elapsed_s"] = round(time.perf_counter() - t0, 1)
        return result

    def analyze_symptoms(self, description: str, age: int | None = None,
                         sex: str | None = None) -> dict:
        """Direct entry point for the Symptom Checker tab (no intent step)."""
        t0 = time.perf_counter()
        extra = ", ".join(
            p for p in
            [f"Age {age}" if age else "", f"Sex: {sex}" if sex else ""]
            if p
        )
        result = diagnosis.analyze_symptoms(
            description.strip(),
            lambda q, ctx, instructions=None: self.conversation.respond(
                q, ctx, instructions=instructions),
            self.store, self.index, extra=extra,
        )
        result["elapsed_s"] = round(time.perf_counter() - t0, 1)
        return result

    def reset(self):
        self._pending_ids = []
        if self._conversation is not None:
            self._conversation.reset()

    # -- health info for the UI -------------------------------------------
    def status(self) -> dict:
        return {
            "patients": len(self.store.list_ids()),
            "index_ready": self.index.ready,
            "llm_provider": config.LLM_PROVIDER,
            "groq_model": config.GROQ_MODEL,
            "embedding_model": config.EMBEDDING_MODEL,
            "rerank_enabled": config.RERANK_ENABLED,
        }
