import React, { useState, useEffect } from 'react';
import { useDecisionApi } from '../hooks/useDecisionApi';

export function DecisionList({ token, teamId, onViewDetail }) {
    const { listDecisions, loading, error } = useDecisionApi(token, teamId);
    const [decisions, setDecisions] = useState([]);
    const [filter, setFilter] = useState('');

    useEffect(() => {
        loadDecisions();
    }, [filter]);

    const loadDecisions = async () => {
        try {
            const opts = filter ? { status: filter } : {};
            const data = await listDecisions(opts);
            setDecisions(data);
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) return <div>Loading decisions...</div>;
    if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;

    return (
        <div>
            <div className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1>Decisions</h1>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="btn" onClick={() => setFilter('')}>All</button>
                    <button className="btn" onClick={() => setFilter('draft')}>Draft</button>
                    <button className="btn" onClick={() => setFilter('active')}>Active</button>
                    <button className="btn" onClick={() => setFilter('locked')}>Locked</button>
                </div>
            </div>

            <div className="card" style={{ padding: 0 }}>
                <table className="table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Type</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {decisions.map(d => (
                            <tr key={d.id}>
                                <td style={{ fontWeight: 500 }}>{d.title}</td>
                                <td>
                                    <span className="badge" style={{
                                        background: d.decision_type === 'automated' ? '#e0f2fe' : '#f3f4f6',
                                        color: d.decision_type === 'automated' ? '#0369a1' : '#374151'
                                    }}>
                                        {d.decision_type}
                                    </span>
                                </td>
                                <td>
                                    <span className={`badge badge-${d.status}`}>
                                        {d.status}
                                    </span>
                                </td>
                                <td>{new Date(d.created_at).toLocaleDateString()}</td>
                                <td>
                                    <button className="btn btn-primary" style={{ padding: '4px 12px', fontSize: '0.875rem' }} onClick={() => onViewDetail(d.id)}>
                                        View
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {decisions.length === 0 && (
                            <tr>
                                <td colSpan="5" style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>
                                    No decisions found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
