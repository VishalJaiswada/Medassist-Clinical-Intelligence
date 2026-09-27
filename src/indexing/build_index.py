"""Build (or rebuild) the FAISS vector index from data/raw/.

Run:  python -m src.indexing.build_index
"""
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from src import config
from src.retrieval.retriever import RecordStore


def build() -> int:
    store = RecordStore()
    ids = store.list_ids()
    if not ids:
        raise SystemExit(f"No records found in {config.DATA_DIR}. Generate some first.")

    docs = [
        Document(page_content=store.load(pid), metadata={"patient_id": pid})
        for pid in ids
    ]
    print(f"Embedding {len(docs)} records with {config.EMBEDDING_MODEL} ...")
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    vs = FAISS.from_documents(docs, embeddings)
    vs.save_local(str(config.INDEX_DIR))
    print(f"Saved FAISS index to {config.INDEX_DIR}")
    return len(docs)


if __name__ == "__main__":
    build()
