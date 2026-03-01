import pdfplumber
import io

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text from a loaded PDF bytes object."""
    text_content = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        return "\n\n".join(text_content)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""