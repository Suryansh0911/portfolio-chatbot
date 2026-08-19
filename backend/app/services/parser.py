from pathlib import Path
from pypdf import PdfReader
from docx import Document

def clean_text(text: str)->str:
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if line:
            lines.append(line)
    return "\n".join(lines)

def parse_pdf(file_path: str)->str:
    reader = PdfReader(file_path)

    text = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text.append(page_text)
    return "\n".join(text)

def parse_docx(file_path: str)->str:
    document = Document(file_path)

    text = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            text.append(paragraph.text)
    return "\n".join(text)

def parse_resume(file_path: str)->str:

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path.suffix.lower()

    if extension == ".pdf":
        return parse_pdf(file_path)
    elif extension == ".docx":
        return parse_docx(file_path)
    else:
        raise ValueError("Unsupported file type. Use PDF or DOCX")