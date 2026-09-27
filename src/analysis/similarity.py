"""Explained patient similarity.

Deterministic, interpretable component scores (0-100) so clinicians see *why*
two cases are considered similar — not just a percentage:

  symptoms  35%   — Jaccard overlap of extracted symptom keywords
  diagnosis 20%   — same / overlapping diagnosis terms
  history   15%   — Jaccard overlap of medical-history terms
  labs      15%   — overlap of lab test names + abnormal flags
  age       10%   — proximity of ages
  sex        5%   — same sex

The FAISS vector search provides the candidate shortlist (recall); these
components provide the ranking and the explanation.
"""
import re

from src.analysis.patients import STOPWORDS, extract_symptoms

WEIGHTS = {
    "symptoms": 0.35,
    "diagnosis": 0.20,
    "history": 0.15,
    "labs": 0.15,
    "age": 0.10,
    "sex": 0.05,
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 50.0  # no information either way
    if not a or not b:
        return 0.0
    return 100.0 * len(a & b) / len(a | b)


def _lab_tests(p: dict) -> set[str]:
    tests = set()
    for line in p.get("labs", []):
        name = re.split(r"[:\-]", line)[0].strip().lower()
        name = re.sub(r"[^a-z ]", "", name).strip()
        if name:
            tests.add(name)
    return tests


def component_scores(current: dict, candidate: dict) -> dict[str, float]:
    cur_sym = set(extract_symptoms(
        current.get("admission_reason", "") + " " + " ".join(current.get("symptoms", []))))
    cand_sym = set(candidate.get("symptoms", []))

    diag_overlap = _jaccard(_tokens(current.get("diagnosis", "")),
                            _tokens(candidate.get("diagnosis", "")))
    # boost when the core condition clearly matches
    if (current.get("diagnosis") and candidate.get("diagnosis")
            and current["diagnosis"].split("(")[0].strip().lower()
            in candidate["diagnosis"].lower()):
        diag_overlap = max(diag_overlap, 90.0)

    scores = {
        "symptoms": round(_jaccard(cur_sym, cand_sym), 1),
        "diagnosis": round(diag_overlap, 1),
        "history": round(_jaccard(_tokens(current.get("history", "")),
                                  _tokens(candidate.get("history", ""))), 1),
        "labs": round(_jaccard(_lab_tests(current), _lab_tests(candidate)), 1),
    }
    a1, a2 = current.get("age"), candidate.get("age")
    if a1 and a2:
        scores["age"] = round(max(0.0, 100.0 - abs(a1 - a2) * 2.0), 1)
    else:
        scores["age"] = 50.0
    s1, s2 = (current.get("sex") or "").lower(), (candidate.get("sex") or "").lower()
    scores["sex"] = 100.0 if (s1 and s1 == s2) else (50.0 if not s1 or not s2 else 0.0)
    return scores


def overall_score(components: dict[str, float]) -> float:
    return round(sum(components[k] * WEIGHTS[k] for k in WEIGHTS), 1)


def explain_against(current: dict, candidate: dict) -> dict:
    comps = component_scores(current, candidate)
    return {"components": comps, "overall": overall_score(comps)}


def find_similar_explained(current: dict, current_text: str, store, index,
                           k: int = 5, exclude: str | None = None) -> list[dict]:
    """Vector shortlist -> explained, re-ranked similar cases."""
    from src.analysis.patients import anonymized_case_id, parse_record

    hits = index.similar(current_text, k=max(k * 3, 10), exclude=exclude)
    results = []
    for pid, _vec_score in hits:
        record = store.load(pid)
        if not record:
            continue
        cand = parse_record(pid, record)
        exp = explain_against(current, cand)
        results.append({
            "patient_id": pid,
            "case_id": anonymized_case_id(pid),
            "age": cand["age"],
            "sex": cand["sex"],
            "diagnosis": cand["diagnosis"],
            "symptoms": cand["symptoms"],
            "treatment": cand["treatment"],
            "outcome": cand["outcome"],
            "components": exp["components"],
            "similarity": exp["overall"],
        })
        if len(results) >= k * 2:
            break
    results.sort(key=lambda r: r["similarity"], reverse=True)
    return results[:k]
