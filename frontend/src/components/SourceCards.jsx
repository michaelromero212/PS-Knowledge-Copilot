import { useState } from 'react'

/**
 * Source Cards Component
 * 
 * Displays the source documents with AI analysis capabilities
 */
function SourceCards({ sources, provider = 'gemini' }) {
    const [analyzing, setAnalyzing] = useState({})
    const [analyses, setAnalyses] = useState({})

    if (!sources || sources.length === 0) {
        return null
    }

    const analyzeDocument = async (index, text) => {
        setAnalyzing(prev => ({ ...prev, [index]: true }))

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, provider })
            })

            if (!response.ok) {
                throw new Error('Analysis failed')
            }

            const data = await response.json()
            setAnalyses(prev => ({ ...prev, [index]: data }))
        } catch (err) {
            console.error('Error analyzing document:', err)
            setAnalyses(prev => ({
                ...prev,
                [index]: {
                    summary: 'Analysis failed. Please try again.',
                    tags: [],
                    complexity: 'unknown'
                }
            }))
        } finally {
            setAnalyzing(prev => ({ ...prev, [index]: false }))
        }
    }

    const getComplexityColor = (complexity) => {
        switch (complexity) {
            case 'beginner': return '#10b981'
            case 'intermediate': return '#f59e0b'
            case 'advanced': return '#ef4444'
            default: return '#6b7280'
        }
    }

    return (
        <div className="sources-section" style={{ padding: '0 1.5rem 1.5rem' }}>
            <h4 className="sources-header">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
                Sources ({sources.length})
            </h4>
            <div className="sources-list">
                {sources.map((source, index) => (
                    <div key={index} className="source-card">
                        <div className="source-title">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                                <polyline points="13 2 13 9 20 9" />
                            </svg>
                            {source.source}
                            {source.chunk_index !== null && source.chunk_index !== undefined && (
                                <span className="source-chunk-badge">
                                    Chunk {source.chunk_index + 1}
                                </span>
                            )}
                        </div>
                        <p className="source-excerpt">{source.content}</p>

                        {!analyses[index] && (
                            <button
                                onClick={() => analyzeDocument(index, source.content)}
                                disabled={analyzing[index]}
                                style={{
                                    marginTop: '0.75rem',
                                    padding: '0.5rem 1rem',
                                    borderRadius: '6px',
                                    border: '1px solid var(--color-primary, #FF3621)',
                                    background: 'var(--color-primary-light, #FFF4F3)',
                                    color: 'var(--color-primary, #FF3621)',
                                    fontWeight: 600,
                                    fontSize: '0.8125rem',
                                    cursor: analyzing[index] ? 'not-allowed' : 'pointer',
                                    transition: 'all 0.2s ease',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem'
                                }}
                            >
                                {analyzing[index] ? (
                                    <>
                                        <div className="loading-spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
                                        Analyzing...
                                    </>
                                ) : (
                                    <>
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M12 20h9" />
                                            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                                        </svg>
                                        Analyze with AI
                                    </>
                                )}
                            </button>
                        )}

                        {analyses[index] && (
                            <div style={{
                                marginTop: '1rem',
                                padding: '1rem',
                                borderRadius: '8px',
                                background: 'var(--color-bg-subtle, #F8FAFC)',
                                border: '1px solid var(--color-border, #E2E8F0)'
                            }}>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    marginBottom: '0.75rem'
                                }}>
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                                    </svg>
                                    <span style={{
                                        fontSize: '0.875rem',
                                        fontWeight: 600,
                                        color: 'var(--color-text-primary, #1A1A1A)'
                                    }}>
                                        AI Analysis
                                    </span>
                                    {analyses[index].complexity && (
                                        <span style={{
                                            marginLeft: 'auto',
                                            padding: '0.25rem 0.5rem',
                                            borderRadius: '4px',
                                            fontSize: '0.75rem',
                                            fontWeight: 600,
                                            backgroundColor: getComplexityColor(analyses[index].complexity) + '20',
                                            color: getComplexityColor(analyses[index].complexity),
                                            textTransform: 'capitalize'
                                        }}>
                                            {analyses[index].complexity}
                                        </span>
                                    )}
                                </div>

                                <p style={{
                                    fontSize: '0.875rem',
                                    lineHeight: '1.5',
                                    color: 'var(--color-text-secondary, #475569)',
                                    marginBottom: '0.75rem'
                                }}>
                                    {analyses[index].summary}
                                </p>

                                {analyses[index].tags && analyses[index].tags.length > 0 && (
                                    <div style={{
                                        display: 'flex',
                                        flexWrap: 'wrap',
                                        gap: '0.5rem'
                                    }}>
                                        {analyses[index].tags.map((tag, tagIndex) => (
                                            <span
                                                key={tagIndex}
                                                style={{
                                                    padding: '0.25rem 0.625rem',
                                                    borderRadius: '12px',
                                                    fontSize: '0.75rem',
                                                    fontWeight: 500,
                                                    background: 'var(--color-primary-light, #FFF4F3)',
                                                    color: 'var(--color-primary, #FF3621)',
                                                    border: '1px solid var(--color-border, #E2E8F0)'
                                                }}
                                            >
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}

export default SourceCards
