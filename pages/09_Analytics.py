"""📊 Analytics — interactive trends across the patient population."""
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis import patients
from src.ui import disclaimer, get_backend, page_setup, render_sidebar, style_fig

page_setup("Analytics", icon="📊")
render_sidebar()
store, _ = get_backend()

st.title("📊 Analytics")
st.caption("Population-level views over the synthetic historical dataset.")

rows = []
for pid in store.list_ids():
    p = patients.parse_record(pid, store.load(pid))
    level, _ = patients.risk_level(p)
    rows.append({
        "id": pid, "age": p["age"], "sex": p["sex"], "diagnosis": p["diagnosis"],
        "risk": level, "month": (p["admission_date"] or "2026-01-01")[:7],
        "outcome": (p["outcome"] or "not recorded").split(";")[0][:60],
    })
df = pd.DataFrame(rows)

# ------------------------------------------------------------------ filters
st.markdown("### Filters")
f1, f2, f3 = st.columns(3)
with f1:
    sexes = st.multiselect("Gender", sorted(df["sex"].dropna().unique()),
                           default=sorted(df["sex"].dropna().unique()))
with f2:
    risks = st.multiselect("Risk", ["Low", "Moderate", "High", "Critical"],
                           default=["Low", "Moderate", "High", "Critical"])
with f3:
    diags = st.multiselect("Diagnosis", sorted(df["diagnosis"].unique()),
                           default=sorted(df["diagnosis"].unique()))
fdf = df[df["sex"].isin(sexes) & df["risk"].isin(risks) & df["diagnosis"].isin(diags)]
if fdf.empty:
    st.warning("No records match the filters.")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    st.markdown("#### Disease trends over time")
    t = fdf.groupby(["month", "diagnosis"]).size().reset_index(name="cases").sort_values("month")
    fig = px.bar(t, x="month", y="cases", color="diagnosis", barmode="stack",
                 color_discrete_sequence=px.colors.sequential.Teal)
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(style_fig(fig), use_container_width=True)
with c2:
    st.markdown("#### Outcome distribution")
    o = fdf["outcome"].value_counts().reset_index()
    o.columns = ["outcome", "cases"]
    fig2 = px.pie(o, names="outcome", values="cases", hole=0.45,
                  color_discrete_sequence=px.colors.sequential.Teal)
    fig2.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(style_fig(fig2), use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    st.markdown("#### Age distribution by diagnosis")
    fig3 = px.histogram(fdf, x="age", color="diagnosis", nbins=12, barmode="overlay",
                        color_discrete_sequence=px.colors.sequential.Teal, opacity=0.75)
    fig3.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(style_fig(fig3), use_container_width=True)
with c4:
    st.markdown("#### Risk by diagnosis")
    r = fdf.groupby(["diagnosis", "risk"]).size().reset_index(name="patients")
    fig4 = px.bar(r, x="diagnosis", y="patients", color="risk", barmode="stack",
                  color_discrete_map={"Low": "#1E8449", "Moderate": "#D4A017",
                                      "High": "#E67E22", "Critical": "#C0392B"})
    fig4.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10),
                       xaxis_tickangle=-20)
    st.plotly_chart(style_fig(fig4), use_container_width=True)

st.markdown("#### Data summary")
st.write(f"**{len(fdf)}** records in view · **{fdf['diagnosis'].nunique()}** diagnoses · "
         f"age range {int(fdf['age'].min())}–{int(fdf['age'].max())} · "
         "risk mix: " + ", ".join(f"{k} {v}" for k, v in Counter(fdf["risk"]).items()))
st.caption("Synthetic demo data. Trends illustrate platform capability, not epidemiology.")
disclaimer()
