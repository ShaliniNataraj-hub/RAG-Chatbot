# Local RAG Chatbot with Qwen3-4B

A local Retrieval-Augmented Generation (RAG) chatbot built with **Python, Flask, ChromaDB, Sentence Transformers, llama.cpp, and Qwen3-4B**.

The system allows users to ask questions about uploaded PDF documents. Relevant information is retrieved from the document using semantic search and provided to the local Qwen3-4B language model to generate an answer.

The entire application runs locally without OpenAI API, Ollama, or any cloud LLM API.

---

## Features

- PDF-based question answering
- Semantic search using vector embeddings
- Local Qwen3-4B language model
- Q4_K_M quantized GGUF model
- Persistent ChromaDB vector database
- Automatic Qwen model download from Hugging Face
- CPU-only inference support
- Flask-based web interface
- Source page information in responses
- No external LLM API required
- RAG + general knowledge fallback
- NDJSON-compatible streaming API

---

## Architecture

```text
                    PDF Files
                       |
                       v
                Text Extraction
                       |
                       v
                   Chunking
                       |
                       v
             Sentence Transformers
                all-MiniLM-L6-v2
                       |
                       v
                   ChromaDB
                       |
                  User Question
                       |
                       v
              Question Embedding
                       |
                       v
              Similarity Search
                       |
                Relevant Chunks
                       |
                       v
                  Qwen3-4B
                 Q4_K_M GGUF
                       |
                       v
                Generated Answer
                       |
                       v
                   Flask UI
```

---

## Technologies

| Component | Technology |
|---|---|
| Language | Python |
| Web Framework | Flask |
| Embedding Model | `all-MiniLM-L6-v2` |
| Vector Database | ChromaDB |
| LLM | Qwen3-4B |
| Quantization | Q4_K_M GGUF |
| LLM Runtime | llama.cpp |
| Model Source | Hugging Face |
| PDF Processing | pypdf |
| Frontend | HTML, CSS, JavaScript |
| API Format | NDJSON |
| Inference | CPU |

---

## Project Structure

```text
RAG-Chatbot/
│
├── app.py
├── chatbot.py
├── vector_db.py
│
├── documents/
│   └── your-document.pdf
│
├── chroma_db/
│   └── ChromaDB files
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
├── README.md
└── requirements.txt
```

---

## Requirements

### Hardware

Recommended:

```text
RAM:       16 GB or more
CPU:       Modern multi-core CPU
Storage:   At least 5 GB free
GPU:       Not required
```

The Qwen3-4B Q4_K_M model is approximately 2.5 GB.

### Software

Install:

- Python 3.10+
- Git
- llama.cpp
- VS Code (recommended)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ShaliniNataraj-hub/RAG-Chatbot.git
cd RAG-Chatbot
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\activate
```

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

If `requirements.txt` is not available:

```powershell
pip install flask chromadb sentence-transformers pypdf requests huggingface-hub
```

---

## Install llama.cpp

On Windows:

```powershell
winget install llama.cpp
```

Verify:

```powershell
llama-cli --version
```

If Windows cannot find `llama-cli`, restart VS Code or open a new PowerShell terminal.

---

## Qwen3-4B Model

This project uses:

```text
Qwen3-4B-Q4_K_M.gguf
```

from the Hugging Face repository:

```text
Qwen/Qwen3-4B-GGUF
```

The application downloads the model automatically through `llama-cli`.

You do not need to manually place the model inside the project directory.

The model is cached locally after the first download.

---

## Add a PDF

Place your PDF inside:

```text
documents/
```

Example:

```text
documents/
└── ai and ml.pdf
```

---

## Create the Vector Database

Run:

```powershell
python vector_db.py
```

The ingestion pipeline is:

```text
PDF
 ↓
Text Extraction
 ↓
Cleaning
 ↓
Chunking
 ↓
Embedding Generation
 ↓
