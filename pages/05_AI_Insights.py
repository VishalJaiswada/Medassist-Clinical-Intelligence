"""🧠 AI Clinical Insights — summary, similar cases, patterns, risks."""
import streamlit as st

from src.analysis import insights
from src.ui import (analysis_for_current, disclaimer, get_backend, page_setup,
                    render_sidebar, require_llm, similar_case_card)

page_setup("AI Clinical Insights", icon="🧠")
render_sidebar()
store, index = get_backend()

st.title("🧠 AI Clinical Insights")

analysis = analysis_for_current(store, index, k=5)
if not analysis or analysis.get("error"):
    st.info("Start from **➕ New Patient** or open a patient from **🧑‍🤝‍🧑 Patients**, then return here.")
    st.stop()

current, similar, patterns = analysis["current"], analysis["similar"], analysis["patterns"]
who = current.get("name") or current.get("patient_id")
st.caption(f"Analyzing: **{who}** · {current.get('age')}y {current.get('sex')}")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Patient Summary", "🔎 Similar Cases", "📊 Diagnosis Patterns", "⚠️ Risk & Outcome Analysis"])

# ------------------------------------------------------------- 1 · summary
with tab1:
    st.markdown("### 📋 Patient summary")
    if require_llm():
        if "summary" not in analysis:
            with st.spinner("Generating summary…"):
                analysis["summary"] = insights.patient_summary(current)
        st.markdown(analysis["summary"])
    if current.get("missing"):
        st.warning("**Missing / incomplete:** " + ", ".join(current["missing"]) +
                   " — analysis confidence is reduced where data is missing.")

# ------------------------------------------------------- 2 · similar cases
with tab2:
    st.markdown("### 🔎 Similar historical cases")
    st.caption("Historical cases are anonymized (case IDs only — no names). "
               "Click “Why similar?” to see the explained breakdown.")
    if not similar:
        st.info("No similar cases found.")
    for c in similar:
        similar_case_card(c, "insights")
    st.markdown('<div class="safebar">ℹ️ These are <b>AI-identified similarities</b> to historical '
                "cases — not diagnoses. Open each case to inspect the underlying record.</div>",
                unsafe_allow_html=True)

# --------------------------------------------------------------- 3 · patterns
with tab3:
    st.markdown("### 📊 Historical diagnosis patterns")
    if patterns:
        total = patterns[0]["total"]
        for p in patterns:
            st.markdown(f"**{p['diagnosis']}** — {p['count']} of {total} similar cases "
                        f"({p['pct']}%)"
                        f'<div class="bar"><div style="width:{p["pct"]}%"></div></div>',
                        unsafe_allow_html=True)
        st.caption(f"Based on {total} similar historical cases. "
                   "Observed historical association ≠ proof of causation. "
                   "Small samples carry high uncertainty.")
    else:
        st.info("Insufficient data for reliable pattern analysis.")

# ------------------------------------------------------------------ 4 · risks
with tab4:
    st.markdown("### ⚠️ Risk & outcome analysis")
    if not similar:
        st.info("Insufficient data for reliable analysis.")
    elif require_llm():
        if "risks" not in analysis:
            with st.spinner("Synthesizing risk analysis…"):
                analysis["risks"] = insights.risk_synthesis(current, similar, patterns)
        st.markdown(analysis["risks"])
    st.markdown('<div class="disclaimer">⚠️ This is an <b>AI-generated risk estimate</b> based on '
                "historical patterns — not a diagnosis or guaranteed prediction. "
                "Clinician review is required.</div>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    if st.button("⚖️ Compare with similar cases", use_container_width=True):
        for c in similar[:3]:
            if c["patient_id"] not in st.session_state.compare_ids:
                st.session_state.compare_ids.append(c["patient_id"])
        st.switch_page("pages/07_Comparison.py")
with c2:
    if st.button("📑 Generate clinical report", use_container_width=True):
        st.switch_page("pages/08_Reports.py")

disclaimer()
