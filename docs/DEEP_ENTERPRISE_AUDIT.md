# RNT MPL Enterprise Cricket Platform - Deep Audit

> Historical snapshot: this audit describes the repository state on June 15-16, 2026. It is retained for architectural history and is not the current delivery status. See `PROJECT_STATUS.md` for the authoritative status and completion percentage.

Audit date: 2026-06-15

## Executive Verdict (Updated 2026-06-16)

The repository has progressed from a **early domain-model scaffold** to a **secure, tenant-grounded foundation ready for Phase 1 development**.
Critical blockers (sensitive data handling, tenant isolation, broken dependencies, deployment infrastructure) have been resolved.

Estimated completion after Phase 0:

| Area | Completion | Change | Notes |
|---|---:|---|---|
| Domain modelling foundation | 25% | +5% | All references use `settings.AUTH_USER_MODEL`; `PlayerProfile` is canonical; +10 tables |
| Authentication and security | 15% | +7% | Aadhaar/PAN encrypted, OTPs hashed, `custom_js` removed, Role.code tenant-scoped, Axes deployed |
| Multi-tenant SaaS | 12% | +7% | TenantScopedManager, TenantOwnedModel base, `TenantMiddleware`, `scoped_to_user_tenants()` API filter |
| Tournament and team management | 12% | +2% | Migrations generated, indexes verified |
| Live scoring and statistics | 0% | — | Still foundation-only |
| APIs and integrations | 3% | +2% | API viewsets/RBAC in place; missing auth endpoints |
| UI/admin/public website | 1% | +1% | Admin registrations for accounts models; landing page works |
| Testing and QA | 0% | — | Zero tests still |
| DevOps and production readiness | 10% | +8% | Docker Compose, Dockerfile, Nginx config, .env.docker |
| Overall platform | **~15%** | **+9%** | **Phase 0 (secure scaffold) complete** |

## Evidence Snapshot

- 29 declared local app directories; 24 are empty.
- 24 Python files, 0 HTML templates, and 0 tests.
- No local app has a `migrations/` package.
- Concrete models currently implemented: approximately 47 across accounts,
  players, teams, and tournaments.
- `python manage.py check`: passes under the local SQLite-oriented settings.
- `python manage.py makemigrations --check --dry-run`: reports no changes because
  the apps have no migration packages; this is not evidence of migration health.
- `python manage.py test`: finds 0 tests.
- Base/production startup fails because `mysqlclient` is unavailable locally.
- Base settings initially fail if the untracked runtime `logs/` directory is
  absent.

## Critical Blockers

### P0 - Application cannot deliver a workflow

There are no views, forms, serializers, viewsets, API URLs, services, admin
registrations, templates, static frontend implementation, or tests. Most URLs
and middleware configured in settings point to modules that do not exist.

Examples include `apps.api.urls`, `apps.accounts.urls`,
`apps.publicsite.urls`, `apps.accounts.middleware`,
`apps.notifications.context_processors`, and WebSocket routing modules.

### P0 - Broken model relations

The code repeatedly references `players.Player`, but the implemented model is
`players.PlayerProfile`. Several relations reference `auth.User` despite
`AUTH_USER_MODEL = 'accounts.User'`. These relations will fail when migrations
are actually generated.

All user relations must use `settings.AUTH_USER_MODEL`. The platform must decide
whether the canonical cricket identity is named `Player` or `PlayerProfile`,
then apply that contract consistently.

### P0 - Multi-tenant isolation is not implemented

`Tenant` and `UserTenant` exist, but domain records such as players, teams,
tournaments, contracts, and matches do not consistently carry a tenant key.
There is no enforced tenant queryset manager, service boundary, permission
policy, database constraint strategy, or tested middleware.

As written, tenant data leakage is unavoidable once endpoints are added.

### P0 - Sensitive data handling is unsafe

- Aadhaar and PAN values are stored as plain text.
- OTP values are stored as plain text.
- JWT tokens are stored as plain text.
- Tenant-controlled `custom_js` creates a stored-XSS/code-execution surface.
- Documents have no malware scan, MIME validation, privacy policy, retention,
  access-control service, or signed-download strategy.

Sensitive identifiers should be encrypted at field level, displayed masked,
access-audited, and indexed only through keyed hashes where required.

### P0 - Live scoring does not exist

The central product differentiator is absent. There is no match state machine,
innings, over, delivery/event ledger, dismissal, extras, striker rotation,
undo/correction workflow, scorer locking, concurrency control, WebSocket
consumer, replay mechanism, score projection, or derived statistics pipeline.

## Architecture Findings

### Useful foundations

- Clear initial bounded-context intent through app directories.
- Common timestamp, soft-delete, status, address, and audit mixins.
- Custom user, tenant membership, role, permission matrix, login history,
  session, device, and activity-log concepts.