ChromaDB
```

The vector database is stored in:

```text
chroma_db/
```

---

## Run the Chatbot

You only need one terminal.

Activate the environment:

```powershell
.\venv\Scripts\activate
```

Then:

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

### Important

You do **not** need to run:

```powershell
llama-server
```

You do **not** need Ollama.

You do **not** need an OpenAI API key.

`chatbot.py` launches `llama-cli` directly when a question is processed.

---

## How the RAG Pipeline Works

```text
User Question
      |
      v
Question Embedding
      |
      v
ChromaDB Similarity Search
      |
      v
Top Relevant Document Chunks
      |
      v
Prompt Construction
      |
      v
Qwen3-4B Q4_K_M
      |
      v
Answer
```

The chatbot retrieves relevant information from the PDF instead of passing the complete document to the language model.

---

## RAG + General Knowledge

The chatbot supports both document-based and general questions.

### Document-related question

Example:

```text
What is machine learning according to the document?
```

The system retrieves relevant document chunks and uses them to generate the answer.

### General question

If the document does not contain the required information, Qwen3 can answer using its general language-model knowledge.

---

## CPU-Only Inference

The project uses:

```text
-ngl 0
```

This prevents GPU layer offloading.

The inference path is:

```text
Qwen3-4B
    |
Q4_K_M GGUF
    |
llama.cpp
    |
CPU
```

A dedicated GPU is not required.

---

## Why Q4_K_M?

Q4_K_M provides a practical balance between:

- Model size
- RAM usage
- CPU performance
- Answer quality

The Q4_K_M model is approximately 2.5 GB.

---

## Flask API

The application exposes:

```text
POST /ask
```

Example request:

```json
{
    "question": "What is machine learning?"
}
```

The endpoint returns newline-delimited JSON (NDJSON).

Example:

```json
{"type":"token","content":"Machine learning"}
{"type":"sources","sources":[1,2]}
{"type":"done"}
```

---

## Source Tracking

The chatbot tracks the document pages used during retrieval.

Example:

```text
Answer:
Machine learning is a method where systems learn
patterns from data.

Sources:
Page 4
Page 5
```

---

## Configuration

The main configuration is in:

```text
chatbot.py
```

### Embedding model

```python
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)
```

### ChromaDB

```python
chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)
```

### Qwen model

```python
MODEL_REPO = "Qwen/Qwen3-4B-GGUF:Q4_K_M"
```

### CPU inference

```text
-ngl 0
```

---

## First Run

The first Qwen run requires an internet connection because the model needs to be downloaded from Hugging Face.

The model is approximately:

```text
2.5 GB
```

After downloading, it is stored in the local cache and reused.

---

## Privacy

The RAG pipeline and LLM inference are designed to run locally.

PDF documents are processed locally.

Qwen3 runs locally through llama.cpp.

No external LLM API is required.

Internet access is required for the initial model download.

---

## Troubleshooting

### `llama-cli is not recognized`

Restart VS Code after installing llama.cpp.

Then run:

```powershell
llama-cli --version
```

### ChromaDB collection not found

Run:

```powershell
python vector_db.py
```

before starting the application.

### PDF not found

Make sure the PDF is inside:

```text
documents/
```

### Model takes time to generate

Qwen3-4B is running on CPU. CPU inference is slower than GPU inference, especially for longer responses.

Reducing the generation token limit can improve response time.

---

## Future Improvements

- Better document chunking
- Hybrid keyword + semantic search
- Reranking
- Conversation memory
- Multiple PDF support
- DOCX support
- Web page ingestion
- Citation highlighting
- Retrieval confidence threshold
- Faster CPU inference
- GPU acceleration
- Docker deployment
- RAG evaluation
- Query rewriting
- Agent-based retrieval

---

## Learning Objectives

This project demonstrates practical implementation of:

- Retrieval-Augmented Generation (RAG)
- Natural Language Processing
- Semantic embeddings
- Vector databases
- Document chunking
- Similarity search
- Local LLM inference
- GGUF quantization
- llama.cpp
- Hugging Face models
- Flask APIs
- PDF processing
- Local AI applications

---

---

## Author

**Shalini N**

Computer Science and Engineering (Cyber Security)
