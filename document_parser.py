import fitz
from docx import Document


def extract_pdf(path):

    text = ""

    pdf = fitz.open(path)

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text


def extract_docx(path):

    doc = Document(path)

    text = []

    for paragraph in doc.paragraphs:
        text.append(paragraph.text)

    return "\n".join(text)


def extract_text(path):

    if path.lower().endswith(".pdf"):
        return extract_pdf(path)

    elif path.lower().endswith(".docx"):
        return extract_docx(path)

    return ""