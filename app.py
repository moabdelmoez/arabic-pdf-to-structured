import streamlit as st
import opendataloader_pdf
import tempfile
import os
import json
import base64
import re
import unicodedata

st.set_page_config(page_title="PDF to AI-Ready Data", layout="wide")


def _is_arabic_char(ch):
    """Check if a character is Arabic script."""
    try:
        return "ARABIC" in unicodedata.name(ch, "")
    except ValueError:
        return False


def _has_arabic(text):
    """Check if text contains any Arabic characters."""
    return any(_is_arabic_char(ch) for ch in text)


def _reverse_arabic_segment(segment):
    """Reverse a text segment while preserving LTR runs (numbers, Latin)."""
    reversed_seg = segment[::-1]
    # Re-reverse number sequences so they read LTR
    reversed_seg = re.sub(
        r'[0-9][0-9.,:\-/٫٬]*[0-9]|[0-9]',
        lambda m: m.group(0)[::-1],
        reversed_seg,
    )
    # Re-reverse Latin words so they read LTR
    reversed_seg = re.sub(
        r'[A-Za-z]+(?:\s+[A-Za-z]+)*',
        lambda m: m.group(0)[::-1],
        reversed_seg,
    )
    return reversed_seg


def fix_arabic_visual_order(text):
    """Convert Arabic text from visual order (reversed) to logical order.

    Many PDF extractors output Arabic in visual order — characters appear
    left-to-right as on screen, but Unicode/HTML RTL rendering expects
    logical order. This reverses each line so the browser can display
    it correctly with dir=rtl.

    For markdown table rows, each cell is reversed individually to
    preserve the table structure.
    """
    lines = text.split("\n")
    fixed_lines = []
    for line in lines:
        if not _has_arabic(line):
            fixed_lines.append(line)
            continue

        stripped = line.strip()
        # Handle markdown table rows: reverse each cell individually
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = line.split("|")
            # cells[0] is empty (before first |), cells[-1] is empty (after last |)
            fixed_cells = []
            for cell in cells:
                if cell.strip() and _has_arabic(cell):
                    fixed_cells.append(_reverse_arabic_segment(cell))
                else:
                    fixed_cells.append(cell)
            fixed_lines.append("|".join(fixed_cells))
        else:
            fixed_lines.append(_reverse_arabic_segment(line))
    return "\n".join(fixed_lines)

RTL_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
  body {{
    direction: rtl;
    text-align: right;
    unicode-bidi: embed;
    font-family: 'Noto Naskh Arabic', 'Amiri', 'Traditional Arabic', 'Arial', serif;
    font-size: 16px;
    line-height: 2.0;
    padding: 16px;
    margin: 0;
    color: #333;
  }}
  pre {{
    direction: rtl;
    text-align: right;
    unicode-bidi: embed;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: 'Noto Naskh Arabic', 'Amiri', monospace;
    font-size: 15px;
    line-height: 2.0;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    direction: rtl;
  }}
  th, td {{
    border: 1px solid #ccc;
    padding: 8px 12px;
    text-align: right;
  }}
