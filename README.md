# 🩺 MedAssist — Clinical Intelligence Platform


[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33%2B-FF4B4B.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-121212.svg)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-6B46C1.svg)](https://github.com/langchain-ai/langgraph)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-orange.svg)](https://github.com/facebookresearch/faiss)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)
[![Build](https://img.shields.io/badge/Build-2026--09--26-teal.svg)](#)

**Enterprise-grade AI Clinical Decision Support · RAG + Explainable Similarity · Multi-LLM**

[Features](#-key-features) · [Architecture](#-architecture) · [Quickstart](#-quickstart) · [API](#-rest-api) · [Security](#-security--compliance) · [Tech Stack](#-tech-stack)

</div>

---

> ⚠️ **Clinical Decision Support Notice:** MedAssist is an AI decision-support system designed for clinicians, hospitals, and authorized healthcare personnel. It provides grounded contextual intelligence and similar case matching — it does **not** provide definitive automated diagnosis. All AI outputs distinguish historical facts from estimates, communicate uncertainty metrics, and require professional clinical evaluation. Historical correlation does not equal causation.

---

## 📌 Executive Overview

**MedAssist** is an enterprise-grade AI Clinical Intelligence Platform that assists healthcare professionals in analyzing patient symptoms, historical timelines, medical records, and diagnostic patterns. Grounded in institutional data, MedAssist uses **Retrieval-Augmented Generation (RAG)** combined with a transparent **multi-factor similarity re-ranking engine** to deliver explainable, safe, and auditable clinical insights.

### What Makes MedAssist Different?

| Principle | Implementation |
|---|---|
| 🔍 **Explainability First** | Every similarity score is broken into 6 labeled clinical components — not just a percentage |
| 🔒 **Grounded Answers** | LLM answers are anchored to retrieved patient record excerpts — never hallucinated |
| ⚠️ **Uncertainty-Aware** | All AI outputs are labeled as estimates; rule-based logic handles risk & alerts |
| 🏥 **Clinician-Centric** | Designed around real clinical workflows: intake → analysis → comparison → report |
| 🛡️ **Privacy-Ready** | Runs fully offline via Ollama; anonymized historical case IDs (CASE-0001) |

### Two Complementary Interfaces

**1. 🏥 Clinical Intelligence Workstation (`app.py`)**
A modern, SaaS-style multi-page clinical dashboard with patient registry, intake pipeline, explainable similar case matching, side-by-side comparison, report generation, population analytics, and safety alerts.

**2. 💬 Conversational Clinical Chatbot (`chatbot_app.py`)**
An interactive, multi-tab conversational interface powered by LangGraph for direct grounded clinical Q&A, symptom evaluation, and instant decision support.

---

## 🌟 Key Features

### 🏥 Clinical Workstation — 11 Pages

| Page | Feature | Highlights |
|---|---|---|
| 01 Dashboard | Executive KPI overview | Admission trends, diagnosis distribution, recent activity |
| 02 Patients | Searchable patient registry | Filter by condition, risk level, date range |
| 03 Patient Profile | Full clinical chart | Visual timeline, vitals, labs, history, risk badge |
| 04 New Patient | Intake & instant analysis | Symptom auto-complete, vitals form, full pipeline trigger |
| 05 AI Insights | LLM-powered analysis | Patient summary, similar cases, risk synthesis, patterns |
| 06 Similar Cases | Historical case search | Anonymized cases, 6-factor similarity breakdown per case |
| 07 Comparison | Side-by-side analysis | Parameter table + LLM comparison narrative |
| 08 Reports | Clinical report generator | 11-section structured reports, `.md` download |
| 09 Analytics | Population health | Plotly charts: age, conditions, risk, outcomes, trends |
| 10 Alerts | Safety alerts engine | Rule-based; Critical → High → Info → Low prioritized |
| 11 Settings | System configuration | LLM config, API keys, reranking, index rebuild |

### 💬 Conversational Chatbot — 3 Tabs

| Tab | Feature |
|---|---|
| 💬 Chat | Multi-turn Q&A with citation expanders and intent metadata |
| 🩺 Symptom Checker | Guided symptom analysis → 4-section clinical assessment from similar cases |
| 📋 Browse Records | Patient selector → full record view → LLM summary → similar search |

---

## 🧠 Architecture

### High-Level System Architecture

```
╔═══════════════════════════════════════════════════════════════╗
║                       USER INTERFACES                         ║
║  ┌─────────────────────────┐  ┌──────────────────────────┐   ║
║  │  Streamlit Workstation  │  │   Streamlit Chatbot       │   ║
║  │  11-page SaaS dashboard │  │   Chat · Symptom · Browse │   ║
║  └────────────┬────────────┘  └──────────────┬───────────┘   ║
╚═══════════════╪══════════════════════════════╪═══════════════╝
                │                              │
╔═══════════════╪══════════════════════════════╪═══════════════╗
║                     APPLICATION ENGINE                        ║
║     src/ui.py                   src/chatbot/engine.py         ║
║     page_setup() render_sidebar()  MedAssistEngine            ║
║     Shared UI design system        .ask() .analyze_symptoms() ║
║                                                               ║
║  ┌────────────────────── ANALYSIS ENGINE ──────────────────┐  ║
║  │  patients.py  · similarity.py  · insights.py            │  ║
║  │  alerts.py    · service.py                              │  ║
║  └──────────────────────────────────────────────────────────┘  ║
║                                                               ║
║  ┌── src/chatbot/ ──┐   ┌──────── RETRIEVAL LAYER ─────────┐  ║
║  │ llm.py           │   │  retriever.py — RecordStore       │  ║
║  │ memory.py        │   │  retriever.py — VectorIndex(FAISS)│  ║
║  │ api.py           │   │  reranker.py  — Cross-encoder     │  ║
║  └──────────────────┘   └───────────────────────────────────┘  ║
║                                                               ║
║  src/router/ (intent.py · dispatcher.py)                     ║
║  src/api/    (FastAPI REST server)                           ║
║                                                               ║
║  ┌───────────────────── DATA LAYER ────────────────────────┐  ║
║  │  data/raw/patient_P001.txt … P060.txt                  │  ║
║  │  data/faiss_index/  (index.faiss + index.pkl)           │  ║
║  │  src/data_gen/generate.py  (synthetic record maker)     │  ║
║  └──────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════╝
```

### AI Pipeline — End to End

```
Patient Presentation (Intake / Question / Symptoms)
          │
          ▼
   Intent Classification  ──────────────────────────────────────┐
   (patient_qa / similar_cases / diagnosis_support / summary)   │
          │                                                      │
          ▼                                                      │
   FAISS Semantic Vector Search                                  │
   all-mpnet-base-v2 → k×3 candidate records                    │
          │                                                      │
          ▼                                                      │
   Multi-Factor Explainable Reranking                           │
   ┌─────────────────────────────────────┐                      │
   │  Symptoms (Jaccard)   35%           │                      │
   │  Diagnosis match      20%           │                      │
   │  Medical history      15%           │                      │
   │  Lab concordance      15%           │                      │
   │  Age proximity        10%           │                      │
   │  Sex match             5%           │                      │
   └─────────────────────────────────────┘                      │
          │                                                      │
          ▼                                                      │
   Cross-Encoder Reranking  (ms-marco-MiniLM-L-6-v2)           │
   [optional: MEDASSIST_RERANK=0 to skip]                       │
          │                                                      │
          ▼                                                      │
   LLM Reasoning with Grounded Context  ◄───────────────────────┘
   Safety-hardened prompt + retrieved excerpts
   Groq / OpenAI / Ollama — ONLY answers from context
          │
          ▼
   Clinical Output: Answer + Citations + Similarity Breakdown
   Reports / Comparison Tables / Alerts
```

### Multi-Factor Similarity Weights

| Component | Weight | Algorithm |
|---|---|---|
| 🩺 **Symptoms Overlap** | **35%** | Jaccard on deterministically extracted clinical keyword sets |
| 📋 **Diagnosis Match** | **20%** | Token Jaccard + ≥90% boost when core condition name matches |
| 📜 **Medical History** | **15%** | Token Jaccard on history text (stopwords stripped) |
| 🧪 **Lab Concordance** | **15%** | Jaccard on extracted lab test names |
| 👤 **Age Proximity** | **10%** | `max(0, 100 − |age1−age2| × 2)` |
| 👫 **Sex Match** | **5%** | 100% same · 50% unknown · 0% different |

---

## 📁 Repository Structure

```
medassist_platform_v2/
├── README.md
└── medassist_platform/
    ├── app.py                      # Clinical Workstation entrypoint
    ├── chatbot_app.py              # Conversational Chatbot entrypoint
    ├── requirements.txt            # Python dependencies
    ├── run.sh                      # One-shot setup & launch script
    ├── .env.example                # Environment variable template
    │
    ├── pages/                      # Streamlit multi-page workstation
    │   ├── 01_Dashboard.py
    │   ├── 02_Patients.py
    │   ├── 03_Patient_Profile.py
    │   ├── 04_New_Patient.py
    │   ├── 05_AI_Insights.py
    │   ├── 06_Similar_Cases.py
    │   ├── 07_Comparison.py
    │   ├── 08_Reports.py
    │   ├── 09_Analytics.py
    │   ├── 10_Alerts.py
    │   └── 11_Settings.py
    │
    └── src/                        # Core application engine
        ├── config.py               # Global config (env-driven, no hardcoded secrets)
        ├── ui.py                   # Shared UI shell, CSS design system, components
        ├── analysis/
        │   ├── patients.py         # Record parser, risk scoring, timeline builder
        │   ├── similarity.py       # Explainable multi-factor similarity engine
        │   ├── insights.py         # LLM clinical text generation (safety-hardened)
        │   ├── alerts.py           # Rule-based safety alert scanner
        │   └── service.py          # High-level analysis coordinator
        ├── chatbot/
        │   ├── engine.py           # MedAssistEngine — unified entry point
        │   ├── llm.py              # LLM provider factory (Groq/OpenAI/Ollama)
        │   ├── memory.py           # Multi-turn conversation memory
        │   └── api.py              # Chatbot REST API adapter
        ├── retrieval/
        │   ├── retriever.py        # RecordStore (file I/O) + VectorIndex (FAISS)
        │   ├── reranker.py         # Cross-encoder reranking
        │   └── chunker.py          # Record section chunker
        ├── router/
        │   ├── intent.py           # IntentClassifier (keyword + rule-based)
        │   └── dispatcher.py       # Intent → handler routing
        ├── handlers/
        │   └── diagnosis.py        # Symptom analysis handler
        ├── data_gen/
        │   └── generate.py         # Synthetic patient record generator (no API needed)
        ├── indexing/
        │   └── build_index.py      # FAISS vector index construction
        └── eval/                   # Evaluation harness (ROUGE + benchmarks)
```

---

## 🚀 Quickstart

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.11 recommended |
| RAM | ≥8 GB | For embedding model |
| Storage | ≥500 MB | Index + model cache |
| LLM Key | 1 required | Groq (free), OpenAI, or Ollama (local) |

### Step 1 — Environment Setup

```bash
cd medassist_platform

# Linux / macOS
python3 -m venv .venv && source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 2 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
# First run: ~3-5 min (PyTorch + transformers download)
```

### Step 3 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
# LLM Provider: groq | openai | ollama
MEDASSIST_LLM_PROVIDER=groq

# Groq — Free tier at https://console.groq.com
GROQ_API_KEY=gsk_your_key_here
MEDASSIST_GROQ_MODEL=openai/gpt-oss-20b

# Embedding & reranking
MEDASSIST_EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
MEDASSIST_RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
MEDASSIST_RERANK=1
```

### Step 4 — Generate Data & Build Index

```bash
# Generate 60 synthetic patient records
python -m src.data_gen.generate --count 60 --seed 42

# Build FAISS vector index (~90 MB model download on first run)
python -m src.indexing.build_index
```

### Step 5 — Launch

```bash
# Option A: Clinical Workstation (Recommended)
streamlit run app.py
# → http://localhost:8501

# Option B: Conversational Chatbot
streamlit run chatbot_app.py
# → http://localhost:8501

# Option C: FastAPI REST Server
uvicorn src.api.main:app --reload --port 8000
# → http://localhost:8000/docs
```

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `MEDASSIST_LLM_PROVIDER` | `groq` | `groq` / `openai` / `ollama` |
| `GROQ_API_KEY` | — | Required when provider = groq |
| `OPENAI_API_KEY` | — | Required when provider = openai |
| `MEDASSIST_GROQ_MODEL` | `openai/gpt-oss-20b` | Groq model name |
| `MEDASSIST_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `MEDASSIST_OLLAMA_MODEL` | `llama3.1` | Ollama local model |
| `MEDASSIST_EMBEDDING_MODEL` | `sentence-transformers/all-mpnet-base-v2` | Embedding model |
| `MEDASSIST_RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Reranker |
| `MEDASSIST_RERANK` | `1` | `1` = on, `0` = off (faster) |
| `MEDASSIST_TOP_K` | `5` | Similar cases returned |
| `MEDASSIST_DATA_DIR` | `data/raw` | Patient .txt files directory |
| `MEDASSIST_INDEX_DIR` | `data/faiss_index` | FAISS index directory |

### LLM Provider Comparison

| Provider | Speed | Cost | Privacy | Best For |
|---|---|---|---|---|
| **Groq** | ⚡ Fastest | 💚 Free tier | ☁️ Cloud | Development & demos |
| **OpenAI** | 🏃 Fast | 💛 Pay-per-use | ☁️ Cloud | Production quality |
| **Ollama** | 🐢 Slower | 💚 Free | 🔒 Fully local | Air-gapped / privacy |

---

## 🔌 REST API Reference

```bash
uvicorn src.api.main:app --reload --port 8000
# Swagger UI → http://localhost:8000/docs
```

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | System status: patients, index, LLM provider |
| `/patients` | `GET` | List all patient summaries (ID, name, age, diagnosis, risk) |
| `/chat` | `POST` | Submit clinical query → `{answer, citations, intent, elapsed_s}` |
| `/symptoms` | `POST` | Analyze symptoms → `{answer, similar, citations, elapsed_s}` |

---

## 🔒 Security & Compliance

> [!WARNING]
> This repository uses **synthetic patient records** for demonstration. Production deployment with real PHI requires the following controls.

| Control | Requirement |
|---|---|
| **De-identification** | HIPAA Safe Harbor / Expert Determination before FAISS indexing |
| **Access Control** | OpenID Connect + RBAC (DOCTOR / NURSE / ADMIN / VIEWER) |
| **Audit Logging** | Immutable timestamped logs for all retrievals, LLM calls, downloads |
| **Encryption** | TLS 1.3 in transit · AES-256 at rest for index + records |
| **Model Validation** | Clinical NLP benchmarks + continuous hallucination monitoring |

| Regulation | Status |
|---|---|
| HIPAA (US) | De-identification pipeline required for real PHI |
| GDPR (EU) | Patient record deletion API needed for production |
| FDA 510(k) | Required pathway for clinical device deployment |

---

## 🛠 Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **UI / Frontend** | Streamlit | 1.33+ |
| **Charts** | Plotly | 5.18+ |
| **REST API** | FastAPI + Uvicorn | 0.110+ |
| **LLM Orchestration** | LangChain + LangGraph | 0.3+ / 0.2+ |
| **LLM Providers** | Groq · OpenAI · Ollama | — |
| **Vector Search** | FAISS | 1.8+ |
| **Embeddings** | all-mpnet-base-v2 (768-dim) | — |
| **Reranker** | ms-marco-MiniLM-L-6-v2 | — |
| **ML Runtime** | PyTorch | 2.2+ |
| **Data** | Pandas · NumPy · scikit-learn | 2.0+ / 1.26+ / 1.3+ |
| **Evaluation** | ROUGE | 1.0+ |

---

## 📊 Synthetic Data Coverage

The built-in data generator covers **10 clinical conditions** without any API key:

| Condition | Risk Level | Key Biomarkers |
|---|---|---|
| Type 2 Diabetes Mellitus | Moderate | HbA1c 9.2%, Glucose 212 mg/dL |
| Hypertension (Stage 2) | Moderate–High | BP 168/104, ECG: LVH |
| Acute Myocardial Infarction | Critical | Troponin I 8.4 ng/mL, LVEF 40% |
| Community-Acquired Pneumonia | Moderate | WBC 14,200 (H), CRP 96 mg/L |
| Chronic Kidney Disease (3b) | High | eGFR 38, Creatinine 1.9 (H) |
| Asthma (Acute Exacerbation) | Moderate | Peak flow 55%, SpO2 93% |
| Ischemic Stroke | Critical | CT: MCA infarct, NIHSS 9 |
| Acute Appendicitis | High | WBC 13,800 (H), US: 9mm appendix |
| Congestive Heart Failure | Critical | BNP 1,240 pg/mL, LVEF 35% |
| COPD (Exacerbation) | High | SpO2 89%, ABG pCO2 52 mmHg |

---

## 📄 License

Released under the **MIT License**. See `LICENSE` for details.

---

<div align="center">

**MedAssist Platform · v2.0 · Build 2026-09-26**

Built with ❤️ using Streamlit · LangChain · LangGraph · FAISS · sentence-transformers · FastAPI

*Clinical decision-support demonstration system · Not a medical device · Not for clinical use without professional validation*

</div>
