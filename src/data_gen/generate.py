"""Generate realistic synthetic patient records (template-based, no API needed).

Each record is a structured text file: data/raw/patient_P001.txt
Run:  python -m src.data_gen.generate --count 50 --seed 42
"""
import argparse
import random
from pathlib import Path

from src import config

# ---------------------------------------------------------------- conditions
CONDITIONS = {
    "Type 2 Diabetes Mellitus": {
        "symptoms": ["increased thirst", "frequent urination", "fatigue", "blurred vision"],
        "labs": ["HbA1c: 9.2% (high)", "Fasting glucose: 212 mg/dL (high)", "Creatinine: 1.1 mg/dL"],
        "meds": ["Metformin 1000 mg twice daily", "Glimepiride 2 mg once daily"],
        "plan": "Diabetic diet, HbA1c recheck in 3 months, foot-care counselling.",
    },
    "Hypertension (Stage 2)": {
        "symptoms": ["headache", "dizziness", "chest discomfort on exertion"],
        "labs": ["BP: 168/104 mmHg", "Serum potassium: 4.1 mmol/L", "ECG: left ventricular hypertrophy"],
        "meds": ["Amlodipine 10 mg once daily", "Losartan 50 mg once daily"],
        "plan": "Low-salt diet, home BP monitoring, review in 4 weeks.",
    },
    "Acute Myocardial Infarction": {
        "symptoms": ["severe central chest pain radiating to left arm", "sweating", "breathlessness"],
        "labs": ["Troponin I: 8.4 ng/mL (critical high)", "ECG: ST elevation in anterior leads", "LVEF: 40%"],
        "meds": ["Aspirin 75 mg once daily", "Clopidogrel 75 mg once daily", "Atorvastatin 80 mg at night", "Metoprolol 50 mg twice daily"],
        "plan": "Primary PCI done. Cardiac rehabilitation, dual antiplatelet therapy for 12 months.",
    },
    "Community-Acquired Pneumonia": {
        "symptoms": ["fever with chills", "productive cough", "right-sided chest pain"],
        "labs": ["WBC: 14,200 /uL (high)", "CRP: 96 mg/L (high)", "Chest X-ray: right lower lobe consolidation"],
        "meds": ["Amoxicillin-clavulanate 625 mg thrice daily", "Azithromycin 500 mg once daily", "Paracetamol 650 mg as needed"],
        "plan": "Complete 7-day antibiotic course, repeat chest X-ray in 6 weeks.",
    },
    "Chronic Kidney Disease (Stage 3b)": {
        "symptoms": ["swelling of feet", "reduced urine output", "fatigue"],
        "labs": ["eGFR: 38 mL/min", "Creatinine: 1.9 mg/dL (high)", "Urine protein: 2+"],
        "meds": ["Sevelamer 800 mg thrice daily", "Sodium bicarbonate 500 mg twice daily"],
        "plan": "Nephrology follow-up, avoid NSAIDs, low-protein diet.",
    },
    "Asthma (Acute Exacerbation)": {
        "symptoms": ["wheezing", "shortness of breath", "night-time cough"],
        "labs": ["Peak flow: 55% of predicted", "SpO2: 93% on room air", "Chest X-ray: hyperinflated lungs"],
        "meds": ["Salbutamol inhaler 2 puffs as needed", "Budesonide inhaler 200 mcg twice daily", "Prednisolone 40 mg once daily for 5 days"],
        "plan": "Asthma action plan given, inhaler technique checked, review in 2 weeks.",
    },
    "Ischemic Stroke": {
        "symptoms": ["sudden right-sided weakness", "slurred speech", "facial droop"],
        "labs": ["CT brain: left MCA territory infarct", "NIHSS score: 9", "Carotid Doppler: 40% left stenosis"],
        "meds": ["Aspirin 150 mg once daily", "Atorvastatin 40 mg at night", "Citicoline 500 mg twice daily"],
        "plan": "Physiotherapy started, thrombolysis window missed, secondary prevention.",
    },
    "Acute Appendicitis": {
        "symptoms": ["right lower abdominal pain", "vomiting", "low-grade fever"],
        "labs": ["WBC: 13,800 /uL (high)", "Ultrasound: dilated appendix 9 mm, non-compressible"],
        "meds": ["Ceftriaxone 1 g twice daily IV", "Metronidazole 500 mg thrice daily IV", "Paracetamol 1 g thrice daily IV"],
        "plan": "Laparoscopic appendectomy done on day 1. Suture removal on day 8.",
    },
    "Congestive Heart Failure": {
        "symptoms": ["breathlessness on lying flat", "ankle swelling", "night-time cough"],
        "labs": ["BNP: 1,240 pg/mL (high)", "Echo: LVEF 35%", "Chest X-ray: pulmonary congestion"],
        "meds": ["Furosemide 40 mg once daily", "Spironolactone 25 mg once daily", "Bisoprolol 2.5 mg once daily"],
        "plan": "Fluid restriction 1.5 L/day, daily weight monitoring, cardiology review in 2 weeks.",
    },
    "COPD (Exacerbation)": {
        "symptoms": ["increased breathlessness", "change in sputum colour", "wheeze"],
        "labs": ["SpO2: 89% on room air", "ABG: pCO2 52 mmHg", "Chest X-ray: flattened diaphragms"],
        "meds": ["Tiotropium inhaler once daily", "Salmeterol-fluticasone inhaler twice daily", "Prednisolone 30 mg once daily for 5 days"],
        "plan": "Smoking cessation counselling, pulmonary rehabilitation referral.",
    },
}

