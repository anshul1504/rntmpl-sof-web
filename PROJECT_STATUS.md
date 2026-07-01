# RNT MPL Cricket Platform - Project Status

**Date:** 2026-06-20  
**Milestone:** SaaS Launch Foundation In Progress
**Current completion:** **96%**
**Stack:** Django, Django REST Framework, Bootstrap templates  
**Verification style:** Lightweight product checks

## Current Verdict

The project has moved beyond auth-only Phase 1. The current target is an internal **Organizer MVP** where one tenant can run the core cricket workflow:

`tenant -> players -> teams -> tournament -> squads -> match schedule -> live scoring -> scorecard/points table`

## Completed / Ready

| Area | Status | Notes |
|---|---|---|
| Authentication and OTP | Ready | JWT/API auth, email OTP service, login/register templates, password reset templates. |
| Tenant onboarding | Ready | Tenant creation assigns `TENANT_ADMIN`, switches active tenant, and dashboard uses active tenant. |
| Dashboard | Ready for MVP | Shows tenant stats, upcoming matches, recent tournaments/players, tenant-aware quick actions. |
| Player registry | MVP ready | Tenant-scoped list/create/edit/detail with cricket profile fields. |
| Team management | MVP ready | Tenant-scoped list/create/edit/detail for team registry. |
| Tournament operations | MVP ready | Create tournament, register teams, add squad players, schedule matches, add officials/sponsors/awards. |
| Live scoring | MVP ready | Scorer can set batters/bowler, record runs/extras/wickets, complete innings, complete match. |
| Scorecards | MVP ready | Batting, bowling, extras, fall of wickets, commentary, and match summary render from scoring projections. |
| Points table | MVP ready | Match completion recalculates group standings through `update_points_table()`. |
| Match setup | Ready | Tournament rules, toss, playing XI, match officials, setup lock and lifecycle gates are active. |
| Scoring corrections | Ready | Last-ball undo creates an audit record and rebuilds innings projections from the delivery ledger. |
| Advanced application shell | Ready | Responsive navigation groups tournament operations, matchday, ecosystem and organization modules. |
| Venues and grounds | Ready | Tenant-scoped venues, grounds, pitches and infrastructure attributes are manageable. |
| Fixture generation | Ready | Round-robin schedules can be generated with configurable dates, slots and venue allocation. |
| Session stability | Ready | Cached database sessions survive Redis restarts; remember-me and active organization persistence are explicit. |
| Fixture rescheduling | Ready | Scheduled matches can be moved with venue/time and team/time conflict validation. |
| Player auction | MVP ready | Tournament auction, franchise purses, player lots, live bids, sold/unsold closure and squad assignment are operational. |
| Organizer security | Hardened | Role capability matrix, inactive/missing-role denial, tenant-safe API writes, and object-level tenant scoping are tested. |
| Organizer regression coverage | Ready | Squad leadership, fixture generation, setup readiness, scoring correction, result/standings, and auction closure have focused regression tests. |
| Player onboarding lifecycle | Ready | Public journey creates a guest account; payment submission, platform verification, trial eligibility, organizer invitation/evaluation, and tenant player activation are separated and tested. |
| Organizer SaaS onboarding foundation | Ready for controlled launch | Public organizer application route, commercial plan records, approval-time tenant provisioning, admin approval/rejection actions, and tenant admin assignment are implemented. |
| Organizer subscription lifecycle | Ready for controlled launch | Provisioned tenants get subscription records; platform admins can suspend/reactivate subscriptions and tenant verification follows subscription state. |
| Payment production foundation | Ready for controlled launch | Generic payment ledger, idempotent Razorpay webhook event logging, organizer payment-capture provisioning, receipts, reconciliation records, and refund audit state are implemented. |
| Notification outbox foundation | Ready for controlled launch | Durable notification outbox exists with email delivery processing through admin action or `process_notifications` management command. |
| Role workspaces | MVP ready | Focused role workspace route exists for tenant admin, scorer, team manager, auction manager, venue manager, and viewer with capability enforcement. |

## Implemented In This Organizer MVP Pass

