import os
import tempfile
import faiss
import pickle
import numpy as np
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic

from shared.llm import ANTHROPIC_MODEL

# Global FAISS index + mapping for retrieval
faiss_index = None
documents = []
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
llm = ChatAnthropic(model=ANTHROPIC_MODEL)  # temperature no longer accepted by the API (Nov 2026)

#------------------------------------
# Process PDF: parse, chunk, embed, store in FAISS
#------------------------------------
def process_pdf(file):
    global faiss_index, documents
    # Reset for new session
    faiss_index, documents = None, []

    # Save file temporarily (needed for PyPDF2)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        file.save(tmp_file.name)
        tmp_path = tmp_file.name

    # Extract text
    reader = PdfReader(tmp_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    if not text.strip():
        raise ValueError("No text extracted from PDF")

    # Chunk text
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)

    # Embed chunks
    embeddings = embedding_model.embed_documents(chunks)

    # Build FAISS index
    dimension = len(embeddings[0])
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(np.array(embeddings).astype("float32"))
    documents = chunks  # keep mapping

    print(f"[INFO] Processed {len(chunks)} chunks from PDF")

    return True

#------------------------------------
# Answer question: search FAISS, retrieve, call LLM
#------------------------------------
def answer_question(question):
    global faiss_index, documents

    if faiss_index is None or not documents:
        return "No document has been uploaded and processed yet."

    # Embed query
    query_vector = embedding_model.embed_query(question)
    query_vector = np.array([query_vector]).astype("float32")

    # Search top-k
    D, I = faiss_index.search(query_vector, k=3)
    retrieved_chunks = [documents[i] for i in I[0] if i < len(documents)]

    # Build prompt
    context = "\n\n".join(retrieved_chunks)
    prompt = f"""
    You are a helpful assistant. Use the following document context to answer the question.
    Context:
    {context}

    Question: {question}
    Answer:
    """

    response = llm.invoke(prompt)
    return response.content