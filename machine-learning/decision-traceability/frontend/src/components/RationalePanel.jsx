import React from 'react';

export function RationalePanel({ rationale }) {
    if (!rationale) {
        return (
            <div className="card" style={{ borderStyle: 'dashed', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                No rationale recorded yet.
            </div>
        );
    }

    return (
        <div className="card">
            <div className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Rationale</h3>
                <div>
                    <span className="badge" style={{ marginRight: '0.5rem' }}>v{rationale.version}</span>
                    <span className="badge" style={{
                        background: rationale.author_type === 'ai' ? '#c4b5fd' : '#d1fae5',
                        color: rationale.author_type === 'ai' ? '#4c1d95' : '#065f46'
                    }}>
                        {rationale.author_type === 'ai' ? 'AI Generated' : 'Human Author'}
                    </span>
                </div>
            </div>

            {rationale.author_type === 'ai' && (
                <div style={{ marginBottom: '1rem', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
                    Confidence Score: <strong>{(rationale.confidence_score * 100).toFixed(1)}%</strong>
                </div>
            )}

            <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.95rem', background: '#f8fafc', padding: '1rem', borderRadius: '4px' }}>
                {rationale.content_text}
            </div>

            <div style={{ marginTop: '0.5rem', textAlign: 'right', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                Recorded: {new Date(rationale.created_at).toLocaleString()}
            </div>
        </div>
    );
}
