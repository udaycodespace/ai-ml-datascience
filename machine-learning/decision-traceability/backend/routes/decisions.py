"""
DECISION-MEMORY API Routes
Uses ED-BASE middleware unchanged.
"""

from flask import Blueprint, request, jsonify, g
import structlog
import sys

sys.path.insert(0, '../../../backend')
from middleware import require_auth, require_team, require_admin
from services import Role

# Import Domain Services
from decision_memory.backend.services import (
    decisions, inputs, contexts, rationales, 
    actors, overrides, policies, risk
)

logger = structlog.get_logger(__name__)

# Note: The import path above assumes the decision-memory folder is capable of being imported 
# or sys.path allows it. Since we are running from within the mono-repo structure, 
# and prompt says 'Generate ONLY... inside decision-memory/', 
# we rely on the runner to have decision-memory in python path or relative imports if integrated.
# Given strict constraints, we'll use relative imports if possible or assume package structure.
# But for safety in a standalone file generation:
sys.path.append('../../../decision-memory/backend')
from services import (
    decisions, inputs, contexts, rationales, 
    actors, overrides, policies, risk
)

decisions_bp = Blueprint('decisions', __name__, url_prefix='/api/decisions')
policies_bp = Blueprint('policies', __name__, url_prefix='/api/policies')

# ================= DECISIONS =================

@decisions_bp.route('', methods=['POST'])
@require_auth
@require_team(required_role=Role.MEMBER)
def create_decision():
    """Create a new decision draft."""
    data = request.json or {}
    record = decisions.create_decision(
        team_id=g.team_id,
        user_id=g.user_id,
        title=data.get('title'),
        decision_type=data.get('decision_type'),
        idempotency_key=request.headers.get('Idempotency-Key')
    )
    return jsonify(record.__dict__), 201

@decisions_bp.route('', methods=['GET'])
@require_auth
@require_team(required_role=Role.VIEWER)
def list_decisions():
    """List decisions for team."""
    results = decisions.list_decisions(
        team_id=g.team_id,
        user_id=g.user_id,
        status=request.args.get('status'),
        limit=int(request.args.get('limit', 50)),
        offset=int(request.args.get('offset', 0))
    )
    return jsonify([r.__dict__ for r in results]), 200

@decisions_bp.route('/<decision_id>', methods=['GET'])
@require_auth
@require_team(required_role=Role.VIEWER)
def get_decision(decision_id):
    result = decisions.get_decision(decision_id, g.team_id, g.user_id)
    if not result:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(result.__dict__), 200

@decisions_bp.route('/<decision_id>/lock', methods=['POST'])
@require_auth
@require_team(required_role=Role.MEMBER)
def lock_decision(decision_id):
    """Lock decision (Finalize)."""
    result = decisions.lock_decision(decision_id, g.team_id, g.user_id)
    return jsonify(result.__dict__), 200

# ================= INPUTS =================

@decisions_bp.route('/<decision_id>/inputs', methods=['POST'])
@require_auth
@require_team(required_role=Role.MEMBER)
def attach_input(decision_id):
    data = request.json or {}
    result = inputs.attach_input(
        decision_id=decision_id,
        team_id=g.team_id,
        user_id=g.user_id,
        input_type=data.get('input_type'),
        input_data=data.get('input_data'),
        source_reference=data.get('source_reference')
    )
    return jsonify(result.__dict__), 201

@decisions_bp.route('/<decision_id>/inputs', methods=['GET'])
@require_auth
@require_team(required_role=Role.VIEWER)
def list_inputs(decision_id):
    results = inputs.list_inputs(decision_id, g.team_id, g.user_id)
    return jsonify([r.__dict__ for r in results]), 200

# ================= CONTEXT =================

@decisions_bp.route('/<decision_id>/context', methods=['POST'])
@require_auth
@require_team(required_role=Role.MEMBER)
def set_context(decision_id):
    data = request.json or {}
    result = contexts.set_context(
        decision_id=decision_id,
        team_id=g.team_id,
        user_id=g.user_id,
        constraints=data.get('constraints', []),
        assumptions=data.get('assumptions', []),
        policies_applied=data.get('policies_applied', [])
    )
    return jsonify(result.__dict__), 201

@decisions_bp.route('/<decision_id>/context', methods=['GET'])
@require_auth
@require_team(required_role=Role.VIEWER)
def get_context(decision_id):
    result = contexts.get_context(decision_id, g.team_id, g.user_id)
    if not result:
        return jsonify({}), 200
    return jsonify(result.__dict__), 200

