-- DECISION-MEMORY Migration 006: Decision Overrides
-- Manual overrides of System/AI decisions

CREATE TABLE IF NOT EXISTS decision_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decision_records(id),
    team_id UUID NOT NULL REFERENCES teams(id),
    
    -- The Overrider
    overrider_user_id UUID NOT NULL REFERENCES auth.users(id),
    
    -- Rationale
    reason TEXT NOT NULL,
    
    -- Status of this override attempt
    -- Edge Case 13.3: First override wins, concurrent ones rejected
    status VARCHAR(20) NOT NULL CHECK (status IN ('applied', 'rejected')),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decision_overrides_decision ON decision_overrides(decision_id);

-- RLS
ALTER TABLE decision_overrides ENABLE ROW LEVEL SECURITY;

CREATE POLICY decision_overrides_select ON decision_overrides
    FOR SELECT USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

-- Insert requires special role check in application (Manager/Auditor)
-- DB policy just enforces team boundary
CREATE POLICY decision_overrides_insert ON decision_overrides
    FOR INSERT WITH CHECK (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );
