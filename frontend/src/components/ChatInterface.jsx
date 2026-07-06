import { useState } from 'react'

/**
 * Chat Interface Component
 * 
 * Provides the query input form with loading, error states, and follow-up questions
 */
function ChatInterface({
    onQuery,
    isLoading,
    error,
    followUpQuestions,
    queryInput,
    setQueryInput,
    showNewQuestionButton,
    onNewQuestion
}) {
    const handleSubmit = (e) => {
        e.preventDefault()
        if (queryInput && queryInput.trim() && !isLoading) {
            onQuery(queryInput.trim())
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSubmit(e)
        }
    }

    const handleFollowUpClick = (question) => {
        setQueryInput(question)
        onQuery(question)
    }

    return (
        <div className="query-card">
            <h2>Ask a Question</h2>
            <form className="query-form" onSubmit={handleSubmit}>
                <div style={{ display: 'flex', gap: '0.75rem', width: '100%' }}>
                    <input
                        type="text"
                        className="query-input"
                        value={queryInput || ''}
                        onChange={(e) => setQueryInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="e.g., What is the resolution target for a P1 incident?"
                        disabled={isLoading}
                        aria-label="Enter your question"
                        style={{ flex: 1 }}
                    />
                    <button
                        type="submit"
                        className={`query-button ${isLoading ? 'loading' : ''}`}
                        disabled={isLoading || !queryInput || !queryInput.trim()}
                    >
                        {isLoading ? (
                            <>
                                <span className="loading-spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                                Thinking...
                            </>
                        ) : (
                            <>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="11" cy="11" r="8" />
                                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                                </svg>
                                Ask
                            </>
                        )}
                    </button>

                    {showNewQuestionButton && !isLoading && (
                        <button
                            type="button"
                            onClick={onNewQuestion}
                            className="new-question-button"
                            style={{
                                padding: '0 1.25rem',
                                borderRadius: '8px',
                                border: '1.5px solid #d1d5db',
                                background: '#f9fafb',
                                color: '#374151',
                                fontSize: '0.9375rem',
                                fontWeight: 500,
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                whiteSpace: 'nowrap'
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.background = '#e5e7eb'
                                e.target.style.borderColor = '#9ca3af'
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.background = '#f9fafb'
                                e.target.style.borderColor = '#d1d5db'
                            }}
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 5v14M5 12h14" />
                            </svg>
                            New
                        </button>
                    )}
                </div>
            </form>

            {error && (
                <div className="error-message" style={{ marginTop: '1rem' }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    {error}
                </div>
            )}

            {followUpQuestions && followUpQuestions.length > 0 && !isLoading && (
                <div style={{ marginTop: '1.5rem' }}>
                    <h3 style={{
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        color: 'var(--color-text-secondary, #475569)',
                        marginBottom: '0.75rem'
                    }}>
                        💡 Follow-up Questions
                    </h3>
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.5rem'
                    }}>
                        {followUpQuestions.map((question, index) => (
                            <button
                                key={index}
                                onClick={() => handleFollowUpClick(question)}
                                style={{
                                    padding: '0.75rem 1rem',
                                    borderRadius: '8px',
                                    border: '1px solid var(--color-border, #E2E8F0)',
                                    background: 'var(--color-bg-subtle, #F8FAFC)',
                                    color: 'var(--color-text-primary, #1A1A1A)',
                                    fontSize: '0.875rem',
                                    textAlign: 'left',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.background = 'var(--color-primary-light, #FFF4F3)'
                                    e.target.style.borderColor = 'var(--color-primary, #FF3621)'
                                    e.target.style.transform = 'translateX(4px)'
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.background = 'var(--color-bg-subtle, #F8FAFC)'
                                    e.target.style.borderColor = 'var(--color-border, #E2E8F0)'
                                    e.target.style.transform = 'translateX(0)'
                                }}
                            >
                                {question}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default ChatInterface
