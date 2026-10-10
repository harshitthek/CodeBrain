import os
import re
import quopri
from bs4 import BeautifulSoup
from django.conf import settings
from apps.utils.logger_manager import get_logger

logger = get_logger(__name__)

# Try importing dependencies
try:
    from docx import Document
except ImportError:
    Document = None

try:
    import spacy
except ImportError:
    spacy = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    from unstructured.partition.auto import partition
    from unstructured.partition.html import partition_html
    from unstructured.partition.text import partition_text
    from unstructured.chunking.title import chunk_by_title
except ImportError:
    partition = None
    partition_html = None
    partition_text = None
    chunk_by_title = None

# ── 1. Force release global NLP limits ─────────────────────────────────────────
if spacy is not None:
    try:
        # Increase upper limit to 10 million characters for default Chinese and English models
        for lang_code in ["zh", "en"]:
            from spacy.util import get_lang_class
            lang_class = get_lang_class(lang_code)
            lang_class.max_length = 10000000
        logger.info("Successfully increased SpaCy global max_length limit to 10,000,000")
    except Exception as e:
        logger.warning(f"Failed to increase SpaCy limit: {e}")

# ── 2. Embedding Model Singleton ───────────────────────────────────────────
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("BAAI/bge-m3", trust_remote_code=True)
    return _embedding_model

# ── 3. Confluence Dedicated Cleaning Logic ────────────────────────────────────

def clean_confluence_content(raw_content):
    """
    Advanced cleaning strategy for Confluence MHTML:
    1. Extract first boundary block (HTML part)
    2. Decode Quoted-Printable
    3. Extract text using BeautifulSoup
    """
    initial_len = len(raw_content)
    try:
        # Step 1: Identify and extract HTML part (Multipart processing)
        # Find start of the first HTML block and end of the next boundary
        html_content = raw_content
        boundary_match = re.search(r'boundary="([^"]+)"', raw_content)
        if boundary_match:
            boundary = boundary_match.group(1)
            # Split blocks
            parts = raw_content.split(f"--{boundary}")
            for part in parts:
                if "Content-Type: text/html" in part:
                    # Found HTML block, strip MIME header
                    html_content = part.split("\r\n\r\n", 1)[-1]
                    break

        # Step 2: Quoted-Printable decoding
        decoded_bytes = quopri.decodestring(html_content.encode('utf-8'))
        decoded_content = decoded_bytes.decode('utf-8', errors='ignore')

        # Step 3: BeautifulSoup fine extraction
        soup = BeautifulSoup(decoded_content, 'html.parser')
        
        # Thoroughly remove unneeded nodes
        for tag in soup(["style", "script", "xml", "meta", "link", "v:imagedata", "o:SmartTagType"]):
            tag.decompose()
            
        # Remove image tags with heavy base64 attributes to prevent them from being parsed as text
        for img in soup.find_all('img'):
            img.decompose()

        # Step 4: Extract text and clean up
        clean_text = soup.get_text(separator="\n")
        
        # Filter non-printable characters, preserve newlines and tabs
        clean_text = "".join(ch for ch in clean_text if ch.isprintable() or ch in "\n\t")
        
        # Merge consecutive blank lines
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text).strip()
        
        final_len = len(clean_text)
        reduction = ((initial_len - final_len) / initial_len * 100) if initial_len > 0 else 0
        
        logger.info(f"[Deep Preprocess] Success. Original {initial_len} -> Current {final_len} (Reduction: {reduction:.2f}%)")
        return clean_text

    except Exception as e:
        logger.error(f"❌ Deep clean failed: {e}")
        # Fallback: if parsing fails, take first 10% of content (HTML is usually at the start)
        return raw_content[:int(initial_len * 0.1)]
# ── 4. Core Parsing Logic ───────────────────────────────────────────────────

def process_single_word(file_path):
    """
    Main entry point for Word file parsing
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    is_confluence = False
    
    # Check if Confluence format
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            head = f.read(4096)
            if "Exported From Confluence" in head or "MIME-Version" in head:
                is_confluence = True
    except Exception as e:
        logger.warning(f"Failed to read file header: {e}")

    if is_confluence:
        logger.info(f"🔍 [Type Detection] File confirmed as Confluence export format, starting deep cleaning.")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_data = f.read()
            
            # Get clean text
            pure_text = clean_confluence_content(raw_data)
            
            # Since it's already pure text, use partition_text directly for highest efficiency
            elements = partition_text(text=pure_text)
            return chunk_by_title(elements=elements, max_characters=3000, combine_text_under_n_chars=500)
        except Exception as e:
            logger.error(f"❌ Confluence handling failed: {e}", exc_info=True)

    # Standard file handling path
    if file_ext == ".docx" and Document is not None:
        try:
            elements = partition(filename=file_path, strategy="fast")
            return chunk_by_title(elements=elements, max_characters=4000)
        except Exception as e:
            logger.warning(f"Standard docx parsing failed: {e}")

    # Fallback for other .doc files
    elements = partition(filename=file_path, strategy="fast")
    return chunk_by_title(elements=elements, max_characters=4000)

def process_singel_file(file_path):
    """
    Main entry point function
    """
    file_type = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_type in [".doc", ".docx"]:
            chunks = process_single_word(file_path)
        elif file_type in [".xlsx", ".xls"]:
            from unstructured.partition.xlsx import partition_xlsx
            elements = partition_xlsx(filename=file_path)
            chunks = chunk_by_title(elements=elements, max_characters=4000)
        elif file_type == ".pdf":
            elements = partition(filename=file_path, strategy="fast")
            chunks = chunk_by_title(elements=elements, max_characters=4000)
        else:
            elements = partition(filename=file_path, strategy="fast")
            chunks = chunk_by_title(elements=elements, max_characters=4000)

        if chunks:
            logger.info(f"✅ Parsing completed: {os.path.basename(file_path)}, generated {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"❌ Critical error processing file {file_path}: {e}", exc_info=True)
        return None