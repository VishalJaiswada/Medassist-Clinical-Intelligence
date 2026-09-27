"""📑 Reports — generate, preview, download clinical reports."""
import streamlit as st

from src.analysis import insights
from src.ui import (analysis_for_current, disclaimer, get_backend, page_setup,
                    render_sidebar, require_llm)

page_setup("Reports", icon="📑")
render_sidebar()
store, index = get_backend()

st.title("📑 Clinical Reports")

analysis = analysis_for_current(store, index, k=5)
if not analysis or analysis.get("error"):
    st.info("Run an analysis first (➕ New Patient, or open a patient → AI insights).")
    st.stop()
current, similar, patterns = analysis["current"], analysis["similar"], analysis["patterns"]

kind = st.selectbox("Report type", [
    "Clinical Analysis Report",
    "Patient Summary Report",
    "Similar Case Report",
    "Follow-up Report",
])

if st.button("⚙️ Generate report", type="primary"):
    with st.spinner("Generating report…"):
        # ensure AI sections exist where the key allows it
        if require_llm():
            analysis.setdefault("summary", insights.patient_summary(current))
            if similar:
                analysis.setdefault("risks", insights.risk_synthesis(current, similar, patterns))
        st.session_state.report_md = insights.build_report(
            kind, current, similar, patterns,
            summary=analysis.get("summary", ""),
            comparison=analysis.get("comparison", ""),
            risks=analysis.get("risks", ""))
    st.success("Report generated.")

md = st.session_state.report_md
if md:
    st.markdown("### Preview")
    st.markdown(md)
    st.download_button("⬇️ Download (.md)", data=md.encode("utf-8"),
                       file_name=f"{kind.replace(' ', '_').lower()}.md",
                       mime="text/markdown", use_container_width=True)
    st.caption("Tip: open the downloaded file in any markdown viewer, or print it from the preview above.")
else:
    st.info("Choose a report type and click **Generate report**.")

disclaimer()