- Initial player skills, contracts, injuries, achievements, team squads,
  tournament stages, matches, and points-table concepts.
- Settings anticipate DRF, JWT, Channels, Celery, Redis, MySQL, SMTP, S3,
  Razorpay, WhatsApp, Firebase, and Google Maps.

### Architecture defects

- Models combine tenant-independent identities and tenant-owned operational
  records without an explicit ownership policy.
- `User.user_type` is a global single role while `UserTenant.role` is tenant
  scoped. The two authorization systems can conflict.
- `Role.code` is globally unique, preventing tenant-specific role codes.
- Generic status/soft-delete inheritance is applied broadly without defining
  lifecycle invariants or uniqueness behavior for deleted records.
- Twelve-character random IDs provide less collision margin than UUIDs and add
  custom complexity without a measured need.
- Tournament score fields are strings, unsuitable as a source of truth.
- Overs are represented as decimals; cricket overs are ball counts, not decimal
  fractions.
- Denormalized counters have no transaction-safe update strategy.
- Conditional active-contract uniqueness needs MySQL compatibility validation.
- Settings list packages that are missing from requirements, including
  `channels-redis`, `django-celery-beat`, and `hiredis`.
- Razorpay is configured but its SDK is absent; Stripe is installed despite the
  stated Razorpay requirement.
- Requirements target Django 6 rather than the stated Django 5+ baseline, and
  the current runtime is Python 3.14 rather than the stated Python 3.12 baseline.

## Capability Matrix

| Requested module | Current state |
|---|---|
| Authentication, OTP, social login, 2FA | Data/settings placeholders; no flows |
| RBAC and permission matrix | Models only; no enforcement |
| Device/session/login history | Models only; no middleware/services |
| Tenant branding/domain/billing/isolation | Models only; isolation/billing absent |
| Player ecosystem | Partial models; no identity link, UI, APIs, analytics |
| Academy management | Empty app |
| Trial management | Empty app |
| Team management | Partial models only |
| Player auction | Empty app |
| Tournament management | Partial models only; no fixture engine |
| Live scoring/match center | Empty app |
| Statistics/rankings | Empty apps; a few aggregate model placeholders |
| Points table | Storage model only; no calculation engine |
| Finance/Razorpay/GST/refunds/P&L | Empty app/config placeholders |
| Sponsorship/media/CRM/helpdesk | Empty apps |
| Notifications/documents/certificates | Empty apps |
| Reporting/BI/exports | Not implemented |
| Public website/admin control center | Not implemented |
| REST/JWT/versioning/docs/webhooks | Settings only |
| WebSockets/Celery/Redis | Settings only; routing/tasks absent |
| Docker/CI/CD/Nginx/backups/monitoring | Not implemented |
| AI features | Empty app; correctly should remain future work |

## Target System Architecture

Use a modular monolith first. It is the lowest-risk architecture for the current
team/repository maturity and can scale well beyond the expected initial load.

```text
Clients: Bootstrap web, public widgets, future mobile apps
  -> Nginx / CDN / WAF
  -> Django ASGI application
       -> REST API + HTML workflows + WebSocket consumers
       -> Domain services and tenant-aware policies
       -> MySQL primary + read replicas when required
       -> Redis cache, locks, channels, rate limits
       -> Celery workers + beat
       -> Local private media, later S3 + signed URLs
       -> External adapters: Razorpay, SMTP, SMS, WhatsApp, Firebase, Maps
  -> Observability: structured logs, metrics, traces, error tracking, audit trail
```

Mandatory architectural rules:

1. Every tenant-owned table has a non-null `tenant_id` and tenant-leading
   indexes/constraints.
2. Views call application services; business rules do not live in templates,
   signals, or serializers.
3. Scoring uses an immutable append-only delivery/event ledger with explicit
   correction events and projected read models.
4. Payments and external notifications use idempotency keys and an outbox.
5. Authorization is policy-based and object/tenant scoped.
6. Personally identifiable information and documents are encrypted/private.

## Database Design Direction

The final design should exceed 100 tables naturally, grouped by bounded context:

- Platform/accounts/tenancy/subscriptions/audit: 20-25
- Players/contracts/transfers/fitness/injuries/availability: 15-20
- Teams/academies/trials/officials/venues: 20-25
- Tournaments/registrations/fixtures/rules/points: 15-20
- Scoring/match center/statistics/rankings: 25-35
- Finance/sponsorship/CRM/helpdesk/notifications: 25-35
- Media/documents/certificates/public content: 15-20

Core scoring tables should include `match`, `match_squad`, `playing_xi`,
`match_official_assignment`, `toss`, `innings`, `over`, `delivery_event`,
`delivery_run`, `dismissal`, `fielder_involvement`, `penalty_event`,
`powerplay`, `review_event`, `partnership`, `score_correction`,
`scoring_session`, `match_result`, and projection tables.

