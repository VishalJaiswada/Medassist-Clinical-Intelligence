"""⚙️ Settings — configuration, data management, model info."""
import subprocess
import sys

import streamlit as st

from src import config
from src.ui import disclaimer, get_backend, page_setup, render_sidebar

page_setup("Settings", icon="⚙️")
render_sidebar()

st.title("⚙️ Settings")

st.markdown("### 🔌 AI configuration")
st.write(f"**LLM provider:** `{config.LLM_PROVIDER}`")
if config.LLM_PROVIDER == "groq":
    st.write(f"**Groq model:** `{config.GROQ_MODEL}`")
    import os
    st.write(f"**API key:** {'✅ configured' if os.getenv('GROQ_API_KEY') else '❌ missing — set GROQ_API_KEY in .env'}")
st.write(f"**Embedding model:** `{config.EMBEDDING_MODEL}`")
st.write(f"**Reranker:** {'enabled' if config.RERANK_ENABLED else 'disabled (faster)'} — "
         "set `MEDASSIST_RERANK=0` in `.env` for faster CPU responses")

st.markdown("### 🗄️ Data management")
store, index = get_backend()
st.write(f"**Patient records:** {len(store.list_ids())} in `data/raw/`")
st.write(f"**Vector index:** {'✅ built' if index.ready else '❌ not built'} in `data/faiss_index/`")

c1, c2 = st.columns(2)
with c1:
    n = st.number_input("Regenerate synthetic records", min_value=10, max_value=200, value=60)
    if st.button("🔄 Regenerate data"):
        with st.spinner("Generating…"):
            r = subprocess.run([sys.executable, "-m", "src.data_gen.generate",
                                "--count", str(int(n)), "--seed", "42"],
                               capture_output=True, text=True, cwd=".")
        if r.returncode == 0:
            st.success(r.stdout.strip() or "Data regenerated.")
            st.cache_resource.clear()
            st.rerun()
        else:
            st.error(r.stderr[-500:] or "Generation failed.")
with c2:
    if st.button("🧲 Rebuild vector index"):
        with st.spinner("Building index… (downloads embedding model on first run)"):
            r = subprocess.run([sys.executable, "-m", "src.indexing.build_index"],
                               capture_output=True, text=True, cwd=".")
        if r.returncode == 0:
            st.success("Index rebuilt.")
            st.cache_resource.clear()
            st.rerun()
        else:
            st.error(r.stderr[-500:] or "Index build failed.")

st.markdown("### 🔐 Privacy & safety")
st.markdown("""
- Demo runs on **synthetic data only** — no real patient information.
- Historical cases are shown with **anonymized case IDs** (no names).
- AI outputs are **decision support**, never diagnoses or guaranteed predictions.
- Role indicator, audit logging and encryption are deployment concerns for a
  production install (see README → *Production hardening*).
""")

st.markdown("### ℹ️ About")
st.caption("MedAssist Clinical Intelligence Platform · demo build 2026-09-25 · "
           "Streamlit + FAISS + LangChain")

disclaimer()
