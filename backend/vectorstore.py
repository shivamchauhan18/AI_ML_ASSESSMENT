"""Add documents to the persistent FAISS index used by retrieval.py."""

import argparse
import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

if __package__:
    from .config import get_embeddings
    from .document_processing import extract_pdf
else:
    from config import get_embeddings
    from document_processing import extract_pdf

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = PROJECT_DIR / "faiss_index"


def read_document(path):
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        return extract_pdf(str(path), output_path=None)
    if path.suffix.lower() in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported document type: {path.suffix}")


def add_documents(paths, index_path=DEFAULT_INDEX, embeddings=None):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n"],
    )
    texts = []
    metadata = []
    for path in paths:
        path = Path(path).expanduser().resolve()
        chunks = splitter.split_text(read_document(path))
        for chunk in chunks:
            texts.append(chunk)
            metadata.append({"source": str(path), "file_name": path.name})

    if not texts:
        raise ValueError("No text found in the supplied documents")

    index_path = Path(index_path).expanduser().resolve()
    index_file = index_path / "index.faiss"
    metadata_file = index_path / "index.pkl"
    if index_file.exists() != metadata_file.exists():
        raise FileNotFoundError(f"Incomplete FAISS index in {index_path}")

    if embeddings is None:
        embeddings = get_embeddings()
    if index_file.exists():
        # Only load index files from a trusted source: index.pkl uses pickle.
        store = FAISS.load_local(
            str(index_path), embeddings, allow_dangerous_deserialization=True
        )
        store.add_texts(texts, metadatas=metadata)
    else:
        store = FAISS.from_texts(texts, embeddings, metadatas=metadata)
    store.save_local(str(index_path))
    return len(texts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documents", nargs="+", help="PDF, Markdown, or text files to add")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="FAISS index directory")
    args = parser.parse_args()
    count = add_documents(args.documents, index_path=args.index)
    print(f"Saved {count} chunks to {args.index}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        main()
    except Exception:
        logging.exception("Document ingestion failed")
        raise SystemExit(1)
