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
* 📑 Source citations (file name and page) for every answer
* 🌐 Web-based user interface built with Streamlit
* 🖨️ OCR support for scanned PDFs (Tesseract + Poppler)

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
├── .env.example
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
├── utils/
│   └── inspect_pdfs.py
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

### 1. Clone the repository

```bash
git clone https://github.com/ganeshkds84/MNITRAG_SYSTEM.git
cd MNITRAG_SYSTEM
```

> **Windows note:** clone into a short path such as `C:\PROJECTS\`. Installing `torch`
> (pulled in by `sentence-transformers`) fails inside deep folders because of Windows'
> 260-character path limit. Alternatively, [enable long paths in Windows](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation#enable-long-paths-in-windows-10-version-1607-and-later).

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux / macOS:

```bash
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract and Poppler (needed for OCR of scanned PDFs)

**Windows**

* Tesseract: install the 64-bit build from the [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki) (default path `C:\Program Files\Tesseract-OCR\tesseract.exe`).
* Poppler: download the latest release zip from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases) and extract it; the binaries are in its `Library\bin` folder.

**Linux / macOS**

```bash
sudo apt install tesseract-ocr poppler-utils   # Debian/Ubuntu
brew install tesseract poppler                 # macOS
```

### 5. Configure environment variables

Copy `.env.example` to `.env` and add your Groq API key:

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

```text
GROQ_API_KEY=your_groq_api_key
```

If Tesseract or Poppler are **not** on your PATH (common on Windows), also set:

```text
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\path\to\poppler\Library\bin
```

### 6. Build the vector store

Place the PDFs under `data/Raw/` (subfolders `faculty/`, `public/`, `student/`), then run:

```bash
python -m rag.ingest
```

Use `--data-dir` to ingest a different folder. Re-run this whenever the documents change.

---

## ▶️ Run the Application

```bash
streamlit run app.py
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

## ⚠️ Known Limitations

* **Fee tables in older scanned PDFs are not parsed into rows.** `Fee_Structure_2024-25_*.pdf`, `PG_2023-24.pdf`, `PhD_2023-24.pdf` and `UG_2023-24.pdf` are image-only scans. They are indexed through Tesseract OCR as plain text, so table columns (General vs SC/ST, odd vs even semester) are often lost or garbled, and answers about those years' fees may be incomplete.
* **Table rows exist only for the 2025-26 fee PDFs** (`FeePG2025-26.pdf`, `FeePhD2025-26.pdf`, `FeeUG2025-26.pdf`, set in `TABLE_ROW_FILES`). These are also scans, but the scanner embedded an OCR text layer; rows are rebuilt from its word positions (`rag/table_rows.py`). OCR spelling errors in row labels (e.g. "Reeistration") are kept as-is, and values in unusual cells (e.g. "US $ 8000 + ...") may be skipped. Check rows with `python -m rag.table_rows`.
* **Answer accuracy is measured with keyword/number matching** (`utils/eval_questions.py`), which cannot tell when a correct number is attached to the wrong category.

---

## 🔮 Future Enhancements

* Hybrid retrieval (semantic + keyword)
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
