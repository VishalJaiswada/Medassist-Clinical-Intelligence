"""Structured view over patient records.

Parses the '## Section' text records into dicts the platform can work with:
demographics, symptoms, labs, vitals, diagnosis, treatment, outcome, plus
derived artefacts (risk estimate, timeline). Missing sections are tolerated.
"""
import re
from datetime import datetime, timedelta

# Curated clinical phrases for deterministic symptom extraction.
SYMPTOM_KEYWORDS = sorted([
    "severe central chest pain radiating to left arm", "breathlessness on lying flat",
    "right lower abdominal pain", "sudden right-sided weakness", "change in sputum colour",
    "chest discomfort on exertion", "productive cough", "night-time cough", "dry cough",
    "shortness of breath", "reduced urine output", "frequent urination", "increased thirst",
    "blurred vision", "slurred speech", "facial droop", "swelling of feet", "ankle swelling",
    "low-grade fever", "chest tightness", "chest pain", "breathlessness", "wheezing",
    "fatigue", "tiredness", "swelling", "headache", "dizziness", "nausea", "vomiting",
    "abdominal pain", "weakness", "sweating", "fever", "chills", "cough", "wheeze",
    "edema", "palpitations", "back pain", "joint pain", "sore throat", "runny nose",
    "diarrhea", "weight loss", "loss of appetite", "night sweats", "confusion",
    "fainting", "rash", "itching", "jaundice", "numbness", "tingling", "insomnia",
], key=len, reverse=True)

STOPWORDS = set("and or the a an of with for to in on at is are was were be been "
                "as by from with without within".split())


def sections_of(text: str) -> dict[str, str]:
    """Split '## Title' record into {title: body}."""
    out, current, buf = {}, None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if current:
                out[current] = "\n".join(buf).strip()
            current, buf = line[3:].strip(), []
        elif current is not None:
            buf.append(line)
    if current:
        out[current] = "\n".join(buf).strip()
    return out


def extract_symptoms(text: str) -> list[str]:
    """Deterministic keyword symptom extraction (longest match first)."""
    low, found, used = text.lower(), [], []
    for kw in SYMPTOM_KEYWORDS:
        start = 0
        while True:
            i = low.find(kw, start)
            if i < 0:
                break
            span = (i, i + len(kw))
            if not any(s <= i < e or s < i + len(kw) <= e for s, e in used):
                found.append(kw)
                used.append(span)
                break
            start = i + 1
    return found


def _bullets(body: str) -> list[str]:
    return [l[2:].strip() for l in body.splitlines()
            if l.strip().startswith("- ") and l[2:].strip()]


def parse_record(patient_id: str, text: str) -> dict:
    s = sections_of(text)
    info = s.get("Patient Information", "")
    age_m = re.search(r"Age:\s*(\d+)", info)
    sex_m = re.search(r"Sex:\s*(\w+)", info)
    name_m = re.search(r"Name:\s*(.+)", info)
    date_m = re.search(r"Admission date:\s*([\d-]+)", info)
    phys_m = re.search(r"Attending physician:\s*(.+)", info)

    vitals = {}
    for line in _bullets(s.get("Vital Signs", "")):
        if ":" in line:
            k, v = line.split(":", 1)
            vitals[k.strip()] = v.strip()

    admission_reason = s.get("Reason for Admission", "")
    diagnosis = re.sub(r"^Primary diagnosis:\s*", "",
                       s.get("Diagnosis", "")).strip(" .")

    return {
        "patient_id": patient_id,
        "name": name_m.group(1).strip() if name_m else patient_id,
        "age": int(age_m.group(1)) if age_m else None,
        "sex": sex_m.group(1) if sex_m else None,
        "admission_date": date_m.group(1) if date_m else None,
        "physician": phys_m.group(1).strip() if phys_m else None,
        "admission_reason": admission_reason,
        "history": s.get("Medical History", ""),
        "examination": s.get("Examination Findings", ""),
        "labs": _bullets(s.get("Lab Results", "")),
        "vitals": vitals,
        "diagnosis": diagnosis,
        "treatment": _bullets(s.get("Treatment Plan", "")),
        "treatment_plan": s.get("Treatment Plan", ""),
        "outcome": s.get("Outcome", ""),
        "risk_factors": s.get("Risk Factors", ""),
        "discharge": s.get("Discharge Summary", ""),
        "symptoms": extract_symptoms(admission_reason + " " + s.get("Examination Findings", "")),
        "raw": text,
    }


