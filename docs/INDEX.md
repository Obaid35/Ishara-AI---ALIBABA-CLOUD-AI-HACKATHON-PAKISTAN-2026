# Documentation Index

This is the master navigation file for Ishara AI.

## Start here
- [Project Charter](PROJECT_CHARTER.md) — problem, users, boundary
- [Application Scope](APPLICATION_SCOPE.md) — scope tiers, roles, routes, what is out of scope
- [Technology Stack](TECH_STACK.md) — **frozen**; do not substitute without a measured failure
- [Project Status](PROJECT_STATUS.md) — daily truth source

## Foundation
- [Project Charter](PROJECT_CHARTER.md)
- [Product Specification](PRODUCT_SPEC.md)
- [Application Scope](APPLICATION_SCOPE.md)
- [Requirements](REQUIREMENTS.md)
- [Acceptance Criteria](ACCEPTANCE_CRITERIA.md)

## UX and design
- [User Flows](USER_FLOWS.md)
- [UI Specification](UI_SPEC.md)
- [Design System](DESIGN_SYSTEM.md)
- [Color Theme](COLOR_THEME.md)
- [Content & Urdu Guidelines](CONTENT_GUIDELINES.md)

## Recognition and data
- [Day-1 Experiment](DAY1_EXPERIMENT.md)
- [Recognition Specification](RECOGNITION_SPEC.md) — segmentation, DTW, unknown gate, thresholds
- [Data Strategy](DATA_STRATEGY.md)
- [Vocabulary Strategy](VOCABULARY_STRATEGY.md)
- [Candidate Vocabulary](CANDIDATE_VOCABULARY.md)
- [Message Map](MESSAGE_MAP.md) — sign → message → demo traceability
- [Patient Medical Message Library](MEDICAL_MESSAGE_LIBRARY.md)
- [Doctor Response Library](DOCTOR_RESPONSE_LIBRARY.md)

## Architecture and engineering
- [Technology Stack](TECH_STACK.md)
- [System Architecture](SYSTEM_ARCHITECTURE.md)
- [Application Architecture](APPLICATION_ARCHITECTURE.md)
- [Data Model](DATA_MODEL.md) — PostgreSQL schema and invariants
- [Admin Specification](ADMIN_SPEC.md) — admin console, verification workflow
- [Offline & Fallback Strategy](OFFLINE_FALLBACK.md)

## Testing and quality
- [Testing Plan](TESTING_PLAN.md)
- [QA Checklist](QA_CHECKLIST.md)
- [Risk Register](RISK_REGISTER.md)
- [Known Limitations](KNOWN_LIMITATIONS.md)

## Execution and demo
- [Six-Day Plan](SIX_DAY_PLAN.md)
- [Team Roles](TEAM_ROLES.md)
- [Decision Log](DECISIONS_LOG.md)
- [Project Status](PROJECT_STATUS.md)
- [Demo Plan](DEMO_PLAN.md)
- [Judge Q&A](JUDGE_QA.md)
- [Roadmap](ROADMAP.md)

## Ethics, permissions and references
- [Privacy, Ethics & Permissions](PRIVACY_ETHICS_PERMISSIONS.md)
- [Content Permission Request](CONTENT_PERMISSION_REQUEST.md)
- [References](REFERENCES.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## The rules that outrank everything else

> **Golden rule:** when time slips, cut the admin console, then the application shell, then vocabulary and optional UI features — never cut validation, unknown-sign handling, or final reliability rehearsal.

> **Stack rule:** the stack is frozen. Substitution requires a measured failure or a documented reason in the [Decision Log](DECISIONS_LOG.md).

> **Access rule:** the patient never needs an account.

> **Safety rule:** unknown is better than confidently wrong, and nothing is spoken without patient confirmation.