# ================= RATIONALE =================

@decisions_bp.route('/<decision_id>/rationale', methods=['POST'])
@require_auth
@require_team(required_role=Role.MEMBER)
def record_rationale(decision_id):
    data = request.json or {}
    result = rationales.record_rationale(
        decision_id=decision_id,
        team_id=g.team_id,
        user_id=g.user_id,
        content_text=data.get('content_text'),
        author_type=data.get('author_type'),
        confidence_score=data.get('confidence_score')
    )
    return jsonify(result.__dict__), 201

@decisions_bp.route('/<decision_id>/rationale', methods=['GET'])
@require_auth
@require_team(required_role=Role.VIEWER)
def get_rationale(decision_id):
    result = rationales.get_rationale(decision_id, g.team_id, g.user_id)
    if not result:
        return jsonify({}), 200
    return jsonify(result.__dict__), 200

# ================= ACTORS =================

@decisions_bp.route('/<decision_id>/actors', methods=['POST'])
@require_auth
@require_team(required_role=Role.MEMBER)
def register_actor(decision_id):
    data = request.json or {}
    result = actors.register_actor(
        decision_id=decision_id,
        team_id=g.team_id,
        user_id=g.user_id,
        actor_type=data.get('actor_type'),
        real_user_id=data.get('real_user_id'),
        model_identifier=data.get('model_identifier'),
        prompt_text=data.get('prompt_text')
    )
    return jsonify(result.__dict__), 201

@decisions_bp.route('/<decision_id>/actors', methods=['GET'])
@require_auth
@require_team(required_role=Role.VIEWER)
def list_actors(decision_id):
    results = actors.get_actors(decision_id, g.team_id, g.user_id)
    return jsonify([r.__dict__ for r in results]), 200

# ================= OVERRIDES =================

@decisions_bp.route('/<decision_id>/overrides', methods=['POST'])
@require_auth
@require_team
def create_override(decision_id):
    # Authorization logic handled in service (requires ADMIN)
    # But route needs to pass basic team check
    data = request.json or {}
    result = overrides.create_override(
        decision_id=decision_id,
        team_id=g.team_id,
        user_id=g.user_id,
        reason=data.get('reason')
    )
    return jsonify(result.__dict__), 201

@decisions_bp.route('/<decision_id>/overrides', methods=['GET'])
@require_auth
@require_team(required_role=Role.VIEWER)
def list_overrides(decision_id):
    results = overrides.list_overrides(decision_id, g.team_id, g.user_id)
    return jsonify([r.__dict__ for r in results]), 200

# ================= RISK =================

@decisions_bp.route('/<decision_id>/risk', methods=['GET'])
@require_auth
@require_team(required_role=Role.VIEWER)
def get_risk_score(decision_id):
    # Compute on fly if not exists or cached?
    # PRD implies computed.
    # Service "compute_risk_score" stores it.
    # We might want to trigger computation on GET if missing? 
    # Or strict separation: PUT /risk -> compute, GET /risk -> retrieve.
    # Implementation plan said GET /risk.
    # Let's try get, if none, maybe compute?
    # For now, simplistic: GET returns what's stored.
    # Actually, let's expose specific compute endpoint or auto-compute.
    # I'll stick to GET returning stored score.
    
    result = risk.get_risk_score(decision_id, g.team_id, g.user_id)
    if not result:
        # Auto-compute for convenience on first read?
        # Or return empty/null.
        # Let's auto-compute to be helpful.
        try:
            result = risk.compute_risk_score(decision_id, g.team_id, g.user_id)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
            
    return jsonify(result.__dict__), 200

# ================= POLICIES =================

@policies_bp.route('', methods=['POST'])
@require_auth
@require_team(required_role=Role.ADMIN)
def create_policy():
    data = request.json or {}
    result = policies.create_policy(
        team_id=g.team_id,
        user_id=g.user_id,
        name=data.get('name'),
        rule_definition=data.get('rule_definition'),
        description=data.get('description')
    )
    return jsonify(result.__dict__), 201

@policies_bp.route('', methods=['GET'])
@require_auth
@require_team(required_role=Role.VIEWER)
def list_policies():
    results = policies.list_policies(
        team_id=g.team_id, 
        user_id=g.user_id,
        active_only=request.args.get('active_only', 'true') == 'true'
    )
    return jsonify([r.__dict__ for r in results]), 200
