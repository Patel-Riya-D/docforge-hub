"""
Document Ingestion Module (Notion → RAG Pipeline)

This module is responsible for extracting and preprocessing documents
from Notion to prepare them for embedding and indexing.

Responsibilities:
- Fetch pages and blocks from Notion database
- Extract structured metadata (title, section, doc_type, industry)
- Split large text into smaller chunks
- Convert raw content into structured chunk format

Output:
- List of chunks with metadata:
    {
        "doc_title": str,
        "section": str,
        "text": str,
        "doc_type": str,
        "industry": str,
        "page_id": str
    }

Used by:
- build_index.py for embedding and vector storage
"""
from backend.rag.notion_reader import fetch_all_pages, fetch_page_blocks


def split_text(text, max_chars=500):
    """
    Split large text into smaller chunks for embedding.

    This function ensures that text is divided into manageable sizes
    while preserving word boundaries.

    Args:
        text (str): Input text to be split
        max_chars (int): Maximum characters per chunk

    Returns:
        list[str]: List of text chunks

    Notes:
    - Prevents overly long inputs for embedding models
    - Splitting is done based on words, not characters
    - Ensures semantic coherence within chunks
    """

    chunks = []

    if len(text) <= max_chars:
        return [text]

    words = text.split()
    current = ""

    for w in words:

        if len(current) + len(w) + 1 > max_chars:
            chunks.append(current.strip())
            current = w
        else:
            current += " " + w

    if current:
        chunks.append(current.strip())

    return chunks


def ingest_documents():
    """
    Ingest documents from Notion and convert them into structured text chunks.

    This function:
    1. Fetches all pages from the Notion database.
    2. Extracts metadata such as:
        - document title
        - document type
        - industry
        - last updated timestamp
    3. Retrieves page content blocks (headings, paragraphs, bullet points).
    4. Splits long text into smaller chunks for embedding.
    5. Assigns section names based on headings.
    6. Returns a list of structured chunks for vector indexing.

    Returns:
        list[dict]: List of document chunks with metadata:
            [
                {
                    "doc_title": str,
                    "section": str,
                    "text": str,
                    "doc_type": str,
                    "industry": str,
                    "page_id": str,
                    "last_updated": str
                }
            ]

    Notes:
        - Supports incremental indexing using `last_updated` field
        - Ensures chunks are optimized for embedding size limits
        - Maintains metadata for filtering and citation generation
    """

    pages = fetch_all_pages()

    all_chunks = []

    for page in pages:

        page_id = page["id"]

        title_list = page["properties"].get("Name", {}).get("title", [])
        title = title_list[0]["plain_text"] if title_list else "Untitled"

        doc_type_field = page["properties"].get("Document Type", {}).get("select")
        doc_type = doc_type_field["name"] if doc_type_field else "Unknown"

        industry_field = page["properties"].get("Industry", {}).get("select")
        industry = industry_field["name"] if industry_field else "Unknown"

        blocks = fetch_page_blocks(page_id)

        current_section = None

        for block in blocks:

            block_type = block["type"]

            # Detect section
            if block_type == "heading_2":

                current_section = block["heading_2"]["rich_text"][0]["plain_text"]

            # Paragraph
            elif block_type == "paragraph":

                rich = block["paragraph"]["rich_text"]

                if not rich:
                    continue

                text = rich[0]["plain_text"]

                text_chunks = split_text(text)

                for chunk_text in text_chunks:

                    chunk = {
                        "doc_title": title,
                        "section": current_section,
                        "text": chunk_text,
                        "doc_type": doc_type,
                        "industry": industry,
                        "page_id": page_id,
                        "last_updated": page.get("last_edited_time") or "1970-01-01T00:00:00"
                    }

                    all_chunks.append(chunk)

            # Bullet list
            elif block_type == "bulleted_list_item":

                rich = block["bulleted_list_item"]["rich_text"]

                if not rich:
                    continue

                text = rich[0]["plain_text"]

                text_chunks = split_text(text)

                for chunk_text in text_chunks:

                    chunk = {
                        "doc_title": title,
                        "section": current_section,
                        "text": chunk_text,
                        "doc_type": doc_type,
                        "industry": industry,
                        "page_id": page_id,
                        "last_updated": page.get("last_edited_time") or "1970-01-01T00:00:00"
                    }

                    all_chunks.append(chunk)

    return all_chunks