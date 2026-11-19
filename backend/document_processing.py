import json
from pathlib import Path


def extract_pdf(pdf_path: str, output_path="extracted.md"):
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    document = result.document

    
    # Extract Markdown
    markdown = document.export_to_markdown()


    if output_path is not None:
        Path(output_path).write_text(markdown, encoding="utf-8")

    return markdown


if __name__ == "__main__":
    pdf_path = "/home/shivam/Desktop/Shivam_Chauhan.pdf"
    data = extract_pdf(pdf_path)
    print(data)
