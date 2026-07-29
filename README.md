# 🎓 MNITRAG_SYSTEM

An AI-powered Retrieval-Augmented Generation (RAG) system designed to make institutional academic information accessible through natural language conversations.

Instead of manually searching through regulations, fee structures, academic policies, faculty guidelines, and student handbooks, users can simply ask questions and receive accurate, context-aware answers grounded in official documents.

---

## 🚀 Problem Statement

Educational institutions maintain hundreds of pages of regulations, academic manuals, fee structures, internship guidelines, and policy documents.

Finding the right information is often:

* Time-consuming
* Confusing for students and faculty
* Dependent on manually browsing multiple PDFs
* Prone to misinterpretation

MNITRAG_SYSTEM addresses this challenge by transforming static academic documents into an intelligent conversational knowledge assistant.

---

## 💡 Solution

MNITRAG_SYSTEM leverages Retrieval-Augmented Generation (RAG) to:

1. Ingest institutional documents
2. Convert document content into vector embeddings
3. Store semantic representations for efficient retrieval
4. Retrieve the most relevant document chunks for a user query
5. Generate grounded responses using a Large Language Model (LLM)

This ensures answers are generated from actual institutional documents rather than relying solely on the model's pre-trained knowledge.

---

## ✨ Key Features

* 📚 Academic document intelligence
* 🔍 Semantic search over institutional PDFs
* 🤖 Conversational AI interface
* 📖 Context-aware question answering
* 🎯 Reduced hallucinations through document grounding
* 🧩 Modular RAG architecture
* 📂 Support for multiple document categories
* ⚡ Fast retrieval and response generation

---

## 🏗️ System Architecture

```text
User Query
     │
     ▼
Retriever
     │
     ▼
Relevant Document Chunks
     │
     ▼
Prompt Builder
     │
     ▼
Large Language Model
     │
     ▼
Grounded Response
```

---

## 📁 Project Structure

```text
MNITRAG_SYSTEM/
│
├── app.py
├── requirements.txt
│
├── config/
│   └── config.py
│
├── data/
│   └── Raw/
│       ├── faculty/
│       ├── public/
│       └── student/
│
└── rag/
    ├── loader.py
    ├── splitter.py
    ├── embedding.py
    ├── vectordb.py
    ├── retriever.py
    ├── prompt_builder.py
    ├── llm.py
    ├── pipeline.py
    ├── ingest.py
    └── schemas.py
```

---

## 🔄 Workflow

### Document Processing Pipeline

1. Load PDF documents
2. Extract textual content
3. Split content into manageable chunks
4. Generate embeddings
5. Store embeddings in vector storage

### Query Pipeline

1. User submits a question
2. Query embedding is generated
3. Similar document chunks are retrieved
4. Context is assembled
5. LLM generates a response based on retrieved information
6. Final answer is returned to the user

---

## 📚 Knowledge Base

The system currently supports institutional documents including:

* Undergraduate regulations
* Postgraduate regulations
* PhD regulations
* Fee structures
* Academic policies
* Internship guidelines
* Faculty guidelines
* Semester promotion policies
* CGPA regulations
* Administrative notifications

---

## 🛠️ Technology Stack

### Backend

* Python

### AI & RAG

* LangChain
* Large Language Models (LLMs)
* Embedding Models
* Retrieval-Augmented Generation (RAG)

### Data Processing

* PDF Processing
* Text Chunking
* Vector Embeddings
* Semantic Search

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/ganeshkds84/MNITRAG_SYSTEM.git
cd MNITRAG_SYSTEM
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment:

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
python app.py
```

---

## 💬 Example Questions

* What is the semester promotion policy?
* What are the CGPA requirements for graduation?
* What is the fee structure for PG students?
* What are the internship guidelines?
* What are the regulations for PhD admission?
* What is the maximum duration of a PG programme?

---

## 🎯 Impact

MNITRAG_SYSTEM improves information accessibility by enabling students, faculty, and administrators to interact with institutional knowledge using natural language instead of manually searching through large document repositories.

---

## 🔮 Future Enhancements

* Source citations in responses
* Hybrid retrieval (semantic + keyword)
* Web-based user interface
* Chat history and memory
* Multi-language support
* Role-based access control
* Document upload portal
* Evaluation and monitoring dashboard

---

## 👨‍💻 Author

**GANESH**

Passionate about AI, Machine Learning, Large Language Models, and building practical solutions that simplify access to information.

GitHub: https://github.com/ganeshkds84

---

## 📜 License

This project is intended for educational, research, and demonstration purposes.
