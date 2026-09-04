import sys
import asyncio
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from rag.retriever import rag_retriever
from pdf.generator import pdf_generator
import json

def test():
    context = rag_retriever.retrieve_context_for_jd("Looking for a Python and Next.js engineer with experience in ChromaDB and RAG")
    print(f"Retrieved {context['match_count']} matches successfully!")
    print(f"Extracted keywords: {context['extracted_keywords']}")

    with open(backend_dir / "sample_data" / "sample_profile.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    path = asyncio.run(pdf_generator.generate_pdf(data, "modern"))
    print(f"Generated PDF at: {path}")
    assert Path(path).exists(), "PDF file should exist"
    print("PDF generation verified!")

if __name__ == "__main__":
    test()
