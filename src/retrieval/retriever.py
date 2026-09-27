"""Record loading (from .txt files) and FAISS vector search (lazy-loaded)."""
import re
from pathlib import Path

from src import config


def normalise_id(raw: str) -> str:
    """'P7' / 'p007' -> 'P007'."""
    num = re.sub(r"\D", "", raw)
    return f"{config.ID_PREFIX}{int(num):03d}" if num else raw.upper()


class RecordStore:
    """Reads patient records straight from data/raw/patient_P001.txt files."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir or config.DATA_DIR)

    def path_for(self, patient_id: str) -> Path:
        return self.data_dir / f"patient_{normalise_id(patient_id)}.txt"

    def load(self, patient_id: str) -> str | None:
        p = self.path_for(patient_id)
        return p.read_text(encoding="utf-8") if p.exists() else None

    def exists(self, patient_id: str) -> bool:
        return self.path_for(patient_id).exists()

    def list_ids(self) -> list[str]:
        ids = []
        for f in sorted(self.data_dir.glob("patient_*.txt")):
            m = re.search(r"patient_([A-Za-z0-9]+)\.txt", f.name)
            if m:
                ids.append(m.group(1).upper())
        return ids


class VectorIndex:
    """FAISS-backed similarity search over whole patient records. Loads lazily."""

    def __init__(self, index_dir: Path | None = None):
        self.index_dir = Path(index_dir or config.INDEX_DIR)
        self._vs = None

    def _load(self):
        if self._vs is not None:
            return self._vs
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
        if not self.index_dir.exists():
            raise FileNotFoundError(
                f"Vector index not found at {self.index_dir}. "
                "Build it first:  python -m src.indexing.build_index"
            )
        self._vs = FAISS.load_local(
            str(self.index_dir), embeddings, allow_dangerous_deserialization=True
        )
        return self._vs

    def similar(self, query_text: str, k: int = 5, exclude: str | None = None):
        """Return [(patient_id, score), ...] most similar records (lower score = closer)."""
        vs = self._load()
        hits = vs.similarity_search_with_score(query_text, k=k + 1)
        out = []
        for doc, score in hits:
            pid = (doc.metadata.get("patient_id") or "").upper()
            if exclude and pid == normalise_id(exclude):
                continue
            out.append((pid, float(score)))
            if len(out) >= k:
                break
        return out

    @property
    def ready(self) -> bool:
        return self.index_dir.exists()
