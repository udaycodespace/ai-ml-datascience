-- DECISION-MEMORY Migration 007: Decision Policies
-- Governance rules that decisions are checked against

CREATE TABLE IF NOT EXISTS decision_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id),
    
    -- Policy Definition
    name VARCHAR(100) NOT NULL,
    description TEXT,
    rule_definition JSONB DEFAULT '{}', -- Structure dependent on rule engine
    
    -- Lifecycle
    is_active BOOLEAN DEFAULT true,
    version INT DEFAULT 1,
    
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE(team_id, name, version) -- Versioned uniqueness
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decision_policies_team ON decision_policies(team_id);
CREATE INDEX IF NOT EXISTS idx_decision_policies_active ON decision_policies(team_id) WHERE is_active = true;

-- RLS
ALTER TABLE decision_policies ENABLE ROW LEVEL SECURITY;

CREATE POLICY decision_policies_select ON decision_policies
    FOR SELECT USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

CREATE POLICY decision_policies_insert ON decision_policies
    FOR INSERT WITH CHECK (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

CREATE POLICY decision_policies_update ON decision_policies
    FOR UPDATE USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );
