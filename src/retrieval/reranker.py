"""Cross-encoder reranking of record chunks. Falls back gracefully if the
model cannot be downloaded (e.g. offline) — then chunks keep file order."""
from src import config

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(config.RERANKER_MODEL)
    return _model


def rerank(question: str, chunks: list[dict], top_n: int = 2) -> list[dict]:
    """Return the top_n chunks most relevant to the question.

    Set MEDASSIST_RERANK=0 to skip the cross-encoder (faster on CPU).
    """
    if not chunks:
        return []
    if not config.RERANK_ENABLED:
        return chunks[:top_n]
    try:
        model = _get_model()
        pairs = [(question, c["text"]) for c in chunks]
        scores = model.predict(pairs)
        ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:top_n]]
    except Exception:
        return chunks[:top_n]  # offline fallback
