"""⚖️ Patient Comparison — current patient vs historical cases."""
import pandas as pd
import streamlit as st

from src.analysis import insights, patients, service
from src.ui import (analysis_for_current, disclaimer, get_backend, page_setup,
                    render_sidebar, require_llm)

page_setup("Patient Comparison", icon="⚖️")
render_sidebar()
store, index = get_backend()

st.title("⚖️ Patient Comparison")

analysis = analysis_for_current(store, index, k=5)
if not analysis or analysis.get("error"):
    st.info("Run an analysis first (➕ New Patient, or open a patient → AI insights).")
    st.stop()
current = analysis["current"]

# ------------------------------------------------------------- case picker
all_ids = [c["patient_id"] for c in analysis["similar"]]
sel = st.multiselect("Historical cases to compare",
                     all_ids,
                     default=st.session_state.compare_ids or all_ids[:2],
                     format_func=lambda pid: next(
                         (c["case_id"] for c in analysis["similar"] if c["patient_id"] == pid), pid))
st.session_state.compare_ids = sel
if not sel:
    st.info("Select at least one historical case.")
    st.stop()

cases = []
for pid in sel:
    hit = next((c for c in analysis["similar"] if c["patient_id"] == pid), None)
    if hit:
        cases.append(hit)
    else:  # fallback: parse directly
        p = patients.parse_record(pid, store.load(pid))
        cases.append({"patient_id": pid, "case_id": patients.anonymized_case_id(pid),
                      "age": p["age"], "sex": p["sex"], "diagnosis": p["diagnosis"],
                      "symptoms": p["symptoms"], "treatment": p["treatment"],
                      "outcome": p["outcome"], "similarity": None, "components": {}})

# ------------------------------------------------------------ compare table
def row(label, cur, *vals):
    return [label, cur, *vals]

table = [
    row("Age", current.get("age"), *[c["age"] for c in cases]),
    row("Sex", current.get("sex"), *[c["sex"] for c in cases]),
    row("Symptoms", ", ".join(current.get("symptoms", [])) or "—",
        *[", ".join(c["symptoms"][:6]) or "—" for c in cases]),
    row("Diagnosis", current.get("diagnosis") or "Pending",
        *[c["diagnosis"] or "—" for c in cases]),
    row("Treatment", "; ".join(current.get("medications", [])) or "Current / planned",
        *["; ".join(c["treatment"][:3]) or "—" for c in cases]),
    row("Outcome", "Unknown", *[c["outcome"] or "not recorded" for c in cases]),
    row("Similarity", "— (reference)",
        *[f"{c['similarity']:.0f}%" if c["similarity"] else "—" for c in cases]),
]
cols = ["Category", "Current patient"] + [c["case_id"] for c in cases]
df = pd.DataFrame(table, columns=cols)
st.dataframe(df, use_container_width=True, hide_index=True)

# ------------------------------------------------------- AI comparison summary
st.markdown("### 🧠 AI Comparison Summary")
if require_llm():
    if "comparison" not in analysis or analysis.get("comparison_for") != tuple(sel):
        with st.spinner("Generating comparison summary…"):
            analysis["comparison"] = insights.comparison_summary(
                service.intake_to_current(st.session_state.intake)
                if st.session_state.intake else current, cases)
            analysis["comparison_for"] = tuple(sel)
    st.markdown(analysis["comparison"])

st.markdown('<div class="safebar">ℹ️ Comparison is based on recorded historical data and '
            "AI-identified similarities. Differences in era, setting and data completeness "
            "limit direct comparability — interpret with clinical judgement.</div>",
            unsafe_allow_html=True)
disclaimer()
