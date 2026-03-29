-- DECISION-MEMORY Migration 002: Decision Inputs
-- Inputs used in making the decision (data sources, docs, etc.)

CREATE TABLE IF NOT EXISTS decision_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Parent decision (Cascade delete not allowed by PRD constraints "decisions remain", 
    -- but usually standard for child tables. Following loose coupling - FK usually suffices)
    decision_id UUID NOT NULL REFERENCES decision_records(id),
    team_id UUID NOT NULL REFERENCES teams(id),
    
    -- Input Details
    input_type VARCHAR(50) NOT NULL, -- 'data_source', 'document', 'metric', 'user_input'
    source_reference VARCHAR(255), -- ID or URL of the source
    
    -- The actual value/snapshot used
    -- CHECK constraint ensures we don't dump massive blobs without check
    input_data JSONB NOT NULL, 
    
    -- Meta
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Constraint for input size safety (soft check, 1MB limit for JSON text representation approx)
ALTER TABLE decision_inputs 
ADD CONSTRAINT check_input_size CHECK (length(input_data::text) < 1000000);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decision_inputs_decision ON decision_inputs(decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_inputs_team ON decision_inputs(team_id);

-- RLS
ALTER TABLE decision_inputs ENABLE ROW LEVEL SECURITY;

CREATE POLICY decision_inputs_select ON decision_inputs
    FOR SELECT USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

CREATE POLICY decision_inputs_insert ON decision_inputs
    FOR INSERT WITH CHECK (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );
