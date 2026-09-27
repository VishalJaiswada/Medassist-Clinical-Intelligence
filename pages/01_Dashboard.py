"""🏥 Dashboard — high-level clinical & operational overview."""
from collections import Counter
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis import alerts, patients
from src.ui import (disclaimer, get_backend, metric_card, page_setup,
                    render_sidebar, risk_badge, style_fig)

page_setup("Dashboard")
render_sidebar()
store, index = get_backend()

st.title("🏥 Clinical Dashboard")
st.caption("Overview of patients, risks and recent activity · synthetic demo data")

# ------------------------------------------------------------ load & derive
records = []
for pid in store.list_ids():
    p = patients.parse_record(pid, store.load(pid))
    level, _ = patients.risk_level(p)
    p["risk"] = level
    records.append(p)

total = len(records)
high_risk = sum(1 for p in records if p["risk"] in ("High", "Critical"))
followups = sum(1 for p in records if "follow-up" in p["discharge"].lower())
all_alerts = alerts.scan_patients(store)

# --------------------------------------------------------------- metric row
m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_card("Total patients", str(total), f"{len(set(p['diagnosis'] for p in records))} distinct diagnoses")
with m2:
    metric_card("High-risk patients", str(high_risk), "rule-based estimate")
with m3:
    metric_card("Follow-ups due", str(followups), "from discharge plans")
with m4:
    metric_card("Active alerts", str(len(all_alerts)), "across all categories")

st.markdown("### 📈 Patient trends")
df = pd.DataFrame([{"month": (p["admission_date"] or "2026-01-01")[:7]} for p in records])
trend = df.groupby("month").size().reset_index(name="patients").sort_values("month")
fig = px.line(trend, x="month", y="patients", markers=True,
              labels={"month": "Admission month", "patients": "Patients"})
fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                  paper_bgcolor="white", plot_bgcolor="white")
fig.update_traces(line_color="#0E7C7B")
st.plotly_chart(style_fig(fig), use_container_width=True)

# ------------------------------------------------------------ distributions
c1, c2 = st.columns(2)
with c1:
    st.markdown("### 🍩 Diagnosis distribution")
    diag_counts = Counter(p["diagnosis"] for p in records if p["diagnosis"])
    ddf = pd.DataFrame(diag_counts.most_common(8), columns=["diagnosis", "cases"])
    fig2 = px.pie(ddf, names="diagnosis", values="cases", hole=0.45,
                  color_discrete_sequence=px.colors.sequential.Teal)
    fig2.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(style_fig(fig2), use_container_width=True)
with c2:
    st.markdown("### ⚠️ Patient risk distribution")
    risk_counts = Counter(p["risk"] for p in records)
    rdf = pd.DataFrame([{"risk": k, "patients": v} for k, v in risk_counts.items()])
    order = ["Low", "Moderate", "High", "Critical"]
    rdf["risk"] = pd.Categorical(rdf["risk"], categories=order, ordered=True)
    rdf = rdf.sort_values("risk")
    fig3 = px.bar(rdf, x="risk", y="patients", color="risk",
                  color_discrete_map={"Low": "#1E8449", "Moderate": "#D4A017",
                                      "High": "#E67E22", "Critical": "#C0392B"})
    fig3.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(style_fig(fig3), use_container_width=True)
    st.caption("Rule-based heuristic — review before clinical use.")

# ------------------------------------------------------------ recent activity
st.markdown("### 🕘 Recent activity")
recent = sorted(records, key=lambda p: p["admission_date"] or "", reverse=True)[:6]
for p in recent:
    st.markdown(
        f'<div class="card" style="padding:.7rem 1rem;">'
        f'<b>{p["patient_id"]}</b> · {p["age"]}y {p["sex"]} · {p["diagnosis"][:60]} '
        f'{risk_badge(p["risk"])}'
        f'<span style="float:right;color:#9AA8BD;font-size:.8rem">{p["admission_date"]} · {p["physician"] or ""}</span>'
        f"</div>", unsafe_allow_html=True)

if st.button("➕ New patient analysis"):
    st.switch_page("pages/04_New_Patient.py")

disclaimer()
