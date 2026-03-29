-- DECISION-MEMORY Migration 003: Decision Contexts
-- Surrounding constraints, assumptions, and active policies

CREATE TABLE IF NOT EXISTS decision_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decision_records(id),
    team_id UUID NOT NULL REFERENCES teams(id),
    
    -- Contextual Data
    constraints JSONB DEFAULT '[]', -- List of constraints considered
    assumptions JSONB DEFAULT '[]', -- List of assumptions made
    policies_applied JSONB DEFAULT '[]', -- Snapshot of policy IDs valid at this time
    
    -- Versioning in case context changes during draft
    version INT NOT NULL DEFAULT 1,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decision_contexts_decision ON decision_contexts(decision_id);

-- RLS
ALTER TABLE decision_contexts ENABLE ROW LEVEL SECURITY;

CREATE POLICY decision_contexts_select ON decision_contexts
    FOR SELECT USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

CREATE POLICY decision_contexts_insert ON decision_contexts
    FOR INSERT WITH CHECK (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );
