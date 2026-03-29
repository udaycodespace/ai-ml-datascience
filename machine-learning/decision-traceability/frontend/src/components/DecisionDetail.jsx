import React, { useState, useEffect } from 'react';
import { useDecisionApi } from '../hooks/useDecisionApi';
import { RationalePanel } from './RationalePanel';
import { OverrideHistory } from './OverrideHistory';
import { RiskIndicators } from './RiskIndicators';

export function DecisionDetail({ token, teamId, decisionId, onBack }) {
    const api = useDecisionApi(token, teamId);
    const [decision, setDecision] = useState(null);
    const [rationale, setRationale] = useState(null);
    const [overrides, setOverrides] = useState([]);
    const [risk, setRisk] = useState(null);
    const [actors, setActors] = useState([]);

    useEffect(() => {
        loadData();
    }, [decisionId]);

    const loadData = async () => {
        try {
            const [d, r, o, riskData, a] = await Promise.all([
                api.getDecision(decisionId),
                api.getRationale(decisionId),
                api.listOverrides(decisionId),
                api.getRiskScore(decisionId),
                api.listActors(decisionId)
            ]);
            setDecision(d);
            setRationale(r);
            setOverrides(o);
            setRisk(riskData);
            setActors(a);
        } catch (err) {
            console.error(err);
        }
    };

    if (!decision) return <div>Loading detail...</div>;

    return (
        <div>
            <div style={{ marginBottom: '1rem' }}>
                <button className="btn" onClick={onBack}>← Back to List</button>
            </div>

            <div className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                        <h1 style={{ fontSize: '2rem' }}>{decision.title}</h1>
                        <span className={`badge badge-${decision.status}`} style={{ fontSize: '1rem', padding: '4px 12px' }}>
                            {decision.status}
                        </span>
                    </div>
                    <div style={{ color: 'var(--color-text-secondary)' }}>
                        ID: <span style={{ fontFamily: 'monospace' }}>{decision.id}</span>
                    </div>
                </div>

                {decision.status !== 'locked' && (
                    <button className="btn" style={{ borderColor: 'var(--color-risk-critical)', color: 'var(--color-risk-critical)' }}
                        onClick={async () => {
                            if (confirm('Are you sure you want to LOCK this decision? This is irreversible.')) {
                                await api.lockDecision(decision.id);
                                loadData();
                            }
                        }}>
                        🔒 Lock Decision
                    </button>
                )}
            </div>

            <div className="grid grid-cols-2">
                <div className="col">
                    <RationalePanel rationale={rationale} />

                    <div className="card">
                        <div className="header"><h3 style={{ margin: 0, fontSize: '1.1rem' }}>Actors</h3></div>
                        <ul style={{ paddingLeft: '1.25rem' }}>
                            {actors.map(a => (
                                <li key={a.id}>
                                    <strong>{a.actor_type}</strong>
                                    {a.model_identifier && <span> ({a.model_identifier})</span>}
                                    {a.is_anonymized && <span style={{ color: 'gray', marginLeft: '0.5rem' }}>[Anonymized]</span>}
                                </li>
                            ))}
                            {actors.length === 0 && <li style={{ color: 'gray' }}>No actors registered</li>}
                        </ul>
                    </div>
                </div>

                <div className="col">
                    <RiskIndicators score={risk} />
                    <OverrideHistory overrides={overrides} />

                    <div className="card">
                        <div className="header"><h3 style={{ margin: 0, fontSize: '1.1rem' }}>Metadata</h3></div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.5rem 1rem', fontSize: '0.9rem' }}>
                            <span style={{ color: 'gray' }}>Type:</span>
                            <span style={{ fontWeight: 500 }}>{decision.decision_type}</span>

                            <span style={{ color: 'gray' }}>Created:</span>
                            <span>{new Date(decision.created_at).toLocaleString()}</span>

                            <span style={{ color: 'gray' }}>Context Status:</span>
                            <span>{decision.context_incomplete ? '⚠️ Incomplete' : '✅ Complete'}</span>

                            {decision.locked_at && (
                                <>
                                    <span style={{ color: 'gray' }}>Locked:</span>
                                    <span>{new Date(decision.locked_at).toLocaleString()}</span>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
