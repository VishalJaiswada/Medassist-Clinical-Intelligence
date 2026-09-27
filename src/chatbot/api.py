"""FastAPI backend for MedAssist.

Run:  uvicorn src.chatbot.api:app --reload --port 8000
"""
from fastapi import FastAPI
from pydantic import BaseModel

from src.chatbot.engine import MedAssistEngine

app = FastAPI(title="MedAssist API")
_engine = MedAssistEngine()


class AskRequest(BaseModel):
    question: str


class SymptomsRequest(BaseModel):
    description: str
    age: int | None = None
    sex: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", **_engine.status()}


@app.get("/patients")
def patients():
    return {"patients": _engine.store.list_ids()}


@app.post("/ask")
def ask(req: AskRequest):
    return _engine.ask(req.question)


@app.post("/symptoms")
def symptoms(req: SymptomsRequest):
    """Symptom-based decision support: similar cases + likely conditions."""
    return _engine.analyze_symptoms(req.description, age=req.age, sex=req.sex)


@app.post("/reset")
def reset():
    _engine.reset()
    return {"status": "conversation reset"}
