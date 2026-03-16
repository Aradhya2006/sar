# SAR Automator — Privacy-First Suspicious Activity Reporting

### 🚀 Overview
Automates generation of **Suspicious Activity Reports (SAR)** using a local LLM
to ensure financial data privacy and full regulatory compliance.
No customer data ever leaves the machine.

---

### 🗂️ Project Structure

```
sar_automator/
├── main.py          — Streamlit UI (run this)
├── anonymizer.py    — PII masking via Microsoft Presidio
├── generator.py     — SAR narrative generation via Ollama (Llama 3.2)
├── database.py      — MongoDB storage and retrieval
├── monitor.py       — Batch CSV fraud scanner
├── risk.py          — Rule-based risk scoring engine (NEW)
├── requirements.txt — Python dependencies
└── README.md
```

---

### 🛡️ Key Features

| Feature | Description |
|---|---|
| **Local AI** | Ollama (Llama 3.2) runs fully offline — nothing leaves your machine |
| **PII Masking** | Microsoft Presidio masks names, emails, phones, credit cards before AI sees them |
| **Risk Scoring** | Rule-based engine assigns Low / Medium / High risk with explanations |
| **Batch Scanning** | Upload a CSV to auto-detect structuring fraud across all customers |
| **Audit Log** | MongoDB stores every report with full metadata for compliance review |
| **Case Management** | Update investigation status per case (Flagged / Under Review / Filed / Closed) |
| **Export** | Download audit log as CSV |

---

### 🛠️ Tech Stack

- **LLM:** Llama 3.2 (via Ollama — runs locally)
- **Framework:** LangChain, Python 3.11+
- **Privacy / PII:** Microsoft Presidio + spaCy `en_core_web_lg`
- **Database:** MongoDB (local instance)
- **Frontend:** Streamlit
- **Risk Engine:** Custom rule-based scorer (`risk.py`)

---

### ⚙️ Setup (Step by Step)

#### 1. Install Ollama and pull the model
```bash
# Install from https://ollama.com
ollama pull llama3.2
ollama serve          # Keep this running in a separate terminal
```

#### 2. Install MongoDB
```bash
# macOS
brew tap mongodb/brew && brew install mongodb-community
brew services start mongodb-community

# Ubuntu
sudo apt install mongodb
sudo systemctl start mongodb
```

#### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

#### 4. Download the spaCy language model (REQUIRED for Presidio)
```bash
python -m spacy download en_core_web_lg
```

#### 5. Run the app
```bash
streamlit run main.py
```

---

### 📋 CSV Format for Batch Scanning

Your CSV must have these columns:

| Column | Type | Required | Description |
|---|---|---|---|
| `customer_name` | string | ✅ Yes | Customer full name |
| `amount` | float | ✅ Yes | Transaction amount in USD |
| `date` | string | No | Transaction date |
| `branch` | string | No | Branch or location |
| `type` | string | No | e.g. `deposit`, `wire` |

Example:
```csv
customer_name,amount,date,type,branch
Aradhya Ranjan,4900,2024-01-15,deposit,Main St Branch
Aradhya Ranjan,4900,2024-01-15,deposit,Oak Ave Branch
Aradhya Ranjan,4900,2024-01-15,deposit,Park Rd Branch
Jane Smith,500,2024-01-15,deposit,Main St Branch
```

---

### 🔍 How the Pipeline Works

```
Raw text input
     │
     ▼
[Presidio Anonymizer]  ── masks PERSON, EMAIL, PHONE, LOCATION, CREDIT_CARD
     │
     ▼
[Risk Scorer]          ── rule-based: amount bands + pattern matching → Low/Medium/High
     │
     ▼
[Ollama Llama 3.2]     ── generates formal SAR narrative from masked text only
     │
     ▼
[MongoDB]              ── stores raw input, masked text, narrative, risk score, status
```

---

### ⚠️ Known Limitations

- Presidio NER accuracy depends on `en_core_web_lg` — uncommon names may be missed
- LLM output quality depends on Ollama being available; a fallback template is used if it's offline
- MongoDB must be running locally; reports are given stub IDs if unavailable
- Batch scan uses a simple aggregation rule — real AML systems use additional behavioral models

---

### 📜 Regulatory Reference

- **BSA (Bank Secrecy Act):** Requires SARs for transactions ≥ $5,000 with suspicion, or ≥ $10,000 with no explanation
- **FinCEN SAR filing deadline:** 30 days from detection (60 days if no suspect identified)
- **Record retention:** 5 years minimum

---

### 🔒 Privacy Notice
All AI processing is local. Presidio masks PII before Llama ever sees it.
No data is sent to any external API. This system is designed for on-premises deployment.
