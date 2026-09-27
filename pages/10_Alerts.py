"""🔔 Alerts — intelligent, neutrally-worded clinical alerts."""
import streamlit as st

from src.analysis import alerts
from src.ui import disclaimer, get_backend, page_setup, render_sidebar

page_setup("Alerts", icon="🔔")
render_sidebar()
store, _ = get_backend()

st.title("🔔 Alerts")
st.caption("Rule-based alerts from record data. Worded neutrally — review, don't alarm.")

items = alerts.scan_patients(store)
if not items:
    st.success("No alerts at the moment. 🎉")
    st.stop()

SEV = {"critical": ("🔴", "#C0392B"), "high": ("🟠", "#E67E22"),
       "info": ("🔵", "#2471A3"), "low": ("⚪", "#93A3BB")}
cats = ["All"] + sorted(set(a["category"] for a in items))
cat = st.selectbox("Category", cats)
shown = [a for a in items if cat == "All" or a["category"] == cat]

st.write(f"**{len(shown)}** alert(s)")
for a in shown:
    icon, color = SEV[a["severity"]]
    st.markdown(
        f'<div class="card" style="border-left:5px solid {color};padding:.8rem 1rem;">'
        f"{icon} <b>{a['category']}</b> — {a['title']}<br>"
        f"<span style='color:#9AA8BD;font-size:.88rem'>{a['detail']}</span></div>",
        unsafe_allow_html=True)
    if st.button("Open patient", key=f"al_{a['patient_id']}_{a['category']}_{a['title'][:10]}"):
        st.session_state.current_pid = a["patient_id"]
        st.session_state.intake = None
        st.session_state.analysis = None
        st.switch_page("pages/03_Patient_Profile.py")

disclaimer()
