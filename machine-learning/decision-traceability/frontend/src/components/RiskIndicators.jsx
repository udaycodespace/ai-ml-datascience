import React from 'react';

export function RiskIndicators({ score }) {
    if (!score) return null;

    return (
        <div className="card">
            <div className="header" style={{ marginBottom: '1rem', paddingBottom: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Risk Assessment</h3>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                <span className={`risk-badge risk-${score.risk_level}`}>
                    {score.risk_level}
                </span>
                <span style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                    {score.score_value}/100
                </span>
            </div>

            <div>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>Contributing Factors:</h4>
                <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.9rem' }}>
                    {score.factors.context_incomplete && <li>Context Incomplete (+30)</li>}
                    {score.factors.ai_assisted && <li>AI Assisted (+20)</li>}
                    {score.factors.automated && <li>automated Decision (+40)</li>}
                    {score.factors.has_override && <li>Has Override (+50)</li>}
                    {score.factors.missing_rationale && <li>Missing Rationale (+50)</li>}
                </ul>
            </div>
        </div>
    );
}
