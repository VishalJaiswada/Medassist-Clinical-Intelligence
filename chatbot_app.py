"""MedAssist — Streamlit frontend.

Run:  streamlit run app.py
"""
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.chatbot.engine import MedAssistEngine  # noqa: E402

st.set_page_config(
    page_title="MedAssist — Clinical AI Assistant",
    page_icon="🩺",
    layout="wide",
)

# ------------------------------------------------------------------ styling
st.markdown("""
<style>
    .hero {
        background: linear-gradient(120deg, #0f766e 0%, #0e7490 55%, #1d4ed8 100%);
        border-radius: 16px;
        padding: 26px 30px;
        color: white;
        margin-bottom: 18px;
        box-shadow: 0 6px 24px rgba(13, 90, 110, .25);
    }
    .hero h1 { color: white !important; margin: 0; font-size: 2rem; }
    .hero p { color: #e0f2f1 !important; margin: 6px 0 0 0; }
    .stat-card {
        background: #f0fdfa;
        border: 1px solid #99f6e4;
        border-radius: 12px;
        padding: 10px 14px;
        text-align: center;
    }
    .case-chip {
        display: inline-block;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1e40af;
        border-radius: 999px;
        padding: 4px 14px;
        margin: 3px 4px 3px 0;
        font-size: .85rem;
        font-weight: 600;
    }
    .disclaimer {
        background: #fffbeb;
        border: 1px solid #fcd34d;
        border-radius: 12px;
        padding: 12px 16px;
        color: #92400e;
        font-size: .9rem;
        margin-top: 14px;
    }
    .stChatMessage { border-radius: 14px; }
    section[data-testid="stSidebar"] { background: #f8fafc; }
    div[data-testid="stExpander"] { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading MedAssist engine...")
def get_engine() -> MedAssistEngine:
    return MedAssistEngine()


engine = get_engine()

SAMPLE_QUESTIONS = [
    "What is the diagnosis for patient P001?",
    "What medications is patient P002 taking?",
    "Summarize the report for patient P003.",
    "Find patients similar to patient P004.",
    "Compare patients P001 and P005.",
    "I have fever and dry cough for 4 days, what could it be?",
]

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.title("🩺 MedAssist")
    st.caption("Grounded clinical AI over patient records")
    try:
        status = engine.status()
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='stat-card'><b>{status['patients']}</b><br><small>records</small></div>",
                    unsafe_allow_html=True)
        c2.markdown(f"<div class='stat-card'><b>{'✅' if status['index_ready'] else '⚠️'}</b><br><small>index</small></div>",
                    unsafe_allow_html=True)
        st.caption(f"LLM: `{status['groq_model']}`")
        if not status["index_ready"]:
            st.warning("Vector index missing — run `python -m src.indexing.build_index`")
    except Exception as e:  # noqa: BLE001
        st.error(f"Engine status check failed: {e}")

    if st.button("🔄 Reset conversation", use_container_width=True):
        engine.reset()
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("✨ Try asking")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, key=f"sample-{q}"):
            st.session_state.pending = q
            st.session_state.go_chat = True

    st.divider()
    st.markdown(
        "<div class='disclaimer'>⚠️ <b>Educational demo.</b> Answers come only from the "
        "synthetic records in <code>data/raw/</code>. Not a medical device — always "
        "consult a qualified doctor.</div>",
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------ header
st.markdown(
    "<div class='hero'><h1>🩺 MedAssist</h1>"
    "<p>Clinical question answering · Report summarization · Similar-patient search · "
    "Symptom-based decision support — every answer grounded in patient records.</p></div>",
    unsafe_allow_html=True,
)

tab_chat, tab_symptom, tab_records = st.tabs(
    ["💬 Chat", "🩺 Symptom Checker", "📋 Browse Records"])

# ============================================================ TAB 1 — chat
with tab_chat:
    if st.session_state.pop("go_chat", False):
        pass  # pending question below is picked up in this tab

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("citations"):
                with st.expander("📎 Sources (record sections used)"):
                    for c in msg["citations"]:
                        st.markdown(f"**{c['patient_id']}** · *{c['section']}*")
                        st.caption(c["excerpt"])

    prompt = st.chat_input(
        "Ask about a patient — or describe symptoms…")
    if "pending" in st.session_state:
        prompt = st.session_state.pop("pending")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("🔎 Finding the right records…"):
                try:
                    result = engine.ask(prompt)
                    answer = result["answer"]
                    citations = result.get("citations", [])
                    meta = (f"_{result.get('intent', '')}"
                            + (f" · patients: {', '.join(result.get('patient_ids', []))}"
                               if result.get("patient_ids") else "")
                            + f" · ⏱ {result.get('elapsed_s', '?')}s_")
                except Exception as e:  # noqa: BLE001
                    answer = (f"⚠️ Something went wrong: `{e}`\n\n"
                              "Check that your API key is set in `.env` and the vector "
                              "index is built (`python -m src.indexing.build_index`).")
                    citations, meta = [], ""
            st.markdown(answer)
            st.caption(meta)
            if citations:
                with st.expander("📎 Sources (record sections used)"):
                    for c in citations:
                        st.markdown(f"**{c['patient_id']}** · *{c['section']}*")
                        st.caption(c["excerpt"])
        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "citations": citations})

# =================================================== TAB 2 — symptom check
with tab_symptom:
    st.subheader("🩺 Symptom Checker")
    st.write("Describe your symptoms (or paste a report). MedAssist finds the most "
             "similar historical cases and shows what conditions those cases had, "
             "how they were treated, and recovery guidance.")

    col_a, col_b = st.columns(2)
    age = col_a.number_input("Age (optional)", min_value=0, max_value=120, value=0,
                             help="Leave 0 to skip")
    sex = col_b.selectbox("Sex (optional)", ["", "male", "female", "other"])

    symptoms = st.text_area(
        "Describe the symptoms",
        placeholder=("e.g. I have had fever, dry cough and chest tightness for 4 days. "
                     "No prior conditions. Blood pressure 130/85."),
        height=130,
    )
    if st.button("🔍 Analyze symptoms", type="primary", use_container_width=True):
        if not symptoms.strip():
            st.warning("Please describe the symptoms first.")
        else:
            with st.spinner("🔎 Finding similar cases…"):
                try:
                    r = engine.analyze_symptoms(
                        symptoms,
                        age=age or None,
                        sex=sex or None,
                    )
                except Exception as e:  # noqa: BLE001
                    st.error(f"⚠️ Something went wrong: `{e}`")
                    r = None
            if r:
                similar = r.get("similar", [])
                if similar:
                    st.markdown("**Most similar historical cases:**")
                    st.markdown("".join(
                        f"<span class='case-chip'>{s['patient_id']} "
                        f"· score {s['score']}</span>"
                        for s in similar), unsafe_allow_html=True)
                st.markdown("### Assessment")
                st.markdown(r["answer"])
                st.caption(f"⏱ {r.get('elapsed_s', '?')}s")
                if r.get("citations"):
                    with st.expander("📎 Cases this assessment is based on"):
                        for c in r["citations"]:
                            st.markdown(f"**{c['patient_id']}** · *{c['section']}*")
                            st.caption(c["excerpt"])
    st.markdown(
        "<div class='disclaimer'>⚠️ This tool suggests <b>possibilities based on similar "
        "past cases</b> — it is not a diagnosis. Always consult a qualified doctor, "
        "especially for severe or worsening symptoms.</div>",
        unsafe_allow_html=True,
    )

# =================================================== TAB 3 — browse records
with tab_records:
    st.subheader("📋 Browse patient records")
    try:
        ids = engine.store.list_ids()
    except Exception:  # noqa: BLE001
        ids = []
    if not ids:
        st.warning("No records found in `data/raw/`.")
    else:
        pid = st.selectbox("Select a patient", ids)
        if pid:
            record = engine.store.load(pid)
            with st.expander(f"📄 Full record — {pid}", expanded=False):
                st.text(record)
            if st.button(f"📝 Summarize {pid}", type="primary"):
                with st.spinner("Summarizing…"):
                    try:
                        r = engine.ask(f"Summarize the report for patient {pid}.")
                        st.markdown(r["answer"])
                        st.caption(f"⏱ {r.get('elapsed_s', '?')}s")
                    except Exception as e:  # noqa: BLE001
                        st.error(f"⚠️ Something went wrong: `{e}`")
            if st.button(f"🔍 Find similar to {pid}"):
                with st.spinner("Searching…"):
                    try:
                        r = engine.ask(f"Find patients similar to patient {pid}.")
                        st.markdown(r["answer"])
                        st.caption(f"⏱ {r.get('elapsed_s', '?')}s")
                    except Exception as e:  # noqa: BLE001
                        st.error(f"⚠️ Something went wrong: `{e}`")

st.divider()
st.caption("MedAssist · grounded RAG over synthetic patient records · "
           "not a medical device. Built with Streamlit, LangChain, LangGraph & FAISS.")
