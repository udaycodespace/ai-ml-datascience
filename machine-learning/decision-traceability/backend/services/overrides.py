"""
DECISION-MEMORY Overrides Service
"""

from datetime import datetime
from typing import List
from dataclasses import dataclass
import structlog
import sys

sys.path.insert(0, '../../../backend')
from utils import get_cursor
from services import (
    transaction,
    IsolationLevel,
    require_team_access,
    Role,
    log_event,
    EventType,
    ActorType
)

logger = structlog.get_logger(__name__)

@dataclass
class DecisionOverride:
    id: str
    decision_id: str
    team_id: str
    overrider_user_id: str
    reason: str
    status: str
    created_at: datetime

def create_override(
    decision_id: str,
    team_id: str,
    user_id: str,
    reason: str
) -> DecisionOverride:
    """
    Override a decision. 
    First override wins -> 'applied'. Subsequent -> 'rejected'.
    Requires ADMIN or OWNER role (Manager/Auditor equivalent).
    """
    # Authorization: Manager/Auditor role -> Mapping to Admin/Owner in ED-BASE
    require_team_access(user_id, team_id, Role.ADMIN)
    
    # Check decision state
    with get_cursor() as cur:
        cur.execute("SELECT status FROM decision_records WHERE id = %s AND team_id = %s", (decision_id, team_id))
        row = cur.fetchone()
        if not row:
            raise ValueError("Decision not found")
        if row['status'] == 'locked':
            raise ValueError("Cannot override locked decision")

    query = """
        INSERT INTO decision_overrides (
            decision_id, team_id, overrider_user_id, reason, status
        )
        SELECT %s, %s, %s, %s,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM decision_overrides 
                    WHERE decision_id = %s AND status = 'applied'
                ) THEN 'rejected'
                ELSE 'applied'
            END
        RETURNING id, decision_id, team_id, overrider_user_id, reason, status, created_at
    """
    
    with transaction(IsolationLevel.SERIALIZABLE) as cur:
        cur.execute(query, (decision_id, team_id, user_id, reason, decision_id))
        row = cur.fetchone()
        
        override = DecisionOverride(
            id=row['id'], decision_id=row['decision_id'], team_id=row['team_id'],
            overrider_user_id=row['overrider_user_id'], reason=row['reason'],
            status=row['status'], created_at=row['created_at']
        )
        
        log_event(
            event_type=EventType.STATE_UPDATE,
            action=f"Override {override.status}",
            actor_id=user_id,
            actor_type=ActorType.USER,
            resource_type="decision_override",
            resource_id=override.id,
            details={'decision_id': decision_id, 'status': override.status}
        )
        
        return override

def list_overrides(decision_id: str, team_id: str, user_id: str) -> List[DecisionOverride]:
    require_team_access(user_id, team_id, Role.VIEWER)
    query = """
        SELECT id, decision_id, team_id, overrider_user_id, reason, status, created_at
        FROM decision_overrides
        WHERE decision_id = %s AND team_id = %s
        ORDER BY created_at ASC
    """
    with get_cursor() as cur:
        cur.execute(query, (decision_id, team_id))
        rows = cur.fetchall()
        return [
            DecisionOverride(
                id=r['id'], decision_id=r['decision_id'], team_id=r['team_id'],
                overrider_user_id=r['overrider_user_id'], reason=r['reason'],
                status=r['status'], created_at=r['created_at']
            )
            for r in rows
        ]
