"""MedAssist Clinical Intelligence Platform — landing."""
import streamlit as st

from src.ui import CSS, page_setup

page_setup("Welcome", icon="🩺")
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; padding: 3rem 1rem 1.5rem 1rem;">
  <div style="font-size:3.2rem;">🩺</div>
  <h1 style="font-size:2.6rem; margin-bottom:.2rem;">MedAssist</h1>
  <p style="font-size:1.15rem; color:#9AA8BD;">AI-Powered Patient Intelligence & Clinical Decision Support</p>
  <p style="max-width:640px; margin: 1rem auto; color:#B9C4D6;">
  Understand each patient's symptoms and history, find similar historical cases,
  compare patients, assess risks from real patterns — and generate clinical reports,
  all grounded in your institution's data.</p>
</div>
""", unsafe_allow_html=True)

col = st.columns(3)
with col[1]:
    if st.button("➜  Enter Dashboard", type="primary", use_container_width=True):
        st.switch_page("pages/01_Dashboard.py")

st.markdown("### What you can do")
c1, c2, c3 = st.columns(3)
c1.markdown('<div class="card"><h4>🧠 AI Patient Analysis</h4>Enter symptoms, vitals, labs and history — get a structured clinical summary with similar-case evidence.</div>', unsafe_allow_html=True)
c2.markdown('<div class="card"><h4>🔎 Similar Cases</h4>Find historical patients like yours, with an explained similarity breakdown — never just a percentage.</div>', unsafe_allow_html=True)
c3.markdown('<div class="card"><h4>⚖️ Compare & Report</h4>Side-by-side patient comparison, risk & outcome analysis, and one-click clinical reports.</div>', unsafe_allow_html=True)

st.markdown('<div class="disclaimer">⚠️ <b>Clinical decision support — not a diagnosis.</b> '
            'This demo runs on <b>synthetic</b> patient data. AI outputs must be reviewed by a '
            'qualified clinician. Historical association does not imply causation.</div>',
            unsafe_allow_html=True)
st.caption("MedAssist Platform · demo build 2026-09-25")