def anonymized_case_id(patient_id: str) -> str:
    """'P001' -> 'CASE-0001' (no names exposed for historical cases)."""
    num = re.sub(r"\D", "", patient_id)
    return f"CASE-{int(num):04d}" if num else f"CASE-{patient_id}"


# ------------------------------------------------------------------ risk
def risk_level(p: dict) -> tuple[str, list[str]]:
    """Rule-based risk estimate. Labelled as heuristic everywhere it is shown."""
    text = f"{p.get('diagnosis', '')} {p.get('examination', '')} " \
           f"{' '.join(p.get('labs', []))}".lower()
    reasons = []
    if any(k in text for k in ["stage 5", "stage 4", "sepsis", "myocardial infarction",
                               "stroke", "critical high", "heart failure"]):
        reasons = ["critical diagnosis or critical lab value present"]
        return "Critical", reasons
    if any(k in text for k in ["stage 3", "failure", "infarct", "uncontrolled",
                               "(high)", "exacerbation"]):
        reasons = ["advanced stage / organ involvement / abnormal labs"]
        return "High", reasons
    if any(k in text for k in ["stage 2", "stage 1", "diabetes", "hypertension",
                               "pneumonia", "asthma"]):
        reasons = ["chronic condition requiring active management"]
        return "Moderate", reasons
    return "Low", ["no high-risk indicators in record"]


# ---------------------------------------------------------------- timeline
def build_timeline(p: dict) -> list[dict]:
    """Ordered clinical events derived from record sections."""
    try:
        base = datetime.strptime(p["admission_date"], "%Y-%m-%d") if p.get("admission_date") \
            else datetime(2026, 6, 1)
    except ValueError:
        base = datetime(2026, 6, 1)

    def d(offset: int) -> str:
        return (base + timedelta(days=offset)).strftime("%Y-%m-%d")

    events = []
    if p.get("admission_reason"):
        events.append({"date": d(0), "title": "Admission",
                       "detail": p["admission_reason"]})
    if p.get("examination"):
        events.append({"date": d(0), "title": "Clinical examination",
                       "detail": p["examination"][:300]})
    if p.get("labs"):
        events.append({"date": d(1), "title": "Laboratory / imaging tests",
                       "detail": "; ".join(p["labs"])[:400]})
    if p.get("diagnosis"):
        events.append({"date": d(1), "title": f"Diagnosis: {p['diagnosis']}",
                       "detail": "Primary diagnosis recorded."})
    if p.get("treatment"):
        events.append({"date": d(1), "title": "Treatment started",
                       "detail": "; ".join(p["treatment"])[:400]})
    if p.get("outcome"):
        events.append({"date": d(5), "title": "Outcome",
                       "detail": p["outcome"][:400]})
    if p.get("discharge"):
        events.append({"date": d(6), "title": "Discharge & follow-up plan",
                       "detail": p["discharge"][:400]})
    events.append({"date": d(6), "title": "Current status",
                   "detail": "Latest recorded state of this case."})
    return events


def missing_data(p: dict) -> list[str]:
    """Fields a clinician may want to complete."""
    missing = []
    if not p.get("labs"):
        missing.append("Laboratory results")
    if not p.get("vitals"):
        missing.append("Vital signs")
    if not p.get("history"):
        missing.append("Medical history")
    if not p.get("treatment"):
        missing.append("Treatment / medication details")
    if not p.get("outcome"):
        missing.append("Outcome / follow-up status")
    return missing