Do not create 100 tables merely to satisfy a count. Each table needs ownership,
invariants, indexes, retention rules, and an API/workflow consumer.

## Delivery Plan

### Phase 0 - Make the scaffold trustworthy (2 sprints)

- Pin a supported Python/Django/MySQL toolchain and install all required deps.
- Repair model references and settle canonical identity names.
- Implement migrations, seed data, admin registration, and CI.
- Introduce tenant-aware base models, managers, policies, and leakage tests.
- Remove unsafe custom JavaScript; encrypt/hash sensitive fields and OTPs.
- Add Docker Compose for web, MySQL, Redis, worker, beat, and Nginx.

Exit gate: clean checks, clean migrations, reproducible startup, and meaningful
automated tests.

### Phase 1 - Tournament operations MVP (4-6 sprints)

- Authentication, tenant onboarding, memberships, invitations, RBAC.
- Player/team/venue/official CRUD and document approval.
- Tournament wizard, registrations, squads, fixture generation, rescheduling.
- Basic finance: invoices, Razorpay payment/webhook/refund ledger.
- Notification outbox and email/SMS/WhatsApp adapters.

Exit gate: one tenant can securely run registration through scheduled fixtures.

### Phase 2 - Scoring and public match center (6-8 sprints)

- Cricket laws/rules configuration and match state machine.
- Offline-tolerant scorer UI, correction workflow, concurrency locks.
- WebSocket live scores, scorecards, commentary, points/NRR calculations.
- Public tournaments, teams, players, live scores, and embeddable widgets.
- Performance/load tests focused on delivery ingestion and fan reads.

Exit gate: a tournament can be scored end-to-end with auditable corrections.

### Phase 3 - Ecosystem modules (6-10 sprints)

- Academies, trials, auctions, transfers, contracts, sponsorship, CRM/helpdesk.
- Certificates, media, reporting, exports, finance dashboards.
- Subscription plans, quotas, feature flags, custom domains, operational BI.

### Phase 4 - Scale and advanced analytics

- Read replicas, partitioning/archival, CDN, search, projection optimization.
- Heatmaps, advanced analytics, broadcast feeds, AI-assisted features.

## Test Strategy

- Unit tests for cricket laws, permissions, pricing, points, and NRR.
- Service/integration tests for tenant isolation and all state transitions.
- API contract tests and webhook replay/idempotency tests.
- WebSocket tests for authorization, ordering, reconnect, and fan-out.
- Property-based tests for scoring invariants.
- End-to-end browser tests for organizer, scorer, player, and fan journeys.
- Load tests for concurrent scoring and public live-score traffic.
- Security tests for IDOR, cross-tenant access, file uploads, XSS, CSRF, rate
  limits, OTP abuse, and payment webhook forgery.
- Migration and backup-restore tests in CI/staging.

Initial quality gates: no untested tenant policy, no untested scoring transition,
and no release with failing migration checks.

## Production Security Checklist

- No default/fallback secret keys; secret manager-backed credentials.
- Private media by default with signed, expiring downloads.
- Field encryption and masking for Aadhaar/PAN and sensitive documents.
- Hashed OTPs/tokens, short expiry, attempt limits, and replay protection.
- Tenant scope enforced in queries, services, WebSockets, tasks, and exports.
- Object-level RBAC with deny-by-default policies.
- Strict CSP, no tenant-supplied executable JavaScript, secure headers.
- File type/size validation, malware scanning, and quarantine.
- Idempotent signed webhooks with timestamp/replay validation.
- Audit trails protected from application-user modification.
- Dependency/SAST/secret/container scans in CI.
- Automated encrypted backups plus tested restoration and retention.
- Centralized logging, metrics, alerting, queue monitoring, and error tracking.
- Incident response, privacy/consent, deletion, and data-retention procedures.

## SaaS Plan Direction

| Plan | Target | Suggested limits/features |
|---|---|---|
| Community | Small organizers | 1 active tournament, basic scoring/public pages |
| Professional | Leagues/academies | More tournaments, payments, exports, branding |
| Business | Associations/franchises | Multi-admin, CRM, advanced reports, custom domain |
| Enterprise | State/corporate operations | SSO, SLA, dedicated support, advanced security/BI |

Billing must attach to tenants, not individual users. Entitlements and quotas
must be centralized and checked server-side.

## Immediate Backlog

1. Repair startup/dependency/toolchain issues.
2. Fix all broken model references and generate initial migrations.
3. Redesign and enforce tenant ownership before adding endpoints.
4. Implement security baseline for sensitive fields, documents, OTPs, and RBAC.
5. Build authenticated tenant onboarding and core CRUD vertical slice.
6. Design the scoring event model before implementing tournament score fields.
7. Add CI, Docker Compose, tests, and operational documentation.

The correct next milestone is **a secure, tenant-isolated tournament operations
MVP**, not simultaneous implementation of every listed module.
