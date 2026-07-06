/**
 * RAG API Service
 * 
 * Handles all API calls to the FastAPI backend
 */

const API_BASE = '/api';

/**
 * Query the knowledge base with a question
 * @param {string} query - The question to ask
 * @param {number} k - Number of documents to retrieve
 * @param {string} provider - LLM provider to use
 * @returns {Promise<Object>} - The query response
 */
export async function queryKnowledgeBase(query, k = 3, provider = 'gemini') {
    const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, k, provider }),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Query failed');
    }

    return response.json();
}

/**
 * Ingest documents into the knowledge base
 * @param {Object} options - Ingestion options
 * @returns {Promise<Object>} - The ingestion response
 */
export async function ingestDocuments(options = {}) {
    const response = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            directory: options.directory || './data/example_inputs',
            chunk: options.chunk !== false,
            chunk_size: options.chunkSize || 800,
            chunk_overlap: options.chunkOverlap || 150,
        }),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Ingestion failed');
    }

    return response.json();
}

/**
 * Check the health of the API
 * @returns {Promise<Object>} - Health status
 */
export async function checkHealth() {
    const response = await fetch(`${API_BASE}/health`);

    if (!response.ok) {
        throw new Error('Health check failed');
    }

    return response.json();
}

/**
 * Get knowledge base statistics
 * @returns {Promise<Object>} - Statistics
 */
export async function getStats() {
    const response = await fetch(`${API_BASE}/stats`);

    if (!response.ok) {
        throw new Error('Failed to get stats');
    }

    return response.json();
}
