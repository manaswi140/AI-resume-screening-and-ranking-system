import pdfplumber  # type: ignore
import docx        # type: ignore
import re
import nltk        # type: ignore
from nltk.tokenize import word_tokenize  # type: ignore
from nltk.corpus import stopwords        # type: ignore


# Download NLTK resources (run once; will be cached)
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
# Some setups now also require punkt_tab for tokenization
try:
    nltk.download("punkt_tab", quiet=True)
except Exception:
    # Older NLTK versions may not have punkt_tab; ignore if missing
    pass


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file using pdfplumber.
    Returns a single string with line breaks between pages.
    """
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:  # Skip pages with no text
                text.append(page_text)
    return "\n".join(text).strip()


def extract_text_from_docx(docx_path: str) -> str:
    """
    Extract text from a DOCX file using python-docx.
    Returns a single string with line breaks between paragraphs.
    """
    document = docx.Document(docx_path)
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs).strip()


def preprocess_text(text):
    """
    Lowercase text, remove non-letters, tokenize,
    remove English stopwords, and join back to a string.
    Accepts either a string or list of strings.
    """
    if not text:
        return ""

    # If list, join into one string
    if isinstance(text, list):
        text = " ".join(text)

    # Normalize
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)

    # Tokenize and remove stopwords
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words("english"))
    tokens = [word for word in tokens if word and word not in stop_words]

    return " ".join(tokens)
