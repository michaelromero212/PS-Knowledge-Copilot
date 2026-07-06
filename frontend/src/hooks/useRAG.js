import { useState, useCallback } from 'react';
import { queryKnowledgeBase } from '../api/ragService';

/**
 * Custom hook for RAG query functionality
 * 
 * Provides state management and API integration for querying the knowledge base
 */
export function useRAG() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([]);

    const query = useCallback(async (queryText, options = {}) => {
        if (!queryText.trim()) {
            setError('Please enter a question');
            return null;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await queryKnowledgeBase(
                queryText,
                options.k || 3,
                options.provider || 'gemini'
            );

            setResult(response);

            // Add to history
            setHistory(prev => [
                {
                    id: Date.now(),
                    query: queryText,
                    answer: response.answer,
                    sources: response.sources,
                    timestamp: new Date(),
                    processingTime: response.processing_time_ms,
                },
                ...prev.slice(0, 9), // Keep last 10 queries
            ]);

            return response;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setIsLoading(false);
        }
    }, []);

    const clearResult = useCallback(() => {
        setResult(null);
        setError(null);
    }, []);

    const clearHistory = useCallback(() => {
        setHistory([]);
    }, []);

    return {
        query,
        isLoading,
        error,
        result,
        history,
        clearResult,
        clearHistory,
    };
}
