"""One-shot LLM analyses for the platform (summaries, comparisons, risks, reports).

Every prompt frames the model as a *decision-support* assistant: it must
distinguish historical facts from AI-generated estimates, express uncertainty,
and never present predictions as definitive diagnoses or guaranteed outcomes.
"""
from langchain_core.messages import HumanMessage, SystemMessage

SAFE_SYSTEM = (
    "You are a clinical decision-support assistant. You never diagnose and never "
    "predict the future with certainty. Rules:\n"
    "1. Distinguish clearly: (a) historical facts from the cases, (b) AI-generated "
    "similarities/estimates, (c) uncertainties.\n"
    "2. Never write 'the patient has X' or 'the patient will develop X'. Use "
    "'the available data is consistent with X' / 'similar historical cases showed "
    "an increased occurrence of X, which may be relevant for monitoring'.\n"
    "3. Every risk or prediction must list supporting evidence, relevant patient "
    "factors, and limitations.\n"
    "4. Be concise, structured, and use markdown headings and bullets."
)

_llm = None


def _client():
    global _llm
    if _llm is None:
        from src.chatbot.llm import get_llm

        _llm = get_llm()
    return _llm


def complete(user_prompt: str, system: str = SAFE_SYSTEM) -> str:
    return _client().invoke(
        [SystemMessage(content=system), HumanMessage(content=user_prompt)]
    ).content


# ------------------------------------------------------------------ summary
def patient_summary(current: dict) -> str:
    vitals = "; ".join(f"{k}: {v}" for k, v in current.get("vitals", {}).items()) or "not recorded"
    prompt = f"""Write a concise clinical summary of this patient under these headings:
Demographics, Main symptoms, Relevant history, Current medications, Important findings, Missing information.

Patient: age {current.get('age')}, sex {current.get('sex')}
Symptoms: {', '.join(current.get('symptoms', [])) or current.get('admission_reason', 'not recorded')}
History: {current.get('history', 'not recorded')}
Medications: {', '.join(current.get('medications', [])) or 'not recorded'}
Allergies: {current.get('allergies', 'not recorded')}
Vitals: {vitals}
Labs: {current.get('labs_text', 'not recorded')}
Notes: {current.get('notes', '')}"""
    return complete(prompt)


# --------------------------------------------------------------- comparison
def comparison_summary(current: dict, cases: list[dict]) -> str:
    case_txt = "\n".join(
        f"- {c['case_id']}: age {c['age']}, {c['sex']}; diagnosis: {c['diagnosis']}; "
        f"symptoms: {', '.join(c['symptoms'][:6])}; "
        f"treatment: {'; '.join(c['treatment'][:3])}; outcome: {c['outcome'] or 'not recorded'}; "
        f"similarity {c['similarity']}%"
        for c in cases
    )
    prompt = f"""Compare the current patient with these historical cases. Current patient:
age {current.get('age')}, {current.get('sex')}; symptoms: {', '.join(current.get('symptoms', []))};
history: {current.get('history', 'not recorded')}.

Historical cases:
{case_txt}

Write an AI Comparison Summary with: Major similarities, Important differences,
Relevant historical patterns, Factors associated with different outcomes,
Information needing additional clinical evaluation. Use decision-support language only."""
    return complete(prompt)


# -------------------------------------------------------------------- risks
def risk_synthesis(current: dict, similar: list[dict], patterns: list[dict]) -> str:
    pat_txt = "\n".join(
        f"- {p['diagnosis']}: observed in {p['count']} of {p['total']} similar cases ({p['pct']}%)"
        for p in patterns
    )
    case_txt = "\n".join(
        f"- {c['case_id']} ({c['similarity']}% similar): {c['diagnosis']} — "
        f"outcome: {c['outcome'] or 'not recorded'}"
        for c in similar[:5]
    )
    prompt = f"""Current patient: age {current.get('age')}, {current.get('sex')};
symptoms: {', '.join(current.get('symptoms', []))}; history: {current.get('history', 'not recorded')};
risk factors: {current.get('risk_factors', 'not recorded')}.

Diagnosis patterns in similar historical cases:
{pat_txt or 'insufficient data'}

Similar cases and their outcomes:
{case_txt or 'insufficient data'}

Write a Risk & Outcome Analysis. For each potential risk/outcome include: the outcome,
a risk category (Low/Moderate/High with justification), supporting historical evidence
('X of Y similar cases…'), relevant patient factors, uncertainty, and monitoring
considerations. End with: 'These are AI-generated estimates based on historical patterns, "
"not diagnoses or guaranteed predictions. Clinician review is required.'"""
    return complete(prompt)


# ------------------------------------------------------------------ reports
def build_report(kind: str, current: dict, similar: list[dict],
                 patterns: list[dict], summary: str = "",
                 comparison: str = "", risks: str = "") -> str:
    """Structured markdown report (11 sections for the clinical analysis kind)."""
    from datetime import date

    header = (f"# {kind}\n\nGenerated: {date.today().isoformat()} · "
              f"Patient: {current.get('name', current.get('patient_id', 'New patient'))} "
              f"({current.get('age')}, {current.get('sex')})\n\n"
              "> AI-generated decision-support document. Not a diagnosis. "
              "Requires clinician review.\n")
    case_list = "\n".join(
        f"### {c['case_id']} — similarity {c['similarity']}%\n"
        f"- Age/Sex: {c['age']}, {c['sex']}\n"
        f"- Diagnosis: {c['diagnosis']}\n"
        f"- Symptoms: {', '.join(c['symptoms'][:8])}\n"
        f"- Treatment: {'; '.join(c['treatment'][:4])}\n"
        f"- Outcome: {c['outcome'] or 'not recorded'}\n"
        f"- Similarity breakdown: " + ", ".join(
            f"{k} {v}%" for k, v in c["components"].items()) + "\n"
        for c in similar
    )
    pat_list = "\n".join(
        f"- {p['diagnosis']}: {p['count']}/{p['total']} similar cases ({p['pct']}%)"
        for p in patterns) or "Insufficient data."

    sections = {
        "1. Executive Summary": summary or "See patient summary.",
        "2. Patient History": current.get("history", "Not recorded."),
        "3. Current Presentation":
            f"Symptoms: {', '.join(current.get('symptoms', [])) or current.get('admission_reason', '—')}\n\n"
            f"Vitals: {current.get('vitals_text', 'not recorded')}\n\nLabs: {current.get('labs_text', 'not recorded')}",
        "4. Relevant Historical Cases": case_list or "None found.",
        "5. Similarities": "See similarity breakdown per case above.",
        "6. Differences": comparison or "Run a comparison to populate.",
        "7. Historical Outcomes": "\n".join(
            f"- {c['case_id']}: {c['outcome'] or 'not recorded'}" for c in similar) or "—",
        "8. Potential Risks": risks or "Run risk analysis to populate.",
        "9. Missing / Important Data": ", ".join(current.get("missing", [])) or "None flagged.",
        "10. Clinical Considerations":
            "Correlate with bedside findings; confirm critical values with repeat testing; "
            "escalate per local protocols if red-flag symptoms appear.",
        "11. Limitations":
            "Analysis is based on a limited synthetic historical dataset; associations are "
            "observational, not causal; AI outputs require clinician verification.",
    }
    body = "\n\n".join(f"## {title}\n\n{text}" for title, text in sections.items())
    return header + "\n" + body + "\n"
