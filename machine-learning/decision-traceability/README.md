# DECISION-MEMORY
Enterprise Decision Traceability & Responsible AI Governance Platform

## Overview
DECISION-MEMORY captures, explains, and audits human and AI-assisted decisions
for compliance, risk, and governance.

## Architecture
This service is a **domain layer only**.

It depends on **ED-BASE** for all security guarantees:
- Authentication
- Session revocation
- Authorization & team isolation
- Audit logging
- Idempotency
- Transaction integrity

ED-BASE is not bundled or reimplemented here.

## Dependency
ED-BASE (required):
https://github.com/udaycodespace/enterprise-data-trust-risk-audit

## Status
Architecture & domain implementation complete.
Infrastructure wiring (Supabase, Postgres, Redis) required to run.
