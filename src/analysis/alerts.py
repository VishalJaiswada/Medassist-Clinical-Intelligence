"""Rule-based clinical alerts (neutral language, no alarmism).

Categories: follow-up required, missing clinical information, high-risk
pattern detected, report-ready reminders. These are deterministic rules over
the records — the AI layer never invents alerts.
"""
from src.analysis import patients


def scan_patients(store) -> list[dict]:
    alerts = []
    for pid in store.list_ids():
        record = store.load(pid)
        if not record:
            continue
        p = patients.parse_record(pid, record)
        level, reasons = patients.risk_level(p)

        if level in ("High", "Critical"):
            alerts.append({
                "severity": "high" if level == "High" else "critical",
                "category": "High-risk pattern detected",
                "title": f"{p['patient_id']} — {p['diagnosis']}",
                "detail": f"Rule-based risk estimate: {level} ({'; '.join(reasons)}). "
                          "Review promptly per local protocol.",
                "patient_id": pid,
            })
        if "follow-up" in p["discharge"].lower() or "review in" in p["discharge"].lower():
            alerts.append({
                "severity": "info",
                "category": "Follow-up required",
                "title": f"{p['patient_id']} — scheduled follow-up",
                "detail": (p["discharge"][:220] + "…") if len(p["discharge"]) > 220 else p["discharge"],
                "patient_id": pid,
            })
        for m in patients.missing_data(p):
            alerts.append({
                "severity": "low",
                "category": "Missing clinical information",
                "title": f"{p['patient_id']} — {m} not recorded",
                "detail": "Consider completing this section for a reliable analysis.",
                "patient_id": pid,
            })
    order = {"critical": 0, "high": 1, "info": 2, "low": 3}
    alerts.sort(key=lambda a: order[a["severity"]])
    return alerts
