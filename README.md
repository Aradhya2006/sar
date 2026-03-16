# SAR-Automator: Privacy-First Suspicious Activity Reporting

### 🚀 Overview
Automating the generation of **Suspicious Activity Reports (SAR)** using Local LLMs to ensure financial data privacy and regulatory compliance. 

### 🛡️ Key Features
- **Local AI Logic:** Uses **Ollama (Llama 3.2)** to generate narratives offline—no data leaves the local environment.
- **PII Masking:** Integrated **Microsoft Presidio** to anonymize sensitive entities (names, account numbers) before processing.
- **Audit Ready:** Transactions and generated reports are logged in **MongoDB** for a full audit trail.
- **Interactive UI:** Built with **Streamlit** for seamless human-in-the-loop review.

### 🛠️ Tech Stack
- **LLM:** Llama 3.2 (via Ollama)
- **Framework:** LangChain, Python
- **Privacy:** Microsoft Presidio
- **Database:** MongoDB
- **Frontend:** Streamlit

### ⚙️ Setup
1. **Install Ollama** and pull the model:
   `ollama pull llama3.2`
2. **Install Dependencies:**
   `pip install -r requirements.txt`
3. **Run the App:**
   `streamlit run src/main.py`