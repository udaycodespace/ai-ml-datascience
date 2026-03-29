"""
DECISION-MEMORY Rationales Service
"""

from datetime import datetime
from typing import Optional
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
)

logger = structlog.get_logger(__name__)

@dataclass
class DecisionRationale:
    id: str
    decision_id: str
    team_id: str
    content_text: str
    content_format: str
    author_type: str
    confidence_score: Optional[float]
    version: int
    created_at: datetime

def record_rationale(
    decision_id: str,
    team_id: str,
    user_id: str,
    content_text: str,
    author_type: str,
    confidence_score: Optional[float] = None
) -> DecisionRationale:
    """Record a rationale for a decision (creates new version)."""
    require_team_access(user_id, team_id, Role.MEMBER)
    
    # 10k Limit Check
    if len(content_text) > 10000:
        raise ValueError("Rationale exceeds 10,000 characters")
        
    if author_type not in ('human', 'ai'):
        raise ValueError("Invalid author type")
        
    if author_type == 'ai' and confidence_score is None:
        raise ValueError("AI rationale requires confidence score")

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
            "SELECT MAX(version) as max_v FROM decision_rationales WHERE decision_id = %s", 
            (decision_id,)
        )
        res = cur.fetchone()
        if res and res['max_v']:
            version = res['max_v'] + 1

    query = """
        INSERT INTO decision_rationales (
            decision_id, team_id, content_text, content_format, 
            author_type, confidence_score, version
        ) VALUES (%s, %s, %s, 'markdown', %s, %s, %s)
        RETURNING id, decision_id, team_id, content_text, content_format, 
                  author_type, confidence_score, version, created_at
    """
    
    with transaction(IsolationLevel.READ_COMMITTED) as cur:
        cur.execute(query, (
            decision_id, team_id, content_text, 
            author_type, confidence_score, version
        ))
        row = cur.fetchone()
        return DecisionRationale(
            id=row['id'], decision_id=row['decision_id'], team_id=row['team_id'],
            content_text=row['content_text'], content_format=row['content_format'],
            author_type=row['author_type'], confidence_score=row['confidence_score'],
            version=row['version'], created_at=row['created_at']
        )

def get_rationale(decision_id: str, team_id: str, user_id: str) -> Optional[DecisionRationale]:
    """Get latest rationale."""
    require_team_access(user_id, team_id, Role.VIEWER)
    
    query = """
        SELECT id, decision_id, team_id, content_text, content_format, 
               author_type, confidence_score, version, created_at
        FROM decision_rationales
        WHERE decision_id = %s AND team_id = %s
        ORDER BY version DESC LIMIT 1
    """
    
    with get_cursor() as cur:
        cur.execute(query, (decision_id, team_id))
        row = cur.fetchone()
        if not row:
            return None
        return DecisionRationale(
            id=row['id'], decision_id=row['decision_id'], team_id=row['team_id'],
            content_text=row['content_text'], content_format=row['content_format'],
            author_type=row['author_type'], confidence_score=row['confidence_score'],
            version=row['version'], created_at=row['created_at']
        )
