from pathlib import Path
from pypdf import PdfReader


DOCUMENTS_DIR = Path("documents")


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        if text:
            pages.append({
                "page": page_number,
                "text": text
            })

    return pages


def create_chunks(text, chunk_size=500, overlap=100):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def main():

    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDF found.")
        return

    pdf_file = pdf_files[0]

    print(f"Reading: {pdf_file.name}")

    pages = extract_text_from_pdf(pdf_file)

    all_text = "\n".join(page["text"] for page in pages)

    chunks = create_chunks(all_text)

    print(f"\nTotal characters: {len(all_text)}")
    print(f"Total chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks, start=1):

        print("\n" + "=" * 60)
        print(f"CHUNK {i}")
        print("=" * 60)

        print(chunk)


if __name__ == "__main__":
    main()