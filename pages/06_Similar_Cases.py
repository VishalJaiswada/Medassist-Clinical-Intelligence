"""🔎 Similar Cases — standalone explorer with filters."""
import streamlit as st

from src.analysis import patients, service, similarity
from src.ui import (disclaimer, get_backend, page_setup, render_sidebar,
                    similar_case_card)

page_setup("Similar Cases", icon="🔎")
render_sidebar()
store, index = get_backend()

st.title("🔎 Similar Cases")
st.caption("Find historical patients resembling a reference case. Cases are anonymized.")

# ---------------------------------------------------------- reference picker
ref_kind, ref_pid = st.session_state.get("similar_ref") or (None, None)
options = ["New-patient intake (current)"] + [
    f"{pid} — {patients.parse_record(pid, store.load(pid))['diagnosis'][:45]}"
    for pid in store.list_ids()]
default_idx = 0
if ref_kind == "existing" and ref_pid:
    match = [i for i, o in enumerate(options) if o.startswith(ref_pid)]
    default_idx = match[0] if match else 0
elif st.session_state.intake:
    default_idx = 0

choice = st.selectbox("Reference", options, index=default_idx)
if choice.startswith("New-patient"):
    if not st.session_state.intake:
        st.info("No intake in progress — complete ➕ New Patient first, or pick a record below.")
        st.stop()
    current = service.intake_to_current(st.session_state.intake)
    current_text = service.intake_text(st.session_state.intake)
    exclude = None
else:
    pid = choice.split(" — ")[0]
    current = patients.parse_record(pid, store.load(pid))
    current_text = store.load(pid)
    exclude = pid

st.markdown(f"**Reference:** {current.get('name') or current.get('patient_id')} · "
            f"{current.get('age')}y {current.get('sex')} · "
            f"symptoms: {', '.join(current.get('symptoms', [])[:6]) or '—'}")

# ------------------------------------------------------------------- filters
st.markdown("### Filters")
f1, f2, f3 = st.columns(3)
with f1:
    min_sim = st.slider("Minimum similarity", 0, 100, 40)
with f2:
    only_diag = st.text_input("Diagnosis contains", placeholder="e.g. pneumonia")
with f3:
    k = st.slider("Max results", 3, 10, 5)

with st.spinner("Searching historical cases…"):
    results = similarity.find_similar_explained(current, current_text, store, index,
                                                k=10, exclude=exclude)
results = [r for r in results if r["similarity"] >= min_sim]
if only_diag:
    results = [r for r in results if only_diag.lower() in (r["diagnosis"] or "").lower()]
results = results[:k]

st.markdown(f"### {len(results)} case(s) found")
for c in results:
    similar_case_card(c, "explorer")
    with st.expander(f"Case detail — {c['case_id']} (anonymized)"):
        st.write(f"**Diagnosis:** {c['diagnosis']}")
        st.write(f"**Treatment received:** {'; '.join(c['treatment']) or '—'}")
        st.write(f"**Outcome:** {c['outcome'] or 'not recorded'}")

disclaimer()
