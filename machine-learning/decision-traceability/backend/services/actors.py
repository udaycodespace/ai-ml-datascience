"""
DECISION-MEMORY Actors Service
"""

from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
import hashlib
import structlog
import sys

sys.path.insert(0, '../../../backend')
from utils import get_cursor
from services import (
    transaction,
    IsolationLevel,
    require_team_access,
    Role,
)

logger = structlog.get_logger(__name__)

@dataclass
class DecisionActor:
    id: str
    decision_id: str
    team_id: str
    actor_type: str
    user_id: Optional[str]
    model_identifier: Optional[str]
    prompt_hash: Optional[str]
    is_anonymized: bool
    anonymized_label: Optional[str]

def register_actor(
    decision_id: str,
    team_id: str,
    user_id: str,
    actor_type: str, # 'human', 'ai_model', 'system'
    real_user_id: Optional[str] = None, # If human
    model_identifier: Optional[str] = None,
    prompt_text: Optional[str] = None
) -> DecisionActor:
    """Register an actor for a decision."""
    require_team_access(user_id, team_id, Role.MEMBER)
    
    prompt_hash = None
    if actor_type == 'ai_model':
        if not model_identifier:
            raise ValueError("AI model requires identifier")
        if prompt_text:
            # Store HASH only (Invariant constraint)
            prompt_hash = hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()
    
    query = """
        INSERT INTO decision_actors (
            decision_id, team_id, actor_type, user_id, 
            model_identifier, prompt_hash
        ) VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, decision_id, team_id, actor_type, user_id, 
                  model_identifier, prompt_hash, is_anonymized, anonymized_label
    """
    
    with transaction(IsolationLevel.READ_COMMITTED) as cur:
        cur.execute(query, (
            decision_id, team_id, actor_type, real_user_id,
            model_identifier, prompt_hash
        ))
        row = cur.fetchone()
        return DecisionActor(
            id=row['id'], decision_id=row['decision_id'], team_id=row['team_id'],
            actor_type=row['actor_type'], user_id=row['user_id'],
            model_identifier=row['model_identifier'], prompt_hash=row['prompt_hash'],
            is_anonymized=row['is_anonymized'], anonymized_label=row['anonymized_label']
        )

def get_actors(decision_id: str, team_id: str, user_id: str) -> List[DecisionActor]:
    require_team_access(user_id, team_id, Role.VIEWER)
    
    query = """
        SELECT id, decision_id, team_id, actor_type, user_id, 
               model_identifier, prompt_hash, is_anonymized, anonymized_label
        FROM decision_actors
        WHERE decision_id = %s AND team_id = %s
    """
    
    with get_cursor() as cur:
        cur.execute(query, (decision_id, team_id))
        rows = cur.fetchall()
        return [
            DecisionActor(
                id=r['id'], decision_id=r['decision_id'], team_id=r['team_id'],
                actor_type=r['actor_type'], user_id=r['user_id'],
                model_identifier=r['model_identifier'], prompt_hash=r['prompt_hash'],
                is_anonymized=r['is_anonymized'], anonymized_label=r['anonymized_label']
            )
            for r in rows
        ]