</style>
</head>
<body>
{content}
</body>
</html>
"""

st.title("PDF to AI-Ready Data")
st.caption("Convert PDF documents (including Arabic) to structured, AI-ready formats")

# --- Sidebar controls ---
with st.sidebar:
    st.header("Settings")

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

    output_format = st.selectbox(
        "Output Format",
        ["markdown", "json", "html", "text", "pdf"],
        format_func=lambda x: {
            "markdown": "Markdown",
            "json": "JSON",
            "html": "HTML",
            "text": "Plain Text",
            "pdf": "Annotated PDF",
        }[x],
    )

    mode = st.radio("Processing Mode", ["Fast", "Hybrid"], index=0)

    if mode == "Hybrid":
        st.info("Hybrid mode uses AI for OCR, formulas, and chart descriptions.")

    rtl_mode = st.checkbox("RTL Display (Arabic/Hebrew)", value=True)

    convert_btn = st.button("Convert", type="primary", disabled=uploaded_file is None)

# --- Conversion logic ---
if convert_btn and uploaded_file is not None:
    with st.spinner("Converting PDF..."):
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Save uploaded file
                # Use ASCII-safe filename — Java CLI can't handle non-ASCII paths
                safe_name = "input.pdf"
                input_path = os.path.join(tmp_dir, safe_name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                output_dir = os.path.join(tmp_dir, "output")
                os.makedirs(output_dir)

                # Build convert kwargs
                convert_kwargs = {
                    "input_path": [input_path],
                    "output_dir": output_dir,
                    "format": output_format,
                }

                if mode == "Hybrid":
                    convert_kwargs["hybrid"] = "docling-fast"

                # Run conversion
                opendataloader_pdf.convert(**convert_kwargs)

                # Find output files
                output_files = []
                for root, _, files in os.walk(output_dir):
                    for fname in files:
                        output_files.append(os.path.join(root, fname))

                if not output_files:
                    st.error("No output files were generated. The PDF may be empty or unsupported.")
                else:
                    # Map output format to expected file extensions
                    format_extensions = {
                        "markdown": {".md"},
                        "json": {".json"},
                        "html": {".html", ".htm"},
                        "text": {".txt"},
                        "pdf": {".pdf"},
                    }
                    expected_exts = format_extensions.get(output_format, set())

                    # Filter to only files matching the requested format
                    matched_files = [
                        f for f in output_files
                        if os.path.splitext(f)[1].lower() in expected_exts
                    ]

                    if not matched_files:
                        st.error("No output files matched the requested format.")
                    for out_file in matched_files:
                        st.success(f"Converted: {os.path.basename(out_file)}")

                        # Only fix visual order for Fast mode — Hybrid already outputs logical order
                        needs_visual_fix = rtl_mode and mode == "Fast"

                        if output_format == "markdown":
                            content = open(out_file, "r", encoding="utf-8").read()
                            if needs_visual_fix:
                                content = fix_arabic_visual_order(content)
                            if rtl_mode:
                                import markdown as _md
                                html_body = _md.markdown(content, extensions=["tables", "fenced_code"])
                                rtl_html = RTL_HTML_TEMPLATE.format(content=html_body)
                                st.components.v1.html(rtl_html, height=600, scrolling=True)
                            else:
                                st.markdown(content)
                            st.download_button("Download Markdown", content, file_name="output.md", mime="text/markdown")

                        elif output_format == "json":
                            content = open(out_file, "r", encoding="utf-8").read()
                            if needs_visual_fix:
                                content = fix_arabic_visual_order(content)
                            try:
                                parsed = json.loads(content)
                                st.json(parsed)
                            except json.JSONDecodeError:
                                st.code(content, language="json")
                            st.download_button("Download JSON", content, file_name="output.json", mime="application/json")

                        elif output_format == "html":
                            content = open(out_file, "r", encoding="utf-8").read()
                            st.components.v1.html(content, height=600, scrolling=True)
                            st.download_button("Download HTML", content, file_name="output.html", mime="text/html")

                        elif output_format == "text":
                            content = open(out_file, "r", encoding="utf-8").read()
                            if needs_visual_fix:
                                content = fix_arabic_visual_order(content)
                            if rtl_mode:
                                import html as _html
                                escaped = _html.escape(content)
                                rtl_html = RTL_HTML_TEMPLATE.format(content=f"<pre>{escaped}</pre>")
                                st.components.v1.html(rtl_html, height=600, scrolling=True)
                            else:
                                st.text(content)
                            st.download_button("Download Text", content, file_name="output.txt", mime="text/plain")

                        elif output_format == "pdf":
                            pdf_bytes = open(out_file, "rb").read()
                            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                            pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                            st.download_button("Download Annotated PDF", pdf_bytes, file_name="output_annotated.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"Conversion failed: {e}")
