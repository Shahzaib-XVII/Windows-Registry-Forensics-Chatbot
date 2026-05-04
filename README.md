# Windows Registry Forensics AI Chatbot

> AI-powered forensic analysis tool for Windows Registry hives and Event Logs  
> CY-2002/3006 Digital Forensics — Semester Project — April 2026

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Dependencies and Prerequisites](#dependencies-and-prerequisites)
- [Installation Instructions](#installation-instructions)
- [Execution Steps](#execution-steps)
- [Platform Compatibility](#platform-compatibility)
- [Troubleshooting](#troubleshooting)

---

## Overview

The **Windows Registry Forensics AI Chatbot** is a Python-based digital forensics tool that parses Windows Registry hive files (`.hiv`) and Windows Event Logs (`.evtx`), indexes the extracted data using semantic embeddings, and enables natural language querying through an AI-powered chatbot interface.

The tool implements a **Retrieval-Augmented Generation (RAG)** architecture — combining ChromaDB vector storage with the Groq AI API — allowing forensic investigators to ask questions in plain English and receive evidence-grounded answers drawn directly from parsed registry and event log data.

### What This Tool Does

- Parses Windows Registry hives: `SOFTWARE.hiv`, `SYSTEM.hiv`, `NTUSER.hiv`
- Parses Windows Event Logs: `System.evtx`, `Application.evtx`
- Embeds extracted forensic data into a semantic vector database (ChromaDB)
- Enables natural language Q&A on registry data via Groq AI (RAG pipeline)
- Provides a graphical user interface (PyQt5) for ease of use
- Generates structured forensic PDF reports from investigation sessions

### Architecture

| Component | Technology | Role |
|-----------|-----------|------|
| Parser | `python-registry`, `python-evtx` | Extracts raw data from forensic artifacts |
| Embedder | `sentence-transformers` | Converts text to semantic vectors |
| Vector Store | `ChromaDB` | Stores and retrieves relevant evidence chunks |
| AI Engine | Groq API (`llama3-8b-8192`) | Generates answers from retrieved context |
| UI | `PyQt5` | Graphical interface for investigators |
| Reporter | `reportlab` | Generates professional PDF forensic reports |
| Cache DB | SQLite (`forensics.db`) | Caches parsed registry data for fast reload |

---

## Project Structure

```
Windows_Registry_Forensics_Chatbot_111/
├── main.py                  # Application entry point (launches PyQt5 UI)
├── run_load.py              # CLI script: load & index evidence files
├── run_qa.py                # CLI script: batch Q&A against indexed evidence
├── requirements.txt         # Python package dependencies
├── .env                     # API key configuration (DO NOT COMMIT)
├── forensics.db             # SQLite database (parsed registry data cache)
│
├── parser/                  # Evidence parsing modules
│   ├── registry_parser.py   # Parses .hiv registry hive files
│   └── evtx_parser.py       # Parses .evtx Windows Event Logs
│
├── indexer/                 # Embedding and vector DB modules
│   ├── embedder.py          # Sentence-transformer embedding pipeline
│   └── db.py                # ChromaDB interface
│
├── engine/                  # QA / RAG engine
│   ├── qa_engine.py         # Core retrieval + Groq AI query engine
│   └── test1.py             # Engine unit tests
│
├── reporter/                # Report generation
│   └── pdf_report.py        # PDF forensic report generator (reportlab)
│
├── ui/                      # GUI components
│   └── main_window.py       # PyQt5 main application window
│
├── chroma_store/            # Persistent vector database storage
│   └── chroma.sqlite3       # ChromaDB persistent store
│
└── tests/                   # Sample forensic evidence files
    ├── SOFTWARE.hiv         # Sample SOFTWARE registry hive (103 MB)
    ├── SYSTEM.hiv           # Sample SYSTEM registry hive (19 MB)
    ├── NTUSER.hiv           # Sample NTUSER registry hive (12 MB)
    ├── System.evtx          # Sample System event log (10 MB)
    └── Application.evtx     # Sample Application event log (8 MB)
```

---

## Dependencies and Prerequisites

### System Prerequisites

| Prerequisite | Version | Where to Get |
|---|---|---|
| Python | 3.10 or higher | https://python.org/downloads |
| pip | 23.0+ | Included with Python 3.10+ |
| Visual C++ Redistributable | 2015–2022 | Microsoft official download page |
| Groq API Key | Free account required | https://console.groq.com |

### Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `python-registry` | ≥ 1.3.1 | Parse Windows Registry `.hiv` hive files |
| `python-evtx` | ≥ 0.7.4 | Parse Windows Event Log `.evtx` files |
| `chromadb` | ≥ 0.4.0 | Vector database for semantic search storage |
| `sentence-transformers` | ≥ 2.2.0 | Generate semantic embeddings from text |
| `groq` | ≥ 0.5.0 | Groq AI API client for the QA engine |
| `PyQt5` | ≥ 5.15.0 | Graphical user interface framework |
| `reportlab` | ≥ 4.0.0 | PDF generation for forensic reports |
| `python-dotenv` | ≥ 1.0.0 | Load `.env` configuration files |
| `tqdm` | ≥ 4.65.0 | Progress bar display during indexing |

---

## Installation Instructions

### Step 1 — Verify Python

Open **Command Prompt** and run:

```bash
python --version
# Expected: Python 3.10.x or higher

pip --version
# Expected: pip 23.x or higher
```

### Step 2 — Navigate to the Project Folder

```bash
D:
cd Downloads\Windows_Registry_Forensics_Chatbot_111
```

### Step 3 — Activate the Virtual Environment

```bash
venv\Scripts\activate
```

Your prompt will change to show `(venv)` — this confirms the environment is active.

> **If activation fails:** The venv may be missing or corrupt. Recreate it:
> ```bash
> rmdir /s /q venv
> python -m venv venv
> venv\Scripts\activate
> ```

### Step 4 — Install Dependencies

```bash
pip install python-registry python-evtx chromadb sentence-transformers groq PyQt5 reportlab python-dotenv tqdm
```

> **Note:** `sentence-transformers` downloads an AI model (~90 MB) on first install. This requires an internet connection and takes 5–10 minutes.

### Step 5 — Configure the API Key

Open the `.env` file in Notepad:

```bash
notepad .env
```

Add your Groq API key on the first line:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

Get a free API key from **console.groq.com → API Keys**.

> **Security:** Never commit your `.env` file to version control. Never share your API key publicly.

---

## Execution Steps

### Option A — Graphical Interface (Recommended)

**1. Load and index the evidence files first:**

```bash
python run_load.py all
```

This parses all `.hiv` and `.evtx` files in the `tests/` folder and builds the ChromaDB vector index. Expect 5–15 minutes for the full evidence set.

**2. Launch the GUI:**

```bash
python main.py
```

A PyQt5 window will open. Type forensic questions in the chat box:

```
What software is installed on this system?
Were any USB devices connected to this system?
What user accounts exist on this system?
Show me recently accessed files.
Are there any suspicious services or autostart entries?
```

**3. Generate a PDF report:**

Click **Generate Report** inside the GUI to export all findings as a PDF.

---

### Option B — Command Line QA

Run predefined forensic questions in batch mode:

```bash
python run_qa.py
```

---

### Quick Launch Sequence (Every Time)

```bash
D:
cd Downloads\Windows_Registry_Forensics_Chatbot_111
venv\Scripts\activate
python main.py
```

---

## Platform Compatibility

| Platform | Support | Notes |
|----------|---------|-------|
| Windows 10 64-bit | ✅ Full | Primary development environment |
| Windows 11 64-bit | ✅ Full | Fully tested and verified |
| Windows 10 32-bit | ❌ Not supported | Some dependencies require 64-bit |
| Ubuntu Linux 20.04+ | ⚠️ Partial | Hive parsing works; Qt may need extra deps |
| macOS 12+ | ⚠️ Untested | Python libraries cross-platform; UI not verified |

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'PyQt5'` | PyQt5 not installed | `pip install PyQt5` |
| `ModuleNotFoundError: No module named 'groq'` | Groq client not installed | `pip install groq` |
| `IndexError: list index out of range` in run_load.py | Missing argument | Run `python run_load.py all` |
| `ModuleNotFoundError: No module named 'Registry'` | python-registry not installed | `pip install python-registry` |
| `venv\Scripts\activate` not recognized | venv missing | Run `python -m venv venv` first |
| `FileNotFoundError` on `.hiv` file | Wrong path in run_load.py | Open run_load.py in Notepad, update paths to `tests\` folder |
| ChromaDB `collection not found` | Evidence not indexed yet | Run `python run_load.py all` first |
| Slow indexing (> 20 min) | Large hive files + CPU only | Normal for 100+ MB hives; let it complete |
| GUI window opens but is blank | PyQt5 render issue | Resize the window to force a repaint |
| API authentication error | Wrong or missing API key | Check `.env` has correct `GROQ_API_KEY=gsk_...` |

### Verify All Packages Are Installed

```bash
python -c "import Registry; import evtx; import chromadb; import groq; from PyQt5.QtWidgets import QApplication; print('All OK')"
```

Expected output: `All OK`

### Reset the ChromaDB Index

If the vector index is corrupt or you want to re-index from scratch:

```bash
rmdir /s /q chroma_store
python run_load.py all
```

---

