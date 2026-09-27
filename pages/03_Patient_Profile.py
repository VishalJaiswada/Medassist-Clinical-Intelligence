"""📄 Patient Profile — comprehensive record view with timeline."""
import streamlit as st

from src.analysis import patients
from src.ui import (disclaimer, get_backend, page_setup, render_sidebar,
                    risk_badge)

page_setup("Patient Profile", icon="📄")
render_sidebar()
store, index = get_backend()

pid = st.session_state.current_pid
if not pid:
    st.info("No patient selected. Pick one from the Patients page, or start a new analysis.")
    if st.button("🧑‍🤝‍🧑 Go to Patients"):
        st.switch_page("pages/02_Patients.py")
    st.stop()

p = patients.parse_record(pid, store.load(pid))
level, reasons = patients.risk_level(p)
missing = patients.missing_data(p)

st.title(f"📄 {p['name']}  ·  {pid}")
st.markdown(f"{p['age']} years · {p['sex']} · Admitted {p['admission_date']} "
            f"· {p['physician'] or ''} &nbsp; {risk_badge(level)}", unsafe_allow_html=True)
st.caption(f"Risk basis (rule-based): {'; '.join(reasons)}")

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🧠 AI insights", type="primary", use_container_width=True):
        st.session_state.intake = None
        st.session_state.analysis = None
        st.switch_page("pages/05_AI_Insights.py")
with c2:
    if st.button("🔎 Similar cases", use_container_width=True):
        st.session_state.similar_ref = ("existing", pid)
        st.switch_page("pages/06_Similar_Cases.py")
with c3:
    if st.button("📑 Generate report", use_container_width=True):
        st.session_state.intake = None
        st.session_state.analysis = None
        st.switch_page("pages/08_Reports.py")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Clinical data", "Timeline", "AI shortcuts"])

with tab1:
    st.markdown(f"""<div class="card"><h4>Overview</h4>
    <b>Diagnosis:</b> {p['diagnosis'] or '—'}<br>
    <b>Presenting complaint:</b> {p['admission_reason'] or '—'}<br>
    <b>Outcome:</b> {p['outcome'] or '—'}<br>
    <b>Risk factors:</b> {p['risk_factors'] or '—'}</div>""", unsafe_allow_html=True)
    if missing:
        st.warning("Missing: " + ", ".join(missing))

with tab2:
    cA, cB = st.columns(2)
    with cA:
        st.markdown("**🩺 Symptoms**")
        st.write(", ".join(p["symptoms"]) or "—")
        st.markdown("**📜 Medical history**")
        st.write(p["history"] or "—")
        st.markdown("**💊 Treatment**")
        for t in p["treatment"]:
            st.write("•", t)
    with cB:
        st.markdown("**❤️ Vital signs**")
        if p["vitals"]:
            for k, v in p["vitals"].items():
                st.write(f"• **{k}:** {v}")
        else:
            st.write("—")
        st.markdown("**🧪 Lab results**")
        for lab in p["labs"]:
            st.write("•", lab)
        if not p["labs"]:
            st.write("—")
    st.markdown("**🖼️ Examination findings**")
    st.write(p["examination"] or "—")
    st.markdown("**📝 Discharge summary**")
    st.write(p["discharge"] or "—")

with tab3:
    st.markdown("### 🕘 Patient timeline")
    st.markdown('<div class="timeline">', unsafe_allow_html=True)
    for ev in patients.build_timeline(p):
        st.markdown(f'<div class="ev"><b>{ev["date"]}</b> — <b>{ev["title"]}</b><br>'
                    f'<span style="color:#9AA8BD;font-size:.88rem">{ev["detail"]}</span></div>',
                    unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="card"><h4>Continue with AI</h4>'
                "Run the full decision-support analysis, compare against historical "
                "cases, or generate a clinical report.</div>", unsafe_allow_html=True)
    if st.button("▶ Run full AI analysis"):
        st.session_state.intake = None
        st.session_state.analysis = None
        st.switch_page("pages/05_AI_Insights.py")

disclaimer()
