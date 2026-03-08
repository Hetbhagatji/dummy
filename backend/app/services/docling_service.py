from docling.document_converter import DocumentConverter
import os

converter = DocumentConverter()
def extract_text_from_pdf(file_path: str) -> str:
    doc = converter.convert(file_path).document
    text = doc.export_to_markdown()
    return text