import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ingest.document_loader import DocumentLoader
from app.ingest.cleaner import Cleaner
from app.rag.embedder import Embedder
from app.vectorstore.chroma_client import ChromaClient
from app.rag.retriever import Retriever

def test_ingestion_and_retrieval():
    print("Testing Ingestion...")
    loader = DocumentLoader("./data/example_inputs")
    documents = loader.load_documents()
    assert len(documents) > 0, "No documents loaded"
    print(f"Loaded {len(documents)} documents.")

    print("Testing Cleaning...")
    cleaned_text = Cleaner.clean_text("  This   is  a   test.  ")
    assert cleaned_text == "This is a test.", "Cleaning failed"
    print("Cleaning passed.")

    print("Testing Embedding...")
    embedder = Embedder()
    embeddings = embedder.generate_embeddings(["Test sentence"])
    assert len(embeddings) == 1, "Embedding generation failed"
    assert len(embeddings[0]) > 0, "Empty embedding"
    print("Embedding passed.")

    print("Testing Vector Store (Chroma)...")
    chroma = ChromaClient(persistence_path="./data/test_chroma_db")
    texts = [doc['content'] for doc in documents]
    metadatas = [doc.get('metadata', {"source": doc['source']}) for doc in documents]
    
    # Generate unique IDs for chunked documents
    ids = []
    for doc in documents:
        metadata = doc.get('metadata', {})
        chunk_idx = metadata.get('chunk_index', 0)
        source = doc['source']
        ids.append(f"{source}_chunk_{chunk_idx}")
    
    embeddings = embedder.generate_embeddings(texts)
    
    chroma.upsert_documents(texts, metadatas, ids, embeddings)
    print("Upsert passed.")

    print("Testing Retrieval...")
    retriever = Retriever()
    # Mock the vector store in retriever to use our test db
    retriever.vector_store = chroma 
    
    results = retriever.retrieve("best time to overseed a lawn", k=1)
    assert len(results) > 0, "No results retrieved"
    print(f"Retrieved: {results[0]['metadata']['source']}")
    print("Retrieval passed.")

    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    test_ingestion_and_retrieval()
