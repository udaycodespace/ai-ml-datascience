-- DECISION-MEMORY Migration 005: Decision Actors
-- Entities responsible for the decision (Human or AI)

CREATE TABLE IF NOT EXISTS decision_actors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL REFERENCES decision_records(id),
    team_id UUID NOT NULL REFERENCES teams(id),
    
    -- Actor Definition
    actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN ('human', 'ai_model', 'system')),
    
    -- If Human
    user_id UUID REFERENCES auth.users(id), 
    
    -- If AI
    model_identifier VARCHAR(100), -- e.g., "gpt-4-0613"
    prompt_hash VARCHAR(64), -- SHA-256 of the prompt (Invariant: No raw prompts stored)
    
    -- If User Deleted (Edge Case 13.5)
    is_anonymized BOOLEAN DEFAULT false,
    anonymized_label VARCHAR(50), -- e.g., "Deleted User <Hash>"
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decision_actors_decision ON decision_actors(decision_id);

-- RLS
ALTER TABLE decision_actors ENABLE ROW LEVEL SECURITY;

CREATE POLICY decision_actors_select ON decision_actors
    FOR SELECT USING (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );

CREATE POLICY decision_actors_insert ON decision_actors
    FOR INSERT WITH CHECK (
        team_id IN (SELECT team_id FROM team_memberships WHERE user_id = auth.uid() AND is_active = true)
    );
