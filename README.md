# Gen AI Data Quality Helper (CSV)

**Frontend URL** = https://gen-ai-data-quality-helper.netlify.app 
**Backend API URL (FastAPI on Hugging Face Spaces)** = https://charulathag21-gen-ai-data-quality-helper.hf.space  


## 1. Overview & Problem Statement

Messy CSV files slow down analysts, data scientists, and ML pipelines.  
Common problems include:

- Missing values
- Outliers and impossible values
- Invalid email / date / phone formats
- Duplicate rows
- Inconsistent categories (e.g., `Male`, `M`, `male`)

This project is a **GenAI-powered Data Quality Helper** that lets a user upload a CSV (20–200 rows) and automatically:

- Analyses basic data quality issues
- Uses **rule-based checks** for fast, deterministic validation
- Uses an **LLM (via Groq + LangChain)** to suggest fixes with confidence levels
- Shows a clean UI with tables and charts
- Lets the user download a **cleaned CSV** and a **JSON report**

---

## 2. Tech Stack (as required by the challenge)

- **Frontend:** React.js (Create React App)
- **Backend:** FastAPI
- **Authentication:** JWT-based Signup + Login (username + password, hashed with bcrypt)
- **GenAI / LLM:**
  - Groq API (`llama-3.1-8b-instant`)
  - LangChain `ChatGroq` + `ChatPromptTemplate`
- **Deployment:**
  - Backend: Hugging Face Spaces (FastAPI)
  - Frontend: Deployed on Netlify

No paid or credit-card-based LLMs are used.  
The LLM is accessed through a **free Groq API key** stored as an environment variable.

---

## 3. Architecture & Workflow

### 3.1 High-level architecture

1. **React Frontend**
   - Login / Signup screen
   - Home / description page
   - CSV upload & analysis page
   - Data quality report tables + charts

2. **FastAPI Backend**
   - `/auth/register` – user signup
   - `/auth/login` – returns JWT access token
   - `/quality/report` – accepts CSV, returns data quality report JSON
   - `/quality/download/{filename}` – download cleaned CSV

3. **GenAI Layer (LangChain + Groq)**
   - Backend builds a list of issues (invalid email/date/phone)
   - Sends them to a LangChain chain with a strict JSON-only prompt
   - LLM responds with suggestions + confidence + reason
   - Backend merges rule-based results with LLM suggestions

4. **Storage**
   - Users stored in a simple `data/users.json` file
   - Cleaned CSV files stored temporarily in `output/` directory

### 3.2 Data Flow

1. User signs up → `/auth/register`
2. User logs in → `/auth/login` returns JWT
3. Frontend stores JWT in `localStorage` and uses it in `Authorization: Bearer <token>`
4. User uploads CSV → `/quality/report`
5. Backend:
   - Reads CSV with pandas
   - Computes:
     - Missing values per column
     - Outliers (IQR rule)
     - Duplicate rows (ignoring ID-like columns)
     - Invalid emails, dates (Indian format aware), phones
     - Summary statistics for numeric columns
   - Builds `issues_for_llm` array for invalid formats:
     - `[{id, issue_type, column, row_index, value}, ...]`
   - Sends issues to LangChain + Groq LLM
   - Receives JSON corrections:
     - suggestion, confidence, reason
   - Drops duplicates, forward/backward fills missing values
   - Saves cleaned CSV and returns:
     - `missing_values`
     - `outliers_detected`
     - `duplicate_rows` and `duplicate_rows_detail`
     - `invalid_format` (raw)
     - `ai_corrections` (LLM suggestions)
     - `summary_statistics`
     - `cleaned_file_download` URL

6. Frontend renders:
   - Tables for each issue type
   - LLM suggestion tables:
     - original value
     - suggested correction
     - confidence
     - reason
   - Charts for missing values and outliers
   - Download buttons for cleaned CSV and JSON report

---

## 4. Setup & Installation

### 4.1 Backend (FastAPI)

```bash
git clone https://github.com/charulathag21/gen-ai-data-quality-helper.git
cd gen-ai-data-quality-helper/backend

python -m venv venv
venv\Scripts\activate   # on Windows
# source venv/bin/activate   # on Mac/Linux

pip install -r requirements.txt

# Set your Groq API key (Windows PowerShell example)
setx GROQ_API_KEY "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"

### Running on Hugging Face Spaces (Docker)
This Space uses a Dockerfile to run FastAPI:

- Installs dependencies from requirements.txt
- Exposes port 7860
- Runs `uvicorn main:app`

Hugging Face automatically builds and starts the app after every push.

# Run backend
uvicorn main:app --reload
