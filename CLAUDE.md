# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Streamlit web app that converts PDF documents (especially Arabic/RTL) to AI-ready formats using `opendataloader-pdf`. Single-file app in `app.py`.

## Commands

```bash
# Install dependencies
uv sync

# Run the app
uv run streamlit run app.py

# Run the app headless (no browser auto-open)
uv run streamlit run app.py --server.headless true
```

**Always use `uv` (not pip) for package management and running Python.**

## Architecture

The app is a single Streamlit file (`app.py`) with three concerns:

1. **Arabic visual-order fix** (`fix_arabic_visual_order`) — PDF extractors often output Arabic text in visual order (reversed). This function reverses each line back to logical order while preserving LTR sequences (numbers, Latin text). Applied when RTL mode is enabled.

2. **RTL HTML rendering** (`RTL_HTML_TEMPLATE`) — Arabic content is rendered via `st.components.v1.html()` in a full HTML document with `dir="rtl"`, `unicode-bidi: embed`, and Arabic fonts. Do not use `st.markdown()` for Arabic text — it breaks ligatures and bidi.

3. **Conversion pipeline** — Uploads are saved to a temp directory, passed to `opendataloader_pdf.convert()`, and output files are read back for preview/download. Supports two modes:
   - **Fast**: local CPU, digital PDFs
   - **Hybrid**: AI-enhanced with OCR (pass `hybrid="docling-fast"` and `ocr_lang`)

## Key Constraints

- Arabic RTL content must go through `st.components.v1.html()`, never `st.markdown()` with `unsafe_allow_html`
- The `fix_arabic_visual_order` function must re-reverse embedded numbers and Latin text after reversing the full line
- Output formats: markdown, json, html, text, annotated pdf
