-- DECISION-MEMORY Migration 008: Decision Risk Scores
-- Computed risk classification

CREATE TABLE IF NOT EXISTS decision_risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decision_records(id),
    team_id UUID NOT NULL REFERENCES teams(id),
    
    -- Score
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    score_value INT CHECK (score_value >= 0 AND score_value <= 100),
    
    -- Breakdown
    factors JSONB DEFAULT '{}', -- e.g., { "ai_involved": true, "override": false }
    
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decision_risk_decision ON decision_risk_scores(decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_risk_level ON decision_risk_scores(risk_level);

-- RLS
ALTER TABLE decision_risk_scores ENABLE ROW LEVEL SECURITY;

CREATE POLICY decision_risk_scores_select ON decision_risk_scores
    FOR SELECT USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

CREATE POLICY decision_risk_scores_insert ON decision_risk_scores
    FOR INSERT WITH CHECK (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );
