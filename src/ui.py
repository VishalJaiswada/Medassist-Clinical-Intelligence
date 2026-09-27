"""Shared UI shell for the MedAssist Clinical Intelligence Platform.

Premium healthcare SaaS theme: deep navy-to-teal sidebar, soft light surfaces,
vibrant teal actions, green/amber/red used only for clinical status. All pages call
`page_setup()` then `render_sidebar()`.
"""
import streamlit as st

RISK_COLORS = {"Critical": "#C0392B", "High": "#E67E22",
               "Moderate": "#D4A017", "Low": "#1E8449"}

CSS = """
<style>
/* ================= MedAssist dark clinical theme ================= */
:root{
  --teal:#14B8A6; --teal-dark:#0D9488;
  --ink:#E8EEF6; --muted:#9AA8BD; --line:#26334D; --bg:#0D1526; --surface:#16233A;
}
[data-testid="stAppViewContainer"]{ background:var(--bg); }
[data-testid="stHeader"]{ background:rgba(13,21,38,0); }
h1,h2,h3{ color:#F2F6FB; }

/* ---------- sidebar : deep navy -> teal ---------- */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0B2447 0%,#123058 55%,#0C5B60 135%);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
[data-testid="stSidebar"] nav a{ color:#EAF1F8 !important; }
[data-testid="stSidebar"] hr{ border-color:rgba(255,255,255,.18); }
/* sidebar buttons: readable white text on translucent pill */
[data-testid="stSidebar"] .stButton > button{
  background:rgba(255,255,255,.13) !important; color:#FFFFFF !important;
  border:1px solid rgba(255,255,255,.30) !important; border-radius:10px; font-weight:600;
}
[data-testid="stSidebar"] .stButton > button:hover{ background:rgba(255,255,255,.24) !important; }
[data-testid="stSidebar"] .stButton > button p{ color:#FFFFFF !important; }
/* sidebar search stays a white box with dark text */
[data-testid="stSidebar"] input{
  background:#FFFFFF !important; color:#17293F !important; border-radius:10px;
}
[data-testid="stSidebar"] input::placeholder{ color:#8A99AD !important; }

/* ---------- brand & user card ---------- */
.brand{ font-size:1.4rem; font-weight:800; letter-spacing:.4px; color:#FFFFFF !important; }
.brand small{ display:block; font-size:.72rem; font-weight:400; opacity:.72; color:#CFE3E2 !important; }
.usercard{ background:rgba(255,255,255,.09); border:1px solid rgba(255,255,255,.14);
  border-radius:14px; padding:.7rem .9rem; margin:.8rem 0; color:#FFFFFF !important; }
.usercard b{ color:#FFFFFF !important; }
.rolebadge{ display:inline-block; background:linear-gradient(135deg,#14B8A6,#0D9488);
  border-radius:999px; padding:.16rem .75rem; font-size:.72rem; font-weight:700; color:#06231F !important; }

/* ---------- cards & metric cards : dark surfaces ---------- */
.metric{ background:var(--surface); border:1px solid var(--line); border-left:5px solid var(--teal);
  border-radius:14px; padding:1rem 1.15rem; box-shadow:0 3px 14px rgba(0,0,0,.35); }
.metric .lbl{ font-size:.74rem; color:#93A3BB; font-weight:700;
  text-transform:uppercase; letter-spacing:.7px; }
.metric .val{ font-size:2rem; font-weight:800; color:#FFFFFF; }
.metric .sub{ font-size:.82rem; color:#8A99AD; }
.card{ background:var(--surface); border:1px solid var(--line); border-radius:14px;
  padding:1.1rem 1.2rem; box-shadow:0 3px 14px rgba(0,0,0,.35); margin-bottom:1rem; color:var(--ink); }
.card h4{ margin:0 0 .4rem 0; color:#FFFFFF; }
.card b{ color:#FFFFFF; }
.pill{ display:inline-block; border-radius:999px; padding:.2rem .8rem;
  font-size:.75rem; font-weight:700; color:#fff; }
.casechip{ display:inline-block; background:rgba(20,184,166,.14); color:#5EEAD4; border-radius:8px;
  padding:.25rem .6rem; font-size:.78rem; font-weight:700; margin:.15rem .25rem .15rem 0; }
.bar{ height:10px; border-radius:999px; background:#26334D; overflow:hidden; margin:.25rem 0 .6rem 0; }
.bar > div{ height:100%; border-radius:999px; background:linear-gradient(90deg,#14B8A6,#2DD4BF); }

/* ---------- notice boxes : dark tints ---------- */
.disclaimer{ background:rgba(212,160,23,.10); border:1px solid #7A5E14; border-radius:12px;
  padding:.8rem 1rem; font-size:.85rem; color:#F2D47E; margin:1rem 0; }
.disclaimer b{ color:#F7E3A1; }
.safebar{ background:rgba(30,132,73,.12); border:1px solid #1E7A45; border-radius:12px;
  padding:.8rem 1rem; font-size:.85rem; color:#86DC9A; margin:1rem 0; }

/* ---------- timeline ---------- */
.timeline{ border-left:3px solid var(--teal); margin-left:.6rem; padding-left:1.2rem; }
.timeline .ev{ position:relative; margin-bottom:1rem; color:var(--ink); }
.timeline .ev::before{ content:""; position:absolute; left:-1.62rem; top:.25rem;
  width:12px; height:12px; border-radius:50%; background:var(--teal);
  border:2px solid rgba(255,255,255,.85); box-shadow:0 0 0 2px var(--teal); }

/* ---------- buttons, tabs, tables ---------- */
.stButton > button{ border-radius:10px; font-weight:600; }
.stButton > button[kind="primary"]{
  background:linear-gradient(135deg,#14B8A6 0%,#0D9488 100%) !important;
  border:none !important; color:#06231F !important;
}
.stButton > button[kind="primary"] p{ color:#06231F !important; }
.stButton > button[kind="primary"]:hover{ filter:brightness(1.1); }
div[data-testid="stDataFrame"]{ border-radius:12px; overflow:hidden; }
.stTabs [data-baseweb="tab"]{ font-weight:600; }
</style>
"""

DISCLAIMER_MD = ("⚠️ **Clinical decision support — not a diagnosis.** AI outputs are generated from "
                 "historical patterns and must be reviewed by a qualified clinician. "
                 "Historical association does not imply causation.")


@st.cache_resource(show_spinner=False)
def _backend():
    """Build store + vector index once per session (lazy, offline-safe)."""
    from src import config
    from src.retrieval.retriever import RecordStore, VectorIndex

    store = RecordStore(config.DATA_DIR)
    index = VectorIndex(config.INDEX_DIR)
    if not index.ready:
        from src.indexing.build_index import build

        build()
    return store, index


def get_backend():
    return _backend()


def llm_available() -> bool:
    try:
        import os

        from src import config
        if config.LLM_PROVIDER == "groq":
            return bool(os.getenv("GROQ_API_KEY"))
        return True
    except Exception:
        return False


def page_setup(title: str, icon: str = "🏥"):
    st.set_page_config(page_title=f"{title} · MedAssist", page_icon=icon,
                       layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)
    for key, default in [("current_pid", None), ("intake", None), ("analysis", None),
                         ("compare_ids", []), ("similar_ref", None), ("report_md", "")]:
        st.session_state.setdefault(key, default)


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="brand">🩺 MedAssist<small>Clinical Intelligence Platform</small></div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="usercard">👩‍⚕️ <b>Dr. Demo User</b><br>'
                    '<span class="rolebadge">DOCTOR · DEMO</span></div>', unsafe_allow_html=True)
        q = st.text_input("🔍 Global search", placeholder="Patient ID, symptom, diagnosis…",
                          key="global_search", label_visibility="collapsed")
        if q:
            _global_search_results(q)
        st.divider()
        st.caption("Authorized demo environment · synthetic data only")
    return q


def _global_search_results(q: str):
    from src.analysis import patients
    store, _ = get_backend()
    ql = q.lower()
    hits = []
    for pid in store.list_ids():
        p = patients.parse_record(pid, store.load(pid))
        hay = f"{pid} {p['name']} {p['diagnosis']} {' '.join(p['symptoms'])}".lower()
        if ql in hay:
            hits.append(p)
        if len(hits) >= 8:
            break
    if not hits:
        st.info("No matches.")
        return
    for p in hits:
        if st.button(f"{p['patient_id']} · {p['diagnosis'][:38]}", key=f"gs_{p['patient_id']}"):
            st.session_state.current_pid = p["patient_id"]
            st.switch_page("pages/03_Patient_Profile.py")


def risk_badge(level: str) -> str:
    color = RISK_COLORS.get(level, "#93A3BB")
    return f'<span class="pill" style="background:{color}">{level} risk</span>'


def metric_card(label: str, value: str, sub: str = ""):
    st.markdown(f'<div class="metric"><div class="lbl">{label}</div>'
                f'<div class="val">{value}</div><div class="sub">{sub}</div></div>',
                unsafe_allow_html=True)


def similarity_bars(components: dict[str, float]):
    labels = {"symptoms": "Symptoms", "diagnosis": "Diagnosis", "history": "Medical history",
              "labs": "Lab findings", "age": "Age", "sex": "Sex"}
    for key, label in labels.items():
        v = components.get(key, 0)
        st.markdown(f"{label} — **{v:.0f}%**"
                    f'<div class="bar"><div style="width:{v}%"></div></div>',
                    unsafe_allow_html=True)


def style_fig(fig):
    """Match a Plotly figure to the dark theme (transparent bg, light text)."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#DCE5F2"),
    )
    return fig


def disclaimer():
    st.markdown(f'<div class="disclaimer">{DISCLAIMER_MD}</div>', unsafe_allow_html=True)


def require_llm() -> bool:
    if not llm_available():
        st.warning("AI text generation needs an LLM API key (see Settings → Configuration). "
                   "Similarity search, analytics and reports structure still work offline.")
        return False
    return True


def analysis_for_current(store, index, k: int = 5):
    """Return cached analysis for the active context (intake or existing patient)."""
    from src.analysis import service
    if st.session_state.intake:
        if (not st.session_state.analysis
                or st.session_state.analysis.get("kind") != "intake"):
            with st.spinner("Analyzing patient…"):
                st.session_state.analysis = {
                    "kind": "intake",
                    **service.analyze_intake(st.session_state.intake, store, index, k=k),
                }
        return st.session_state.analysis
    if st.session_state.current_pid:
        if (not st.session_state.analysis
                or st.session_state.analysis.get("kind") != st.session_state.current_pid):
            with st.spinner("Analyzing patient…"):
                st.session_state.analysis = {
                    "kind": st.session_state.current_pid,
                    **service.analyze_existing(st.session_state.current_pid, store, index, k=k),
                }
        return st.session_state.analysis
    return None


def similar_case_card(c: dict, key_prefix: str):
    st.markdown(f'<div class="card"><h4>{c["case_id"]} '
                f'<span class="pill" style="background:#0E7C7B">{c["similarity"]:.0f}% similar</span></h4>'
                f"<b>{c['diagnosis'] or 'Diagnosis not recorded'}</b><br>"
                f"Age {c['age']} · {c['sex']}<br>"
                f"<span style='color:#9AA8BD;font-size:.85rem'>"
                f"Symptoms: {', '.join(c['symptoms'][:6]) or '—'}</span></div>",
                unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔎 Why similar?", key=f"{key_prefix}_why_{c['case_id']}"):
            st.session_state[f"why_{c['case_id']}"] = True
    with col2:
        if st.button("⚖️ Add to compare", key=f"{key_prefix}_cmp_{c['case_id']}"):
            if c["patient_id"] not in st.session_state.compare_ids:
                st.session_state.compare_ids.append(c["patient_id"])
            st.toast(f"{c['case_id']} added to comparison")
    if st.session_state.get(f"why_{c['case_id']}"):
        with st.expander(f"Similarity breakdown — {c['case_id']}", expanded=True):
            similarity_bars(c["components"])
            st.caption("Why am I seeing this? Component scores compare extracted clinical "
                       "features between the current patient and this historical case. "
                       "The shortlist itself comes from semantic vector search over all records.")
