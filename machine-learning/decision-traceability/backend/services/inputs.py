"""
DECISION-MEMORY Inputs Service
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
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
class DecisionInput:
    id: str
    decision_id: str
    team_id: str
    input_type: str
    source_reference: Optional[str]
    input_data: Dict
    created_at: datetime

def attach_input(
    decision_id: str,
    team_id: str,
    user_id: str,
    input_type: str,
    input_data: Dict,
    source_reference: Optional[str] = None
) -> DecisionInput:
    """Attach an input to a decision record."""
    require_team_access(user_id, team_id, Role.MEMBER)
    
    # Check decision not locked (application logic)
    # Using raw SQL to avoid circular dependency with decisions.py if possible,
    # or just trust the caller. For robustness, simple check:
    check_query = "SELECT status FROM decision_records WHERE id = %s AND team_id = %s"
    with get_cursor() as cur:
        cur.execute(check_query, (decision_id, team_id))
        row = cur.fetchone()
        if not row:
            raise ValueError("Decision not found")
        if row['status'] == 'locked':
            raise ValueError("Cannot attach inputs to locked decision")

    input_json = json.dumps(input_data)
    # DB constraint will check 1MB limit, but we can fail fast here
    if len(input_json) > 1000000:
        raise ValueError("Input data exceeds 1MB limit")

    query = """
        INSERT INTO decision_inputs (
            decision_id, team_id, input_type, source_reference, input_data
        ) VALUES (%s, %s, %s, %s, %s)
        RETURNING id, decision_id, team_id, input_type, source_reference, input_data, created_at
    """
    
    with transaction(IsolationLevel.READ_COMMITTED) as cur:
        cur.execute(query, (decision_id, team_id, input_type, source_reference, input_json))
        row = cur.fetchone()
        
        return DecisionInput(
            id=row['id'],
            decision_id=row['decision_id'],
            team_id=row['team_id'],
            input_type=row['input_type'],
            source_reference=row['source_reference'],
            input_data=row['input_data'],
            created_at=row['created_at']
        )

def list_inputs(decision_id: str, team_id: str, user_id: str) -> List[DecisionInput]:
    require_team_access(user_id, team_id, Role.VIEWER)
    
    query = """
        SELECT id, decision_id, team_id, input_type, source_reference, input_data, created_at
        FROM decision_inputs
        WHERE decision_id = %s AND team_id = %s
        ORDER BY created_at ASC
    """
    
    with get_cursor() as cur:
        cur.execute(query, (decision_id, team_id))
        rows = cur.fetchall()
        return [
            DecisionInput(
                id=r['id'], decision_id=r['decision_id'], team_id=r['team_id'],
                input_type=r['input_type'], source_reference=r['source_reference'],
                input_data=r['input_data'], created_at=r['created_at']
            )
            for r in rows
        ]
