# Ask your PDF
Upload a PDF and ask questions about its contents.

## Setup

You need Python 3.10 or newer, Ollama and an OpenAI API key.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull embeddinggemma-2:440m
```

Start Ollama if it is not already running (`ollama serve`). Add your api key to a
`.env` file in the project root:

```text
OPENAI_API_KEY=your_api_key
```

The `.env` file is ignored by Git. The embedding and language models can be
changed in `backend/config.py`.

## Streamlit app

```bash
streamlit run app.py
```


## API

```bash
uvicorn api:app
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

```bash
# Check the API
curl http://127.0.0.1:8000/health

# Add a PDF to the vector store
curl -X POST http://127.0.0.1:8000/upload -F "file=@/path/to/document.pdf"

# Ask a question
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

The API keeps a shared index in `faiss_index`. Uploads append to it, including
duplicate uploads. Run one API worker and avoid modifying the index from another
process while the API is running. 

