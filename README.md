# Arabic PDF to Structured

A Streamlit web app that converts PDF documents — especially Arabic and RTL content — into AI-ready structured formats using [opendataloader-pdf](https://pypi.org/project/opendataloader-pdf/).

PDF extractors often output Arabic text in visual (reversed) order. This app fixes that automatically, producing correctly ordered logical text suitable for LLMs, RAG pipelines, and downstream NLP tasks.
<p align="center">
<img width="559" height="300" alt="Screenshot 2026-04-14 at 11 51 35 AM" src="https://github.com/user-attachments/assets/025ced1c-8549-4d0b-ae43-ea9477bc4115" />
</p>
## Features

- **Fast mode** — local CPU processing for digital PDFs
- **Hybrid mode** — AI-enhanced conversion with OCR support (powered by Docling), ideal for scanned documents
- **Arabic/RTL handling** — automatic visual-to-logical order correction with proper bidirectional text rendering
- **Multiple output formats** — Markdown, JSON, HTML, plain text, and annotated PDF
- **In-browser preview** — rendered RTL output with Arabic font support directly in the app

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

```bash
git clone https://github.com/moabdelmoez/arabic-pdf-to-structured.git
cd arabic-pdf-to-structured
uv sync
```

## Usage

```bash
uv run streamlit run app.py
```

This opens the app in your browser. From there:

1. Upload a PDF file
2. Choose an output format (markdown, json, html, text, or annotated pdf)
3. Select a processing mode:
   - **Fast** — for digital PDFs, runs locally on CPU
   - **Hybrid** — for scanned or complex PDFs, uses AI-enhanced OCR (requires the hybrid backend — see below)
4. Toggle **RTL display** for Arabic content (enabled by default)
5. Click **Convert** and preview or download the result

### Hybrid Mode Setup

Hybrid mode requires a running backend server. Start it in a **separate terminal** before converting:

```bash
uv run opendataloader-pdf-hybrid --port 5002
```

Wait for `Application startup complete` to appear (first run may take a while to download models), then use Hybrid mode in the app.

### Headless Mode

To run without auto-opening a browser (e.g., on a server):

```bash
uv run streamlit run app.py --server.headless true
```

## Output Formats

| Format         | Description                                      |
|----------------|--------------------------------------------------|
| Markdown       | Structured text with headings, lists, and tables |
| JSON           | Machine-readable structured output               |
| HTML           | Rendered document with formatting preserved      |
| Text           | Plain text extraction                            |
| Annotated PDF  | Original PDF with extraction annotations overlay |

## Contributing with Claude Code

This project includes a [`CLAUDE.md`](CLAUDE.md) file that provides architecture details, key constraints, and development commands for [Claude Code](https://claude.ai/code). Clone the repo, open it with Claude Code, and you'll be productive immediately.
