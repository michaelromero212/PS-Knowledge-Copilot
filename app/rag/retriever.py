from typing import List, Dict, Any
from ..vectorstore.chroma_client import ChromaClient
from .embedder import Embedder


class Retriever:
    """Retrieves the top-k most relevant document chunks for a query."""

    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = ChromaClient()

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top-k relevant documents for a query."""
        query_embedding = self.embedder.generate_embeddings([query])[0]

        results = self.vector_store.search([query_embedding], k)

        # Format Chroma results to a standard list of dicts
        formatted_results = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "id": results['ids'][0][i]
                })
        return formatted_results
