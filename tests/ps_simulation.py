import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ingest.document_loader import DocumentLoader
from app.rag.embedder import Embedder
from app.vectorstore.chroma_client import ChromaClient
from app.rag.retriever import Retriever
from app.rag.llm_connector import LLMConnector

def simulate_ps_workflow():
    print("\n=======================================================")
    print("🤖 PS KNOWLEDGE COPILOT - SIMULATION RUN")
    print("=======================================================\n")
    
    # Initialize
    print("Initializing system components...")
    embedder = Embedder()
    chroma = ChromaClient(persistence_path="./data/simulation_chroma_db")
    retriever = Retriever()
    retriever.vector_store = chroma
    llm = LLMConnector(provider="huggingface_local")

    # 1. Ingest Knowledge Base
    print("\n[STEP 1] Ingesting Knowledge Base...")
    loader = DocumentLoader("./data/example_inputs")
    documents = loader.load_documents()
    
    if documents:
        texts = [doc['content'] for doc in documents]
        metadatas = [{"source": doc['source']} for doc in documents]
        ids = [doc['source'] for doc in documents]
        embeddings = embedder.generate_embeddings(texts)
        chroma.upsert_documents(texts, metadatas, ids, embeddings)
        print(f"✅ Ingested {len(documents)} documents successfully.")
    else:
        print("❌ No documents found to ingest!")
        return

    # 2. Simulate PS Questions
    ps_questions = [
        {
            "role": "Service Desk Analyst",
            "query": "What is the resolution target for a P1 incident?",
            "intent": "Incident Management"
        },
        {
            "role": "Change Manager",
            "query": "Who approves an emergency change?",
            "intent": "Change Management"
        },
        {
            "role": "Security Engineer",
            "query": "What does the principle of least privilege mean?",
            "intent": "Access Management"
        },
        {
            "role": "Service Delivery Manager",
            "query": "What is an error budget?",
            "intent": "SLA Management"
        }
    ]

    print("\n[STEP 2] Simulating Consultant Queries...\n")

    for i, item in enumerate(ps_questions):
        print(f"--- Interaction {i+1} ---")
        print(f"👤 User Role: {item['role']}")
        print(f"❓ Question: {item['query']}")
        print(f"🎯 Intent: {item['intent']}")
        
        start_time = time.time()
        print("   Thinking...", end="", flush=True)
        
        # Retrieve
        docs = retriever.retrieve(item['query'], k=3)
        
        # Generate
        answer = llm.generate_answer(item['query'], docs)
        
        end_time = time.time()
        print(f" (took {end_time - start_time:.2f}s)")
        
        print(f"\n🤖 Copilot Answer:\n{answer.strip()}")
        print("\n📚 Sources:")
        for doc in docs:
            print(f"   - {doc['metadata']['source']}")
        print("\n" + "-"*60 + "\n")

    print("=======================================================")
    print("✅ SIMULATION COMPLETE")
    print("=======================================================")

if __name__ == "__main__":
    simulate_ps_workflow()
