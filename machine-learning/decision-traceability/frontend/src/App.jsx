import React, { useState } from 'react';
import { DecisionList } from './components/DecisionList';
import { DecisionDetail } from './components/DecisionDetail';

// Mock auth for development - in production this comes from ED-BASE context
const MOCK_TOKEN = "dev-token";
const MOCK_TEAM_ID = "22222222-2222-2222-2222-222222222222";

function App() {
    const [view, setView] = useState('list'); // 'list', 'detail', 'policies'
    const [selectedDecisionId, setSelectedDecisionId] = useState(null);

    const handleViewDetail = (id) => {
        setSelectedDecisionId(id);
        setView('detail');
    };

    const Navbar = () => (
        <nav style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)', padding: '0.75rem 2rem' }}>
            <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span style={{ fontWeight: '700', fontSize: '1.25rem' }}>DECISION MEMORY</span>
                    <div style={{ height: '20px', width: '1px', background: 'var(--color-border)' }}></div>
                    <button
                        className={`btn ${view === 'list' || view === 'detail' ? 'btn-primary' : ''}`}
                        onClick={() => { setView('list'); setSelectedDecisionId(null); }}
                        style={{ border: 'none', background: 'transparent', color: view !== 'policies' ? 'var(--color-primary)' : 'var(--color-text-secondary)' }}
                    >
                        Decisions
                    </button>
                    <button
                        className={`btn ${view === 'policies' ? 'btn-primary' : ''}`}
                        onClick={() => setView('policies')}
                        style={{ border: 'none', background: 'transparent', color: view === 'policies' ? 'var(--color-primary)' : 'var(--color-text-secondary)' }}
                    >
                        Policies
                    </button>
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
                    ED-BASE Enterprise
                </div>
            </div>
        </nav>
    );

    return (
        <div style={{ minHeight: '100vh', background: 'var(--color-bg)' }}>
            <Navbar />

            <main className="container">
                {view === 'list' && (
                    <DecisionList
                        token={MOCK_TOKEN}
                        teamId={MOCK_TEAM_ID}
                        onViewDetail={handleViewDetail}
                    />
                )}

                {view === 'detail' && selectedDecisionId && (
                    <DecisionDetail
                        token={MOCK_TOKEN}
                        teamId={MOCK_TEAM_ID}
                        decisionId={selectedDecisionId}
                        onBack={() => setView('list')}
                    />
                )}

                {view === 'policies' && (
                    <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                        <h3>Governance Policies</h3>
                        <p>Policy management view would go here.</p>
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
