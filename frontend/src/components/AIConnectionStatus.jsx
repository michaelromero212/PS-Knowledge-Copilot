import { useState, useEffect } from 'react'

/**
 * AI Connection Status Component
 * 
 * Displays the current AI provider connection status with visual indicators
 */
function AIConnectionStatus({ provider = 'gemini', onStatusChange }) {
    const [status, setStatus] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchStatus = async () => {
        setLoading(true)
        setError(null)

        try {
            const response = await fetch(`/api/ai-status?provider=${provider}`)

            if (!response.ok) {
                throw new Error('Failed to fetch AI status')
            }

            const data = await response.json()
            setStatus(data)
            if (onStatusChange) {
                onStatusChange(data)
            }
        } catch (err) {
            setError(err.message)
            if (onStatusChange) {
                onStatusChange({ status: 'disconnected', provider, model: null, details: err.message })
            }
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchStatus()

        // Refresh status every 30 seconds
        const interval = setInterval(fetchStatus, 30000)

        return () => clearInterval(interval)
    }, [provider])

    const getStatusColor = () => {
        if (!status) return '#6b7280'
        switch (status.status) {
            case 'connected':
                return '#10b981'
            case 'degraded':
                return '#f59e0b'
            case 'disconnected':
                return '#ef4444'
            default:
                return '#6b7280'
        }
    }

    const getStatusIcon = () => {
        if (loading) {
            return (
                <div className="loading-spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
            )
        }

        if (error || !status) {
            return (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="15" y1="9" x2="9" y2="15" />
                    <line x1="9" y1="9" x2="15" y2="15" />
                </svg>
            )
        }

        if (status.status === 'connected') {
            return (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12" />
                </svg>
            )
        }

        return (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
        )
    }

    const getDisplayText = () => {
        if (loading) return 'Checking AI connection...'
        if (error) return 'Connection error'
        if (!status) return 'Unknown status'

        const providerName = status.provider.replace('_', ' ').split(' ').map(
            word => word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ')

        return `${providerName}: ${status.status}`
    }

    return (
        <div className="ai-status-container" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: '6px',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            fontSize: '0.875rem',
            color: getStatusColor(),
            transition: 'all 0.2s ease'
        }}>
            {getStatusIcon()}
            <span style={{ fontWeight: 500 }}>{getDisplayText()}</span>

            {status?.model && (
                <span style={{
                    color: 'rgba(255, 255, 255, 0.5)',
                    fontSize: '0.75rem',
                    marginLeft: '4px'
                }}>
                    ({status.model.split('/').pop()})
                </span>
            )}

            {!loading && (
                <button
                    onClick={fetchStatus}
                    style={{
                        background: 'none',
                        border: 'none',
                        padding: '2px',
                        cursor: 'pointer',
                        color: 'rgba(255, 255, 255, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        marginLeft: '4px'
                    }}
                    title="Refresh status"
                    aria-label="Refresh AI connection status"
                >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="23 4 23 10 17 10" />
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                    </svg>
                </button>
            )}
        </div>
    )
}

export default AIConnectionStatus
