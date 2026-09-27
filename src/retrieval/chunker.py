"""Split a patient record into sections (chunks) on '## ' headers."""
import re


def chunk_record(text: str) -> list[dict]:
    """Return [{'title': ..., 'text': ...}] chunks, one per section."""
    parts = re.split(r"(?m)^##\s+", text)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        chunks.append({"title": title, "text": f"## {title}\n{body}"})
    return chunks
