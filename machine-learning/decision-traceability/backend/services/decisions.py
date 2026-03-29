"""
DECISION-MEMORY Decisions Service
Core lifecycle management for decision records.
Inherits ED-BASE security guarantees.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
import structlog

import sys
sys.path.insert(0, '../../../backend')

from utils import get_cursor, DatabaseError
from services import (
    transaction,
    IsolationLevel,
    log_event,
    EventType,
    ActorType,
    require_team_access,
    Role,
)
from services.idempotency import IdempotencyContext

logger = structlog.get_logger(__name__)


@dataclass
class DecisionRecord:
    id: str
    team_id: str
    title: str
    decision_type: str
    status: str
    context_incomplete: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    locked_at: Optional[datetime]


def create_decision(
    team_id: str,
    user_id: str,
    title: str,
    decision_type: str,
    idempotency_key: Optional[str] = None
) -> DecisionRecord:
    """
    Create a new decision record with idempotency support.
    Status starts as 'draft'.
    """
    require_team_access(user_id, team_id, Role.MEMBER)
    
    # Validation
    if decision_type not in ('human', 'ai_assisted', 'automated'):
        raise ValueError(f"Invalid decision type: {decision_type}")

    request_body = json.dumps({
        'team_id': team_id,
        'title': title,
        'decision_type': decision_type
    }).encode('utf-8')

    # Idempotency wrapper (Invariant #2)
    with IdempotencyContext(idempotency_key, user_id, request_body) as ctx:
        if not ctx.should_process:
            return DecisionRecord(**ctx.response)

        query = """
            INSERT INTO decision_records (
                team_id, title, decision_type, status, created_by
            ) VALUES (%s, %s, %s, 'draft', %s)
            RETURNING id, team_id, title, decision_type, status, 
                      context_incomplete, created_by, created_at, updated_at, locked_at
        """
        
        with transaction(IsolationLevel.READ_COMMITTED) as cur:
            cur.execute(query, (team_id, title, decision_type, user_id))
            row = cur.fetchone()
            
            # Audit Log (Invariant #5, #10)
            log_event(
                event_type=EventType.STATE_CREATE,
                action="Created decision draft",
                actor_id=user_id,
                actor_type=ActorType.USER,
                resource_type="decision_record",
                resource_id=row['id'],
                details={'title': title, 'type': decision_type}
            )
            
            record = DecisionRecord(**row)
            ctx.set_response(row) # Cache response for idempotency
            return record


def get_decision(decision_id: str, team_id: str, user_id: str) -> Optional[DecisionRecord]:
    """Get decision by ID with team scoping."""
    require_team_access(user_id, team_id, Role.VIEWER)
    
    query = """
        SELECT id, team_id, title, decision_type, status, 
               context_incomplete, created_by, created_at, updated_at, locked_at
        FROM decision_records
        WHERE id = %s AND team_id = %s
    """
    
    with get_cursor() as cur:
        cur.execute(query, (decision_id, team_id))
        row = cur.fetchone()
        if not row:
            return None
        return DecisionRecord(**row)


def lock_decision(
    decision_id: str,
    team_id: str,
    user_id: str
) -> DecisionRecord:
    """
    Finalize a decision, moving status to 'locked'.
    Irreversible action.
    """
    require_team_access(user_id, team_id, Role.MEMBER) # Standard members can lock their work
    
    query = """
        UPDATE decision_records
        SET status = 'locked', locked_at = %s, updated_at = %s
        WHERE id = %s AND team_id = %s AND status != 'locked'
        RETURNING id, team_id, title, decision_type, status, 
                  context_incomplete, created_by, created_at, updated_at, locked_at
    """
    
    now = datetime.now(timezone.utc)
    
    with transaction(IsolationLevel.REPEATABLE_READ) as cur:
        cur.execute(query, (now, now, decision_id, team_id))
        row = cur.fetchone()
        
        if not row:
            # Check if it was already locked or doesn't exist
            current = get_decision(decision_id, team_id, user_id)
            if not current:
                raise ValueError("Decision not found")
            if current.status == 'locked':
                raise ValueError("Decision already locked")
            raise DatabaseError("Failed to lock decision")

        log_event(
            event_type=EventType.STATE_UPDATE,
            action="Locked decision",
            actor_id=user_id,
            actor_type=ActorType.USER,
            resource_type="decision_record",
            resource_id=decision_id,
            details={'status': 'locked'}
        )
        
        return DecisionRecord(**row)


def list_decisions(
    team_id: str,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[DecisionRecord]:
    """List decisions for a team with pagination."""
    require_team_access(user_id, team_id, Role.VIEWER)
    
    query = """
        SELECT id, team_id, title, decision_type, status, 
               context_incomplete, created_by, created_at, updated_at, locked_at
        FROM decision_records
        WHERE team_id = %s
    """
    params = [team_id]
    
    if status:
        query += " AND status = %s"
        params.append(status)
        
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    with get_cursor() as cur:
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        return [DecisionRecord(**row) for row in rows]
