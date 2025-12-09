from docling.document_converter import DocumentConverter
import os


def extract_text_from_pdf(file_path: str) -> str:
    converter = DocumentConverter()
    doc = converter.convert(file_path).document
    text = doc.export_to_markdown()
    return text