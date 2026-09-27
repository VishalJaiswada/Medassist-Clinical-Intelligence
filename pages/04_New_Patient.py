"""➕ New Patient — comprehensive intake → AI analysis."""
from datetime import date

import streamlit as st

from src.analysis.patients import SYMPTOM_KEYWORDS
from src.ui import disclaimer, page_setup, render_sidebar

page_setup("New Patient", icon="➕")
render_sidebar()

st.title("➕ New Patient")
st.caption("Enter what is available — structured fields or free text. Missing fields are flagged, never invented.")

with st.form("intake", clear_on_submit=False):
    st.markdown("### 🧑 Patient information")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        name = st.text_input("Name", placeholder="e.g. Demo Patient")
    with c2:
        age = st.number_input("Age", min_value=0, max_value=120, value=45)
    with c3:
        sex = st.selectbox("Gender", ["Male", "Female", "Other"])
    with c4:
        visit_date = st.date_input("Date of visit", value=date.today())

    st.markdown("### 🤒 Current symptoms")
    preset = sorted(set(SYMPTOM_KEYWORDS))
    symptoms = st.multiselect("Select symptoms (type to search)", preset,
                              placeholder="fever, cough, chest pain…")
    extra = st.text_input("Other symptoms (comma separated)", placeholder="e.g. palpitations, dry mouth")
    c1, c2 = st.columns(2)
    with c1:
        duration = st.text_input("Duration of symptoms", placeholder="e.g. 4 days")
    with c2:
        severity = st.select_slider("Severity", options=["Mild", "Moderate", "Severe"])

    st.markdown("### ❤️ Vital signs")
    v1, v2, v3, v4, v5 = st.columns(5)
    vitals = {
        "BP": v1.text_input("BP", placeholder="120/80"),
        "Heart rate": v2.text_input("HR", placeholder="78 bpm"),
        "SpO2": v3.text_input("SpO2", placeholder="98%"),
        "Temperature": v4.text_input("Temp", placeholder="98.6°F"),
        "Resp. rate": v5.text_input("RR", placeholder="16 /min"),
    }

    st.markdown("### 📜 Clinical information")
    conditions = st.multiselect(
        "Existing conditions",
        ["Type 2 Diabetes Mellitus", "Hypertension", "Asthma", "COPD", "Heart disease",
         "Chronic Kidney Disease", "Thyroid disorder", "None known"])
    meds = st.text_input("Current medications (comma separated)")
    allergies = st.text_input("Allergies", placeholder="e.g. Penicillin — or 'none known'")
    labs_text = st.text_area("Relevant lab results", height=80,
                             placeholder="e.g. HbA1c 9.2% (high); WBC 14,200 /uL (high)")
    imaging_text = st.text_area("Imaging / report summaries", height=80,
                                placeholder="e.g. Chest X-ray: right lower lobe consolidation")
    notes = st.text_area("Free-text clinical notes", height=110,
                         placeholder="Describe the presentation in your own words…")

    submitted = st.form_submit_button("🔬 Analyze Patient", type="primary",
                                      use_container_width=True)

if submitted:
    all_symptoms = symptoms + [s.strip() for s in extra.split(",") if s.strip()]
    if not all_symptoms and not notes.strip():
        st.error("Please enter at least one symptom or some clinical notes.")
        st.stop()
    st.session_state.intake = {
        "name": name.strip(), "age": int(age), "sex": sex,
        "visit_date": visit_date.isoformat(), "symptoms": all_symptoms,
        "duration": duration, "severity": severity, "vitals": vitals,
        "conditions": conditions,
        "medications": [m.strip() for m in meds.split(",") if m.strip()],
        "allergies": allergies, "labs_text": labs_text,
        "imaging_text": imaging_text, "notes": notes,
    }
    st.session_state.current_pid = None
    st.session_state.analysis = None
    st.session_state.compare_ids = []
    st.switch_page("pages/05_AI_Insights.py")

disclaimer()
