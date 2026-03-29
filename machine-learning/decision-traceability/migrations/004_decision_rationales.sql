-- DECISION-MEMORY Migration 004: Decision Rationales
-- The "Why" behind the decision

CREATE TABLE IF NOT EXISTS decision_rationales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decision_records(id),
    team_id UUID NOT NULL REFERENCES teams(id),
    
    -- Rationale Content
    content_text TEXT NOT NULL,
    content_format VARCHAR(20) DEFAULT 'markdown', -- 'text', 'markdown'
    
    -- Source
    author_type VARCHAR(20) NOT NULL CHECK (author_type IN ('human', 'ai')),
    
    -- For AI Author
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1.0),
    
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Length Constraint (10k chars)
ALTER TABLE decision_rationales 
ADD CONSTRAINT check_rationale_length CHECK (length(content_text) <= 10000);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decision_rationales_decision ON decision_rationales(decision_id);

-- RLS
ALTER TABLE decision_rationales ENABLE ROW LEVEL SECURITY;

CREATE POLICY decision_rationales_select ON decision_rationales
    FOR SELECT USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

CREATE POLICY decision_rationales_insert ON decision_rationales
    FOR INSERT WITH CHECK (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );
