import React from 'react';

export function OverrideHistory({ overrides }) {
    if (!overrides || overrides.length === 0) return null;

    return (
        <div className="card">
            <div className="header" style={{ marginBottom: '1rem', paddingBottom: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Override History</h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {overrides.map(override => (
                    <div key={override.id} style={{
                        borderLeft: `4px solid ${override.status === 'applied' ? 'var(--color-risk-critical)' : 'var(--color-text-secondary)'}`,
                        paddingLeft: '1rem',
                        paddingTop: '0.25rem',
                        paddingBottom: '0.25rem'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                            <span>{new Date(override.created_at).toLocaleString()}</span>
                            <span style={{ fontWeight: '600', textTransform: 'uppercase' }}>{override.status}</span>
                        </div>
                        <div style={{ marginTop: '0.5rem' }}>
                            <strong>Reason:</strong> {override.reason}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
