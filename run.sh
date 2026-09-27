#!/usr/bin/env bash
# One-shot setup for the MedAssist Clinical Intelligence Platform. Run from the project root.
set -e
python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; echo "Created .env — add your GROQ_API_KEY."; fi
python -m src.data_gen.generate --count 60 --seed 42
python -m src.indexing.build_index
echo "Done. Launch the platform with: streamlit run app.py"
echo "Classic chatbot: streamlit run chatbot_app.py"
