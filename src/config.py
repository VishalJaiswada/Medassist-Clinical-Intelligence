"""Central configuration for MedAssist. Everything is overridable via .env."""
import os
from pathlib import Path

try:  # python-dotenv is optional; plain environment variables also work
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.getenv("MEDASSIST_DATA_DIR", BASE_DIR / "data" / "raw"))
INDEX_DIR = Path(os.getenv("MEDASSIST_INDEX_DIR", BASE_DIR / "data" / "faiss_index"))

EMBEDDING_MODEL = os.getenv(
    "MEDASSIST_EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2"
)
RERANKER_MODEL = os.getenv(
    "MEDASSIST_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

LLM_PROVIDER = os.getenv("MEDASSIST_LLM_PROVIDER", "groq").lower()  # groq | openai | ollama
GROQ_MODEL = os.getenv("MEDASSIST_GROQ_MODEL", "openai/gpt-oss-20b")
OPENAI_MODEL = os.getenv("MEDASSIST_OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_MODEL = os.getenv("MEDASSIST_OLLAMA_MODEL", "llama3.1")

TOP_K_SIMILAR = int(os.getenv("MEDASSIST_TOP_K", "5"))

# How many similar cases the symptom checker looks at
DIAGNOSIS_TOP_K = int(os.getenv("MEDASSIST_DIAGNOSIS_TOP_K", "5"))

# Cross-encoder reranking improves chunk relevance but costs a few seconds
# per question on CPU. Set MEDASSIST_RERANK=0 to skip it (faster answers).
RERANK_ENABLED = os.getenv("MEDASSIST_RERANK", "1") == "1"

# Patient IDs look like P001, P042 ... (normalised to 3 digits)
ID_PREFIX = "P"

SYSTEM_PROMPT = (
    "You are MedAssist, a careful clinical assistant. "
    "Answer ONLY from the patient record sections provided by the user. "
    "If the answer is not present in the records, say exactly: 'Not found in the record.' "
    "Never use outside medical knowledge, never guess, and never invent details. "
    "Be direct and concise, and mention the disease stage when the record states it."
)

# Used by the symptom checker: the LLM may synthesise across similar cases
# and add general recovery guidance, but everything case-specific must come
# from the provided cases, and it must always close with the disclaimer.
DIAGNOSIS_SYSTEM_PROMPT = (
    "You are MedAssist, a clinical decision-support assistant. "
    "You receive a user's symptom description plus excerpts from similar historical patient cases. "
    "Rules:\n"
    "1. Base every case-specific statement (likely conditions, treatments given, outcomes) "
    "STRICTLY on the provided cases — never invent case details.\n"
    "2. Structure your answer with these sections: 'Possible conditions (seen in similar cases)', "
    "'How similar cases were treated', 'General recovery guidance', 'When to see a doctor urgently'.\n"
    "3. 'General recovery guidance' may contain widely-known self-care measures, clearly labeled as general advice.\n"
    "4. Always end with exactly: 'This is not a medical diagnosis. Please consult a qualified doctor.'"
)
