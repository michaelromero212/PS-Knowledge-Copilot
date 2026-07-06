import sys
import os
import time
import random
import string

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ingest.document_loader import DocumentLoader
from app.rag.embedder import Embedder
from app.vectorstore.chroma_client import ChromaClient
from app.rag.retriever import Retriever
from app.rag.llm_connector import LLMConnector

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def stress_test():
    print("=== STARTING STRESS TEST ===")
    
    # Initialize components
    embedder = Embedder()
    chroma = ChromaClient(persistence_path="./data/stress_test_chroma_db")
    retriever = Retriever()
    retriever.vector_store = chroma
    llm = LLMConnector(provider="huggingface_local")

    # 1. Ingestion Stress
    print("\n[TEST 1] Ingestion Robustness")
    loader = DocumentLoader("./data/example_inputs")
    documents = loader.load_documents()
    
    # Simulate multiple rapid ingestions
    start_time = time.time()
    for i in range(5):
        print(f"  Ingestion run {i+1}...")
        texts = [doc['content'] for doc in documents]
        metadatas = [{"source": doc['source']} for doc in documents]
        ids = [doc['source'] for doc in documents] # Using filename as ID should prevent dupes if handled correctly
        embeddings = embedder.generate_embeddings(texts)
        chroma.upsert_documents(texts, metadatas, ids, embeddings)
    end_time = time.time()
    print(f"  5 Ingestion runs took {end_time - start_time:.2f}s")
    
    # Check for duplicates (Chroma should handle this via IDs)
    results = chroma.collection.get()
    print(f"  Total documents in DB: {len(results['ids'])} (Expected: {len(documents)})")
    if len(results['ids']) > len(documents):
        print("  FAIL: Duplicates detected!")
    else:
        print("  PASS: No duplicates.")

    # 2. Context Window / Long Query
    print("\n[TEST 2] Long Query / Context Overflow")
    long_query = "explain " + "very " * 100 + "long query"
    try:
        docs = retriever.retrieve(long_query, k=3)
        answer = llm.generate_answer(long_query, docs)
        print("  PASS: Handled long query without crash.")
    except Exception as e:
        print(f"  FAIL: Crashed on long query: {e}")

    # 3. Nonsense Query
    print("\n[TEST 3] Nonsense Query")
    nonsense_query = "asdfghjkl qwertyuiop zxcvbnm"
    docs = retriever.retrieve(nonsense_query, k=3)
    answer = llm.generate_answer(nonsense_query, docs)
    print(f"  Answer to nonsense: {answer[:100]}...")
    # We expect some answer, but hopefully not a crash. 
    # Ideally, it should say "insufficient context" but local models might hallucinate.
    
    # 4. Latency Check
    print("\n[TEST 4] Latency Check (Standard Query)")
    query = "What is the resolution target for a P1 incident?"
    start_time = time.time()
    docs = retriever.retrieve(query, k=3)
    answer = llm.generate_answer(query, docs)
    end_time = time.time()
    print(f"  Query took {end_time - start_time:.2f}s")
    if (end_time - start_time) > 10:
        print("  WARN: High latency (>10s)")
    else:
        print("  PASS: Acceptable latency.")

    print("\n=== STRESS TEST COMPLETE ===")

if __name__ == "__main__":
    stress_test()