- Tenant creation now creates/selects an admin membership and sends the organizer to dashboard.
- Tournament child actions are active-tenant bounded.
- Tournament forms validate duplicate team registrations, duplicate squad players, captain/vice-captain collision, same home/away team, and cross-tournament team selections.
- Live scoring now scopes selected batters/bowlers/fielders to registered tournament squads.
- Wides/no-balls/byes/leg-byes are supported in scorer UI and score projection.
- Ball totals now include extras correctly.
- Illegal deliveries no longer reuse a database-unique delivery slot.
- Match completion writes scores, overs, winner/loser or draw state, then updates standings.
- Innings completes automatically on the overs limit, all-out, or a successful chase.
- Tournament bowling limits are enforced and chase balls/required run rate update live.
- Mobile sidebar backdrop, desktop collapse persistence, and active organization context are available globally.
- Manual scheduling validates venue/time and team/time conflicts.
- Player registration no longer grants Player access before payment verification and organizer selection.
- Dedicated payment transactions prevent duplicate UTR use and support platform-admin verification or rejection.
- Organizer-owned trial events support invitation, scheduling, attendance, evaluation, selection, rejection, and waitlisting.
- One shared dashboard routes users to Guest, Trial Candidate, Player, Organization, or Platform modes.
- Public organizer signup at `/organizer-signup/` creates reviewed organizer applications against active organization plans.
- Default Starter, Growth and Professional organization plans are seeded by migration.
- Organizer approval provisions a tenant, assigns `TENANT_ADMIN`, copies plan limits to tenant metadata, and creates an outbox notification.
- Primary player, team, tournament and venue create paths now enforce SaaS plan limits at save time.
- Primary player/team/tournament API create paths enforce the same plan limits.
- Razorpay webhook requests are signature-verified and logged idempotently.
- Role-specific workspaces are available under `/accounts/workspaces/<workspace>/`.
- Organizer applicants can track submitted applications, pending payments, tenant provisioning, and subscription status at `/organizer-applications/`.
- Paid organizer plan payments can be marked paid from a valid Razorpay `payment.captured` webhook, then provision the organizer tenant automatically.
- Organization subscriptions are created during provisioning and can be suspended/reactivated by platform admins.
- Paid payments generate receipt records and reconciliation audit rows.
- Refund marking updates payment/reconciliation state and queues refund notifications.
- Notification delivery can be processed with `python manage.py process_notifications --limit 25`.

## Organizer MVP Walkthrough

1. Login or register from `/accounts/login/` or `/accounts/register/`.
2. Create/select a tenant from `/accounts/tenants/`.
3. Add players from `/players/add/`.
4. Create teams from `/teams/register/`.
5. Create a tournament from `/tournaments/create/`.
6. Open the tournament detail page and register at least two teams.
7. Add squad players to each registered tournament team.
8. Schedule a match from the tournament detail actions.
9. Open `/scoring/`, choose the match, and start the scoring console.
10. Select striker, non-striker, and bowler, then record deliveries.
11. Complete innings one and innings two.
12. Verify the scorecard and standings on the scorecard/tournament pages.

## Current Backlog

| Priority | Item |
|---|---|
| High | Expand API capability enforcement across every secondary team/tournament sub-entity endpoint. |
| High | Add browser-level organizer and scorer journey tests. |
| High | Add browser-level organizer/scorer/auction journey tests and fix any UI-flow regressions. |
| High | Finish organizer subscription renewal reminders, plan upgrades/downgrades, and automated settlement imports. |
| High | Add organizer invitations and sponsor/umpire/scorer/coach role workspaces. |
| Medium | Improve bulk team squad operations and transfer workflows. |
| Medium | Add public tournament/team/player/live-score pages for fan viewing. |
| Medium | Add API parity for scoring actions if mobile/frontend clients need it. |
| Later | Production hardening, Razorpay settlement/reconciliation, WebSockets, notification delivery workers, advanced analytics. |

## Verification

- `python manage.py check`: passing.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- Full test suite is the organizer-hardening gate and must remain green.


