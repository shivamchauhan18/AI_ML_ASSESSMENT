import hashlib
import logging
import tempfile
from pathlib import Path

import streamlit as st

from backend.retrieval import answer_question, source_name
from backend.vectorstore import add_documents


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

st.set_page_config(layout="wide")
st.title("Ask your PDF")

left, right = st.columns(2)

with left, st.container(border=True):
    st.subheader("1. Upload a PDF")
    uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

    if uploaded_file is None:
        st.session_state.pop("upload_id", None)
        st.session_state.pop("directory", None)
    else:
        data = uploaded_file.getvalue()
        upload_id = (uploaded_file.name, hashlib.sha256(data).hexdigest())
        if st.session_state.get("upload_id") != upload_id:
            st.session_state.pop("upload_id", None)
            st.session_state.pop("directory", None)
            directory = None
            try:
                directory = tempfile.TemporaryDirectory()
                filename = Path(uploaded_file.name.replace("\\", "/")).name
                pdf_path = Path(directory.name) / filename
                with st.spinner("Processing PDF..."):
                    pdf_path.write_bytes(data)
                    chunks = add_documents([pdf_path], index_path=Path(directory.name) / "index")
                st.session_state["directory"] = directory
                st.session_state["upload_id"] = upload_id
                logger.info("PDF indexed: %s chunks", chunks)
            except Exception as error:
                if directory is not None:
                    directory.cleanup()
                logger.exception("PDF processing failed")
                st.error(f"Could not process the PDF: {error}")

        if st.session_state.get("upload_id") == upload_id:
            st.success(f"{uploaded_file.name} is ready.")

with right, st.container(border=True):
    st.subheader("2. Ask a question")
    if "directory" not in st.session_state:
        st.info("Upload a PDF to get started.")
    else:
        with st.form("question_form", clear_on_submit=True):
            question = st.text_input("Your question")
            submitted = st.form_submit_button("Ask")

        if submitted and question.strip():
            try:
                with st.spinner("Finding an answer..."):
                    index_path = Path(st.session_state["directory"].name) / "index"
                    answer, sources = answer_question(question.strip(), index_path)
                logger.info("Question answered: %s sources", len(sources))
                st.markdown(answer)
                with st.expander("Sources"):
                    for number, source in enumerate(sources, 1):
                        st.write(f"[{number}] {source_name(source)}")
            except Exception as error:
                logger.exception("Question answering failed")
                st.error(f"Could not answer the question: {error}")