NAMES_M = ["Ramesh Gupta", "Amit Sharma", "Vikram Singh", "Suresh Yadav", "Rajesh Kumar",
           "Anil Verma", "Deepak Mishra", "Manoj Tiwari", "Karan Patel", "Arjun Nair"]
NAMES_F = ["Priya Sharma", "Sunita Devi", "Meera Iyer", "Kavita Singh", "Anjali Gupta",
           "Rekha Verma", "Pooja Mishra", "Neha Kumari", "Divya Nair", "Shalini Rao"]
PHYSICIANS = ["Dr. A. Rao", "Dr. S. Banerjee", "Dr. M. Khan", "Dr. R. Iyer", "Dr. P. Nair"]
HISTORY_POOL = ["Type 2 diabetes for 6 years", "hypertension for 4 years", "no known drug allergies",
                "smoker (10 pack-years)", "occasional alcohol use", "family history of heart disease",
                "previous appendectomy in 2015", "takes regular medication as prescribed"]
RISK_POOL = ["age above 65", "smoking history", "sedentary lifestyle", "obesity (BMI 31)",
             "family history of cardiovascular disease", "chronic stress", "none significant"]
OUTCOMES = [
    ("Improved with treatment and discharged in stable condition.", 0.62),
    ("Stable at discharge; follow-up required in 2 weeks.", 0.22),
    ("Referred to specialist for further evaluation.", 0.10),
    ("Condition managed; readmission risk noted, close monitoring advised.", 0.06),
]


def make_vitals(rng: random.Random, condition: str) -> str:
    if "Hypertension" in condition or "Myocardial" in condition or "Heart Failure" in condition:
        bp = f"{rng.randint(150, 185)}/{rng.randint(95, 115)} mmHg"
    elif "Stroke" in condition:
        bp = f"{rng.randint(160, 190)}/{rng.randint(95, 110)} mmHg"
    else:
        bp = f"{rng.randint(110, 140)}/{rng.randint(70, 90)} mmHg"
    if "Asthma" in condition or "COPD" in condition or "Pneumonia" in condition:
        spo2 = f"{rng.randint(88, 94)}% on room air"
    else:
        spo2 = f"{rng.randint(95, 99)}% on room air"
    lines = [
        f"- BP: {bp}",
        f"- Heart rate: {rng.randint(68, 112)} bpm",
        f"- SpO2: {spo2}",
        f"- Temperature: {rng.choice(['98.6°F', '99.1°F', '100.4°F', '101.2°F'])}",
        f"- Respiratory rate: {rng.randint(14, 28)} /min",
    ]
    return "\n".join(lines)


def pick_outcome(rng: random.Random) -> str:
    r = rng.random()
    upto = 0.0
    for text, w in OUTCOMES:
        upto += w
        if r <= upto:
            return text
    return OUTCOMES[0][0]


def make_record(pid: str, rng: random.Random) -> str:
    sex = rng.choice(["Male", "Female"])
    name = rng.choice(NAMES_M if sex == "Male" else NAMES_F)
    age = rng.randint(24, 82)
    condition = rng.choice(list(CONDITIONS.keys()))
    c = CONDITIONS[condition]
    symptoms = ", ".join(rng.sample(c["symptoms"], k=min(3, len(c["symptoms"]))))
    history = "; ".join(rng.sample(HISTORY_POOL, k=3))
    labs = "\n".join(f"- {lab}" for lab in c["labs"])
    meds = "\n".join(f"- {med}" for med in c["meds"])
    admit_day = rng.randint(1, 28)
    admit_month = rng.randint(3, 8)  # spread over ~6 months for trend analytics
    physician = rng.choice(PHYSICIANS)
    vitals = make_vitals(rng, condition)
    outcome = pick_outcome(rng)
    risk_factors = "; ".join(rng.sample(RISK_POOL, k=2))

    return f"""## Patient Information
- Name: {name}
- Sex: {sex}
- Age: {age} years
- Medical Record Number (MRN): {pid}
- Admission date: 2026-{admit_month:02d}-{admit_day:02d}
- Attending physician: {physician}

## Reason for Admission
Patient presented with {symptoms}.

## Medical History
{history}.

## Examination Findings
Relevant examination findings consistent with {condition}. Vitals stable at presentation unless noted.

## Vital Signs
{vitals}

## Lab Results
{labs}

## Diagnosis
Primary diagnosis: {condition}.

## Treatment Plan
{meds}

## Outcome
{outcome}

## Risk Factors
{risk_factors}.

## Discharge Summary
Patient improved with treatment and was discharged in stable condition.
Follow-up plan: {c["plan"]}
"""


def generate(count: int, seed: int = 42) -> list[str]:
    rng = random.Random(seed)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    made = []
    for i in range(1, count + 1):
        pid = f"{config.ID_PREFIX}{i:03d}"
        path = config.DATA_DIR / f"patient_{pid}.txt"
        path.write_text(make_record(pid, rng), encoding="utf-8")
        made.append(pid)
    return made


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    made = generate(args.count, args.seed)
    print(f"Generated {len(made)} records in {config.DATA_DIR}: {', '.join(made)}")


if __name__ == "__main__":
    main()
