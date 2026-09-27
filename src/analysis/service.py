"""Analysis orchestration: intake -> similar cases -> patterns -> risks."""
from collections import Counter

from src.analysis import insights, patients, similarity


def intake_to_current(intake: dict) -> dict:
    """Normalise a New-Patient form dict into the parsed-patient shape."""
    symptoms = list(dict.fromkeys(
        [s.strip().lower() for s in intake.get("symptoms", []) if s.strip()]
        + patients.extract_symptoms(intake.get("notes", ""))))
    vitals = {k: v for k, v in (intake.get("vitals") or {}).items() if v}
    return {
        "patient_id": intake.get("patient_id") or "NEW",
        "name": intake.get("name") or "New patient",
        "age": intake.get("age"),
        "sex": intake.get("sex"),
        "admission_date": intake.get("visit_date"),
        "physician": None,
        "admission_reason": intake.get("notes", ""),
        "history": "; ".join(intake.get("conditions", [])) or intake.get("history_text", ""),
        "examination": "",
        "labs": [],
        "labs_text": intake.get("labs_text", ""),
        "vitals": vitals,
        "vitals_text": "; ".join(f"{k}: {v}" for k, v in vitals.items()),
        "diagnosis": "",
        "treatment": [],
        "medications": intake.get("medications", []),
        "allergies": intake.get("allergies", ""),
        "outcome": "",
        "risk_factors": "; ".join(intake.get("risk_factor_list", [])),
        "discharge": "",
        "symptoms": symptoms,
        "missing": _missing_intake(intake),
        "raw": "",
    }


def _missing_intake(intake: dict) -> list[str]:
    missing = []
    if not intake.get("labs_text"):
        missing.append("Laboratory results")
    if not (intake.get("vitals") or {}):
        missing.append("Vital signs")
    if not intake.get("conditions") and not intake.get("history_text"):
        missing.append("Medical history")
    if not intake.get("medications"):
        missing.append("Current medications")
    if not intake.get("notes"):
        missing.append("Free-text clinical notes")
    return missing


def intake_text(intake: dict) -> str:
    """Free-text rendering of an intake for vector search."""
    parts = [
        f"Age {intake.get('age')}, {intake.get('sex')}.",
        "Symptoms: " + ", ".join(intake.get("symptoms", [])) + ".",
        f"Duration: {intake.get('duration', '')}. Severity: {intake.get('severity', '')}.",
        "Conditions: " + ", ".join(intake.get("conditions", [])) + ".",
        "Medications: " + ", ".join(intake.get("medications", [])) + ".",
        "Labs: " + intake.get("labs_text", ""),
        "Imaging: " + intake.get("imaging_text", ""),
        "Notes: " + intake.get("notes", ""),
    ]
    return " ".join(p for p in parts if p.strip(" ."))


def diagnosis_patterns(similar: list[dict]) -> list[dict]:
    total = len(similar)
    counts = Counter(c["diagnosis"] for c in similar if c.get("diagnosis"))
    return [{"diagnosis": d, "count": n, "total": total,
             "pct": round(100.0 * n / total, 1)} for d, n in counts.most_common()]


def analyze_intake(intake: dict, store, index, k: int = 5) -> dict:
    """Full pipeline for a new patient. Returns everything the UI needs."""
    current = intake_to_current(intake)
    text = intake_text(intake)
    similar = similarity.find_similar_explained(current, text, store, index, k=k)
    patterns = diagnosis_patterns(similar)
    return {
        "current": current,
        "similar": similar,
        "patterns": patterns,
        # LLM parts are generated lazily by the UI so the page stays fast:
        # keys 'summary', 'risks', 'comparison' filled on demand.
    }


def analyze_existing(patient_id: str, store, index, k: int = 5) -> dict:
    record = store.load(patient_id)
    if not record:
        return {"error": f"No record found for {patient_id}."}
    current = patients.parse_record(patient_id, record)
    current["missing"] = patients.missing_data(current)
    similar = similarity.find_similar_explained(
        current, record, store, index, k=k, exclude=patient_id)
    return {"current": current, "similar": similar,
            "patterns": diagnosis_patterns(similar)}
