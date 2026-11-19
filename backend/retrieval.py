import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
if __package__:
    from .config import get_embeddings, get_llm
else:
    from config import get_embeddings, get_llm


def source_name(document):
    filename = document.metadata.get("file_name")
    if not filename and document.metadata.get("source"):
        filename = Path(document.metadata["source"]).name
    return filename or "Unknown source"


def format_context(documents):
    """Give each retrieved chunk a citation number and source filename."""
    chunks = []
    for number, document in enumerate(documents, 1):
        chunks.append(f"[{number}] Source: {source_name(document)}\n{document.page_content}")
    return "\n\n".join(chunks)


def answer_question(question, index_path=None):
    """Answer from the index and return the retrieved chunks for citations."""
    llm = get_llm()
    embedding_model = get_embeddings()
    if index_path is None:
        index_path = Path(__file__).resolve().parent.parent / "faiss_index"
    vectorstore = FAISS.load_local(
        str(index_path),
        embeddings=embedding_model,
        allow_dangerous_deserialization=True,
    )
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3, "fetch_k": 10, "lambda_mult": 0.5},
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant.
Answer the user's question using only the provided context.
If the answer is not available in the context, say you don't know.
Do not invent information or source names.
Cite the numbered context chunks in square brackets for each fact you use, for example [1].

Context:
{context}"""),
        ("human", "{question}"),
    ])

    documents = retriever.invoke(question)
    messages = prompt.format_messages(context=format_context(documents), question=question)
    response = llm.invoke(messages)
    return response.content, documents


def main():
    response, documents = answer_question("What are the technical skills of the candidate?")
    print("\nLLM Response:\n")
    print(response)
    print("\nSources:\n")
    for number, document in enumerate(documents, 1):
        print(f"[{number}] {source_name(document)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        main()
    except Exception:
        logging.exception("Question answering failed")
        raise SystemExit(1)
