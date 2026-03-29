-- DECISION-MEMORY Migration 001: Decision Records
-- Core entity for tracking decision event lifecycle

CREATE TABLE IF NOT EXISTS decision_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Team isolation (inherits ED-BASE pattern)
    team_id UUID NOT NULL REFERENCES teams(id),
    
    -- Decision classification
    title VARCHAR(255) NOT NULL,
    decision_type VARCHAR(50) NOT NULL CHECK (decision_type IN ('human', 'ai_assisted', 'automated')),
    
    -- Lifecycle Management
    status VARCHAR(50) NOT NULL CHECK (status IN ('draft', 'active', 'locked')),
    
    -- Context Flags for Edge Cases
    context_incomplete BOOLEAN NOT NULL DEFAULT false,
    
    -- Audit Timestamps
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked_at TIMESTAMPTZ
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_decision_records_team ON decision_records(team_id);
CREATE INDEX IF NOT EXISTS idx_decision_records_status ON decision_records(status);
CREATE INDEX IF NOT EXISTS idx_decision_records_created_at ON decision_records(created_at);
CREATE INDEX IF NOT EXISTS idx_decision_records_type ON decision_records(decision_type);

-- RLS Policy (team isolation)
ALTER TABLE decision_records ENABLE ROW LEVEL SECURITY;

-- Select: See decisions for your team
CREATE POLICY decision_records_select ON decision_records
    FOR SELECT USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

-- Insert: Create decisions for your team
CREATE POLICY decision_records_insert ON decision_records
    FOR INSERT WITH CHECK (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

-- Update: Update decisions for your team (application logic handles status checks like 'locked')
CREATE POLICY decision_records_update ON decision_records
    FOR UPDATE USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );
