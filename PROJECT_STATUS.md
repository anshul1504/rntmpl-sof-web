# RNT MPL Cricket Platform - Project Status

**Date:** 2026-06-20  
**Milestone:** Organizer MVP  
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
| High | Add focused smoke tests for tenant isolation, tournament setup, match scheduling, and scoring completion. |
| High | Add scorer correction/undo workflow for wrongly entered balls. |
| High | Improve team squad management outside tournament-specific squad registration. |
| High | Add focused smoke tests for match setup, scoring completion, corrections, fixture generation, and auction closure. |
| Medium | Add public tournament/team/player/live-score pages for fan viewing. |
| Medium | Add API parity for scoring actions if mobile/frontend clients need it. |
| Later | Production hardening, payments/Razorpay, WebSockets, notification outbox, advanced analytics. |

## Verification

- `python manage.py check`: passing.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- Full test-suite execution is intentionally not the MVP gate right now; use focused smoke checks for touched product flows.


