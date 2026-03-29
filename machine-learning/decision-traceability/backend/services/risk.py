"""
DECISION-MEMORY Risk Service
"""

from datetime import datetime
from typing import Dict, Optional, List
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
class RiskScore:
    id: str
    decision_id: str
    team_id: str
    risk_level: str
    score_value: int
    factors: Dict
    computed_at: datetime

def compute_risk_score(
    decision_id: str,
    team_id: str,
    user_id: str
) -> RiskScore:
    """
    Compute and store risk score.
    Logic:
    - Base: 0
    - Context Incomplete: +30
    - AI Assisted: +20
    - Automated: +40
    - Override Exists: +50
    - Missing Rationale: +50
    
    Levels:
    - 0-20: LOW
    - 21-50: MEDIUM
    - 51-80: HIGH
    - 81+: CRITICAL
    """
    require_team_access(user_id, team_id, Role.MEMBER)
    
    score = 0
    factors = {}
    
    # Fetch Decision Info
    with get_cursor() as cur:
        # Decision Core
        cur.execute(
            "SELECT decision_type, context_incomplete FROM decision_records WHERE id = %s", 
            (decision_id,)
        )
        dec = cur.fetchone()
        if not dec:
            raise ValueError("Decision not found")
            
        if dec['context_incomplete']:
            score += 30
            factors['context_incomplete'] = True
            
        if dec['decision_type'] == 'ai_assisted':
            score += 20
            factors['ai_assisted'] = True
        elif dec['decision_type'] == 'automated':
            score += 40
            factors['automated'] = True

        # Overrides
        cur.execute(
            "SELECT COUNT(*) as cnt FROM decision_overrides WHERE decision_id = %s AND status = 'applied'",
            (decision_id,)
        )
        ovr = cur.fetchone()
        if ovr and ovr['cnt'] > 0:
            score += 50
            factors['has_override'] = True
            
        # Rationale
        cur.execute(
            "SELECT COUNT(*) as cnt FROM decision_rationales WHERE decision_id = %s",
            (decision_id,)
        )
        rat = cur.fetchone()
        if not rat or rat['cnt'] == 0:
            score += 50
            factors['missing_rationale'] = True

    # Cap score
    score = min(score, 100)
    
    # Determined Level
    if score <= 20:
        level = 'LOW'
    elif score <= 50:
        level = 'MEDIUM'
    elif score <= 80:
        level = 'HIGH'
    else:
        level = 'CRITICAL'
        
    query = """
        INSERT INTO decision_risk_scores (
            decision_id, team_id, risk_level, score_value, factors
        ) VALUES (%s, %s, %s, %s, %s)
        RETURNING id, decision_id, team_id, risk_level, score_value, factors, computed_at
    """
    
    with transaction(IsolationLevel.READ_COMMITTED) as cur:
        cur.execute(query, (
            decision_id, team_id, level, score, json.dumps(factors)
        ))
        row = cur.fetchone()
        return RiskScore(
            id=row['id'], decision_id=row['decision_id'], team_id=row['team_id'],
            risk_level=row['risk_level'], score_value=row['score_value'],
            factors=row['factors'], computed_at=row['computed_at']
        )

def get_risk_score(decision_id: str, team_id: str, user_id: str) -> Optional[RiskScore]:
    require_team_access(user_id, team_id, Role.VIEWER)
    query = """
        SELECT id, decision_id, team_id, risk_level, score_value, factors, computed_at
        FROM decision_risk_scores
        WHERE decision_id = %s AND team_id = %s
        ORDER BY computed_at DESC LIMIT 1
    """
    with get_cursor() as cur:
        cur.execute(query, (decision_id, team_id))
        row = cur.fetchone()
        if not row:
            return None
        return RiskScore(
            id=row['id'], decision_id=row['decision_id'], team_id=row['team_id'],
            risk_level=row['risk_level'], score_value=row['score_value'],
            factors=row['factors'], computed_at=row['computed_at']
        )
