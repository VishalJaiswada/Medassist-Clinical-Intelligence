"""🧑‍🤝‍🧑 Patients — browse & search the patient registry."""
import pandas as pd
import streamlit as st

from src.analysis import patients
from src.ui import get_backend, page_setup, render_sidebar

page_setup("Patients", icon="🧑‍🤝‍🧑")
render_sidebar()
store, _ = get_backend()

st.title("🧑‍🤝‍🧑 Patients")
st.caption("All records are synthetic demo data. Historical cases are anonymized in analysis views.")

q = st.text_input("Search", placeholder="Filter by ID, name, diagnosis or symptom…",
                  label_visibility="collapsed")

rows = []
for pid in store.list_ids():
    p = patients.parse_record(pid, store.load(pid))
    level, _ = patients.risk_level(p)
    rows.append({
        "ID": pid, "Age": p["age"], "Sex": p["sex"],
        "Diagnosis": p["diagnosis"],
        "Symptoms": ", ".join(p["symptoms"][:4]),
        "Risk": level, "Admitted": p["admission_date"],
        "_name": p["name"],
    })

df = pd.DataFrame(rows)
if q:
    ql = q.lower()
    df = df[df.apply(lambda r: ql in f"{r['ID']} {r['_name']} {r['Diagnosis']} {r['Symptoms']}".lower(), axis=1)]

st.dataframe(df.drop(columns=["_name"]), use_container_width=True, hide_index=True,
             height=min(560, 80 + 35 * max(len(df), 1)))

st.markdown("### Open a patient profile")
ids = df["ID"].tolist()
if ids:
    sel = st.selectbox("Patient", ids, label_visibility="collapsed")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📄 Open profile", type="primary", use_container_width=True):
            st.session_state.current_pid = sel
            st.session_state.intake = None
            st.session_state.analysis = None
            st.switch_page("pages/03_Patient_Profile.py")
    with c2:
        if st.button("🧠 AI insights", use_container_width=True):
            st.session_state.current_pid = sel
            st.session_state.intake = None
            st.session_state.analysis = None
            st.switch_page("pages/05_AI_Insights.py")
    with c3:
        if st.button("⚖️ Add to comparison", use_container_width=True):
            if sel not in st.session_state.compare_ids:
                st.session_state.compare_ids.append(sel)
            st.toast(f"{sel} added to comparison")
else:
    st.info("No patients match the filter.")
