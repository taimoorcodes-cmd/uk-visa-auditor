# UK Visa Auditor

AI-assisted document checker for UK Student Visa applicants in Pakistan.

## ⚠️ Disclaimer

This is an informational and document-checking tool. It does NOT provide 
immigration advice. It does NOT guarantee visa approval. Always verify 
requirements on the official UK government website (gov.uk).

## Status

V1 in progress — Week 1

## Features (V1)

- Upload passport, CAS, and bank statement
- AI extracts data from PDFs
- Rules engine checks against UK Home Office rules
- Readiness score (0-100)
- Friendly AI narration
- Official gov.uk links

## Tech Stack

- Streamlit (UI)
- LangGraph (AI workflow)
- OpenRouter (LLM)
- pdfplumber + mrz (PDF parsing)
- Python + JSON (rules engine)

## Author

Taimoor Ghalib
https://github.com/taimoorcodes-cmd