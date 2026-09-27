from pathlib import Path
from pypdf import PdfReader


DOCUMENTS_DIR = Path("documents")


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()

        if page_text:
            text += f"\n--- Page {page_number} ---\n"
            text += page_text

    return text


def main():
    pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in the documents folder.")
        return

    for pdf_file in pdf_files:
        print(f"\nReading: {pdf_file.name}")

        text = extract_text_from_pdf(pdf_file)

        print(f"Characters extracted: {len(text)}")
        print("\nFirst 1000 characters:")
        print(text[:1000])


if __name__ == "__main__":
    main()