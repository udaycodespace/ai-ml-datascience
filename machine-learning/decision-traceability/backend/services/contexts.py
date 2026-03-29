"""
DECISION-MEMORY Contexts Service
"""

from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
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
class DecisionContext:
    id: str
    decision_id: str
    team_id: str
    constraints: List[Dict]
    assumptions: List[Dict]
    policies_applied: List[str]
    version: int
    created_at: datetime

def set_context(
    decision_id: str,
    team_id: str,
    user_id: str,
    constraints: List[Dict],
    assumptions: List[Dict],
    policies_applied: List[str]
) -> DecisionContext:
    """Set or update context for a decision (creates new version)."""
    require_team_access(user_id, team_id, Role.MEMBER)
    
    # Check lock status
    with get_cursor() as cur:
        cur.execute("SELECT status FROM decision_records WHERE id = %s AND team_id = %s", (decision_id, team_id))
        row = cur.fetchone()
        if not row or row['status'] == 'locked':
            raise ValueError("Decision not found or locked")

    # Get latest version
    version = 1
    with get_cursor() as cur:
        cur.execute(
            "SELECT MAX(version) as max_v FROM decision_contexts WHERE decision_id = %s", 
            (decision_id,)
        )
        res = cur.fetchone()
        if res and res['max_v']:
            version = res['max_v'] + 1

    query = """
        INSERT INTO decision_contexts (
            decision_id, team_id, constraints, assumptions, policies_applied, version
        ) VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, decision_id, team_id, constraints, assumptions, policies_applied, version, created_at
    """
    
    with transaction(IsolationLevel.READ_COMMITTED) as cur:
        cur.execute(query, (
            decision_id, team_id, 
            json.dumps(constraints), 
            json.dumps(assumptions), 
            json.dumps(policies_applied), 
            version
        ))
        row = cur.fetchone()
        return DecisionContext(
            id=row['id'], decision_id=row['decision_id'], team_id=row['team_id'],
            constraints=row['constraints'], assumptions=row['assumptions'],
            policies_applied=row['policies_applied'], version=row['version'],
            created_at=row['created_at']
        )

def get_context(decision_id: str, team_id: str, user_id: str) -> Optional[DecisionContext]:
    """Get latest context for decision."""
    require_team_access(user_id, team_id, Role.VIEWER)
    
    query = """
        SELECT id, decision_id, team_id, constraints, assumptions, policies_applied, version, created_at
        FROM decision_contexts
        WHERE decision_id = %s AND team_id = %s
        ORDER BY version DESC LIMIT 1
    """
    
    with get_cursor() as cur:
        cur.execute(query, (decision_id, team_id))
        row = cur.fetchone()
        if not row:
            return None
        return DecisionContext(
            id=row['id'], decision_id=row['decision_id'], team_id=row['team_id'],
            constraints=row['constraints'], assumptions=row['assumptions'],
            policies_applied=row['policies_applied'], version=row['version'],
            created_at=row['created_at']
        )
