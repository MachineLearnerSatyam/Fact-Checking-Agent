# 🛡️ Fact-Checking-Agent

An intelligent, automated "Truth Layer" designed to analyze marketing documents, extract critical statistical claims, and cross-reference them against live web data to detect hallucinations, outdated metrics, and fabricated statistics.

This project was built as an assessment submission for the Product Management Trainee role, demonstrating a robust pipeline for handling "Trap Documents."

## ✨ Core Features
* **Automated Document Parsing:** Extracts raw text from uploaded PDF files using `pdfplumber`.
* **Structured Claim Extraction:** Utilizes Groq (Llama-3.3-70b) to intelligently scan text and output a strict JSON array of only verifiable, hard statistical claims (ignoring fluff).
* **Live Agentic Web Search:** Integrates the Tavily API to execute deep background searches for each extracted claim, fetching real-time, accurate web context and source URLs.
* **Intelligent Evaluation Loop:** A secondary LLM pass acts as a judge, comparing the original claim against live data to categorize it as `Verified`, `Inaccurate`, or `False`, while providing the actual corrected fact.
* **Professional UI Dashboard:** Built with Streamlit, featuring real-time progress tracking, metric summaries, and an executive report layout.

## 🛠️ Tech Stack
* **Frontend & Framework:** Streamlit
* **LLM Engine:** Groq API (Model: `llama-3.3-70b-versatile`)
* **Search Retrieval:** Tavily API
* **PDF Processing:** `pdfplumber`
* **Data Validation:** Pydantic

## 🚀 How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone <your-github-repo-url>
   cd <your-repo-directory>