# 🇬🇧 UK Visa Auditor AI Agent

An AI-powered document checker for Pakistani students applying for UK Student Visas. Built to reduce refusal rates by pre-auditing documents before submission.

## 🚀 Live Demo
 **Live Demo:** *(Coming soon)*

## ✨ Features
- **3D Glassmorphism UI:** Cinematic dark theme with rotating 3D elements.
- **AI Chat Assistant:** Answers questions about document requirements using official gov.uk links.
- **Smart Document Parsing:** Extracts data from Passport (MRZ), CAS, and Bank Statements (PDF).
- **28-Day Funds Engine:** Calculates exact GBP/PKR requirements and verifies the 28-day consecutive balance rule.
- **OCR Support:** Reads both digital PDFs and scanned images (JPG/PNG).
- **Privacy First:** Uploaded files are deleted immediately after processing.
- **Freemium Model:** Includes SQLite database for user history, limits, and Easypaisa payment tracking.

## 🛠️ Tech Stack
- **Frontend:** Streamlit + Custom HTML/CSS (3D UI)
- **AI Orchestration:** LangGraph
- **LLM Provider:** OpenRouter (Currently configured for free models)
- **PDF Parsing:** pdfplumber, mrz, pytesseract
- **Database:** SQLite
- **Backend:** Python, JSON rules engine, RapidFuzz

## 🚀 How to Run Locally
1. Clone the repo: `git clone https://github.com/taimoorcodes-cmd/uk-visa-auditor.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file and add your OpenRouter API key:
