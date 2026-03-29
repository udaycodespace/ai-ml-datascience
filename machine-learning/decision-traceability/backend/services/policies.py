"""
DECISION-MEMORY Policies Service
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
class DecisionPolicy:
    id: str
    team_id: str
    name: str
    description: Optional[str]
    rule_definition: Dict
    is_active: bool
    version: int
    created_by: str
    created_at: datetime

def create_policy(
    team_id: str,
    user_id: str,
    name: str,
    rule_definition: Dict,
    description: Optional[str] = None
) -> DecisionPolicy:
    """Create a new policy version."""
    require_team_access(user_id, team_id, Role.ADMIN)
    
    # Get next version
    version = 1
    with get_cursor() as cur:
        cur.execute(
            "SELECT MAX(version) as max_v FROM decision_policies WHERE team_id = %s AND name = %s",
            (team_id, name)
        )
        res = cur.fetchone()
        if res and res['max_v']:
            version = res['max_v'] + 1

    query = """
        INSERT INTO decision_policies (
            team_id, name, description, rule_definition, 
            is_active, version, created_by
        ) VALUES (%s, %s, %s, %s, true, %s, %s)
        RETURNING id, team_id, name, description, rule_definition, 
                  is_active, version, created_by, created_at
    """
    
    with transaction(IsolationLevel.READ_COMMITTED) as cur:
        cur.execute(query, (
            team_id, name, description, 
            json.dumps(rule_definition), version, user_id
        ))
        row = cur.fetchone()
        return DecisionPolicy(
            id=row['id'], team_id=row['team_id'], name=row['name'],
            description=row['description'], rule_definition=row['rule_definition'],
            is_active=row['is_active'], version=row['version'],
            created_by=row['created_by'], created_at=row['created_at']
        )

def list_policies(team_id: str, user_id: str, active_only: bool = True) -> List[DecisionPolicy]:
    require_team_access(user_id, team_id, Role.VIEWER)
    
    query = """
        SELECT id, team_id, name, description, rule_definition, 
               is_active, version, created_by, created_at
        FROM decision_policies
        WHERE team_id = %s
    """
    if active_only:
        query += " AND is_active = true"
    
    # Get latest version for each name if not specified otherwise
    # Simplifying to listing all for now, ordered by name, version
    query += " ORDER BY name, version DESC"
    
    with get_cursor() as cur:
        cur.execute(query, (team_id,))
        rows = cur.fetchall()
        return [
            DecisionPolicy(
                id=r['id'], team_id=r['team_id'], name=r['name'],
                description=r['description'], rule_definition=r['rule_definition'],
                is_active=r['is_active'], version=r['version'],
                created_by=r['created_by'], created_at=r['created_at']
            )
            for r in rows
        ]
