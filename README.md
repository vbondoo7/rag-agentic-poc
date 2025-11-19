# 🧠 Agentic Architect AI — RAG + Gemini

An intelligent, multi-agent architecture assistant that can:
- Analyze microservices codebases.
- Identify architecture patterns, flows, and dependencies.
- Evaluate impact of changes.
- Generate blueprints and technical documentation automatically.

---

## 🚀 Features

✅ Multi-agent orchestration (Understanding, Impact, Blueprint, Doc Generation)  
✅ RAG-based retrieval using ChromaDB  
✅ Persistent chat history (SQLite)  
✅ Markdown-based doc generation  
✅ Modular architecture for extension  

---

## 🧩 Folder Structure

rag-agentic-poc/
│
├── ai_agents/
│ ├── architect_agent.py
│ ├── understanding_agent.py
│ ├── blueprint_agent.py
│ ├── impact_agent.py
│ ├── doc_generator_agent.py
│ ├── requirements_agent.py
│ ├── sdk_tools.py
│ └── db.py
│
├── sample_codebase/
│ ├── microservices/
│ │ ├── order-service/
│ │ ├── user-service/
│ │ ├── payment-service/
│ │ └── ...
│
├── chroma_db/
├── generated_docs/
├── main.py
├── requirements.txt
└── README.md

yaml
Copy code

---

## ⚙️ Installation & Setup

### 1️⃣ Clone and Setup
```bash
git clone <your_repo_url>
cd rag-agentic-poc
python -m venv .venv
source .venv/bin/activate   # on Mac/Linux
# or .venv\Scripts\activate  # on Windows