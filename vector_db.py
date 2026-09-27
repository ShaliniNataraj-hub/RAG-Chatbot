from pathlib import Path
import re
import shutil

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


# ============================================================
# Configuration
# ============================================================

DOCUMENTS_DIR = Path("documents")
CHROMA_DIR = Path("chroma_db")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


# ============================================================
# Load embedding model
# ============================================================

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================================================
# Clean extracted PDF text
# ============================================================

def clean_text(text):

    # Remove common HTML-style space artifacts
    text = text.replace("&#x20;", " ")

    # Remove excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Reduce excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Remove spaces before punctuation
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    return text.strip()


# ============================================================
# Extract PDF page-by-page
# ============================================================

def extract_pages(pdf_path):

    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text()

        if not text:
            continue

        text = clean_text(text)

        if text:
            pages.append({
                "page": page_number,
                "text": text
            })

    return pages


# ============================================================
# Create meaningful chunks
# ============================================================

def create_chunks(pages):

    chunks = []

    for page_data in pages:

        page_number = page_data["page"]
        text = page_data["text"]

        # Split primarily using blank lines
        paragraphs = re.split(r"\n\s*\n", text)

        current_chunk = ""

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            # If adding this paragraph stays within our target size
            if len(current_chunk) + len(paragraph) + 2 <= CHUNK_SIZE:

                if current_chunk:
                    current_chunk += "\n\n"

                current_chunk += paragraph

            else:

                # Save existing chunk
                if current_chunk:

                    chunks.append({
                        "text": current_chunk,
                        "page": page_number
                    })

                # Start new chunk
                current_chunk = paragraph

        # Save remaining text
        if current_chunk:

            chunks.append({
                "text": current_chunk,
                "page": page_number
            })

    return chunks


# ============================================================
# Main ingestion process
# ============================================================

def main():

    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))

    if not pdf_files:

        print("No PDF files found in documents/")

        return


    # --------------------------------------------------------
    # Recreate ChromaDB
    # --------------------------------------------------------

    if CHROMA_DIR.exists():

        print("\nRemoving old ChromaDB...")

        shutil.rmtree(CHROMA_DIR)


    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )


    collection = client.get_or_create_collection(
        name="documents"
    )


    # --------------------------------------------------------
    # Process PDFs
    # --------------------------------------------------------

    total_chunks = 0

    for pdf_path in pdf_files:

        print("\n" + "=" * 70)
        print(f"Processing: {pdf_path.name}")
        print("=" * 70)


        # Extract pages
        pages = extract_pages(pdf_path)

        print(f"Pages extracted: {len(pages)}")


        # Create chunks
        chunks = create_chunks(pages)

        print(f"Chunks created: {len(chunks)}")


        if not chunks:
            continue


        # ----------------------------------------------------
        # Prepare data
        # ----------------------------------------------------

        documents = []
        metadatas = []
        ids = []


        for index, chunk in enumerate(chunks):

            documents.append(chunk["text"])

            metadatas.append({
                "source": pdf_path.name,
                "page": chunk["page"],
                "chunk": index + 1
            })

            ids.append(
                f"{pdf_path.stem}_chunk_{index + 1}"
            )


        # ----------------------------------------------------
        # Create embeddings
        # ----------------------------------------------------

        print("Creating embeddings...")

        embeddings = model.encode(
            documents,
            show_progress_bar=True
        )


        # ----------------------------------------------------
        # Store in ChromaDB
        # ----------------------------------------------------

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )


        total_chunks += len(chunks)


    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)

    print(f"Total chunks stored: {total_chunks}")


if __name__ == "__main__":
    main()