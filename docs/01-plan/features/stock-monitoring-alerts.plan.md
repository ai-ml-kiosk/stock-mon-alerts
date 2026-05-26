# stock-monitoring-alerts - Plan Document

> Version: 1.0.0 | Date: 2026-05-26 | Status: Draft
> Level: Enterprise

---

## 1. Project Overview

### 1.1 Purpose

Stock Monitoring and Alerts is a cloud-ready platform for authenticated users to manage stock watchlists, configure price alert rules, monitor quote trends, and receive notifications when target conditions are met.

The platform will begin as a clean repository with a local MVP centered on the Python engine, database schema, mock market data, REST contracts, and CI-friendly test flows. The target cloud architecture will then integrate Oracle Visual Builder Studio / Visual Builder (VBS), OCI API Gateway, Oracle Integration Cloud (OIC), and private backend services running on an Ubuntu VM.

### 1.2 Goals

- Provide authenticated dashboard access for users to manage stock watchlists and alert targets.
- Support repeatable stock price monitoring using mock market data in MVP and live providers later.
- Persist watchlists, alert targets, quote snapshots, target history, execution logs, and notification audit records from the beginning.
- Keep the Python engine private and expose public traffic only through OCI API Gateway over HTTPS.
- Use OIC as the workflow and orchestration brain for dashboard actions, alert evaluation flows, switch branches, and downstream notifications.
- Establish clear contracts between VBS, API Gateway, OIC, Python engine APIs, and database persistence.
- Clearly separate implemented MVP scope from planned cloud integration scope.

### 1.3 Non-Goals

- Real-money trading, order placement, brokerage integration, or portfolio execution.
- Financial advice, recommendations, or automated investment decisions.
- Public direct access to the Python engine or database.
- Production live-market-provider integration in the first MVP.
- Full multi-region disaster recovery in the first release.
- Guaranteed real-time tick-by-tick market data in the first release.

## 2. MVP Scope and Future Scope

### 2.1 MVP Scope

The MVP will prove the core product behavior locally and in CI without depending on external market data or full OCI service provisioning.

- Python stock monitoring engine with provider abstraction.
- Mock market data provider for local development, deterministic tests, and CI.
- Database persistence design and initial schema/migrations.
- Internal REST APIs for watchlists, alert targets, quote snapshots, alert evaluation, execution logs, and notification audit records.
- Basic alert rule evaluation for price crosses above or below configured thresholds.
- Local notification adapter that records notification intent/audit records without sending through production channels.
- API contract definitions suitable for later OIC and API Gateway integration.
- Configuration model for switching from mock provider to live provider later.
- Documentation of cloud integration responsibilities and boundaries.

### 2.2 Planned Cloud Integration Scope

The planned cloud scope will connect the MVP engine to the target Oracle architecture.

- VBS dashboard for login, watchlist management, monitoring widgets, graphs, alert toggles, threshold forms, alert history, and notification status views.
- OCI API Gateway as the public HTTPS entry point on port 443.
- API Gateway policies for authentication, authorization, request validation, routing, and token/header propagation.
- OIC integrations for dashboard-triggered actions, scheduled or event-driven alert orchestration, OIC Switch branch routing, and notification delivery.
- Live market data provider integration through the provider abstraction.
- Production notification channels such as email, SMS, Slack, and push notifications.
- Observability dashboards, operational alerts, and production runbooks.

### 2.3 Explicit Out of Scope for MVP

- Provisioning OCI API Gateway, OIC, or VBS environments.
- Production identity provider configuration.
- Live market data provider credentials and billing setup.
- Production SMS, Slack, push, or email delivery.
- End-user-facing VBS implementation.
- High availability deployment of the Ubuntu VM and database.

## 3. Functional Requirements

### 3.1 User and Access Functions

- Users can authenticate before accessing the dashboard in the target architecture.
- Dashboard requests must carry identity context through API Gateway to OIC and backend services where needed.
- Backend APIs must treat user identity as part of the request context and data ownership model.
- The MVP may use local development authentication stubs or static test identities, but APIs must be designed for authenticated operation.

### 3.2 Watchlist Functions

- Users can create, read, update, and delete watchlist entries.
- Each watchlist item includes stock symbol, display name where available, enabled status, and user ownership.
- Watchlist entries can be activated or disabled without deleting historical records.
- Invalid symbols are rejected by validation rules or marked unresolved pending provider support.

### 3.3 Alert Target Functions

- Users can create, read, update, and delete alert targets for watchlist symbols.
- Supported MVP rule types:
  - Price greater than or equal to target.
  - Price less than or equal to target.
  - Alert enabled or disabled.
- Each alert target stores threshold value, comparison operator, enabled status, notification preference, and last evaluation state.
- Future rule types may include percent change, moving average, time-window rules, volume thresholds, and composite conditions.

### 3.4 Quote Monitoring Functions

- The engine retrieves quote snapshots through a provider interface.
- MVP quote retrieval uses mock data that is deterministic and suitable for automated tests.
- Quote snapshots are persisted for auditability, charting, and alert evaluation history.
- Quote retrieval failures are logged without crashing the full monitoring cycle.

### 3.5 Alert Evaluation Functions

- The engine evaluates enabled alerts against the latest quote snapshots.
- Alert evaluations create execution log records.
- Triggered alerts create notification audit records.
- Alert state must prevent uncontrolled duplicate notifications for the same unchanged condition.
- Alert rules must be independently testable from provider and notification adapters.

### 3.6 Notification Functions

- MVP notification delivery records notification intent and status in the database.
- Planned cloud notification delivery is orchestrated by OIC.
- Notification channels may include email, SMS, Slack, and push.
- Notification audit records must include channel, recipient or destination reference, trigger reason, delivery status, and timestamps.

### 3.7 Dashboard Functions

- VBS dashboard displays watchlist configuration, current quote status, stock price graphs, monitoring widgets, alert toggles, threshold forms, alert history, and notification status.
- MVP does not implement the full VBS dashboard but must provide API contracts and data shapes that support it.

## 4. Non-Functional Requirements

### 4.1 Security

- Public access must terminate at OCI API Gateway over HTTPS on port 443.
- Python engine ports must not be publicly exposed.
- Backend APIs must require trusted internal routing or valid propagated identity/token context.
- Secrets must be provided through environment variables or secret management, never committed to source control.
- Audit records must be stored for alert evaluations and notification attempts.

### 4.2 Reliability

- Monitoring cycles should isolate failures by symbol, provider call, and notification attempt.
- Failed provider calls and failed notification attempts must be logged with enough context for replay or support.
- The MVP should be testable without external network dependencies.

### 4.3 Maintainability

- Market data providers must be implemented behind a configurable abstraction.
- Notification delivery must be implemented behind channel adapters.
- Business rules must be separated from REST transport and database persistence.
- Configuration must distinguish local MVP, CI, staging, and production modes.

### 4.4 Observability

- The system must record execution logs for quote retrieval, alert evaluation, and notification attempts.
- Logs should include correlation IDs where available from API Gateway or OIC.
- Future cloud deployment should integrate OCI logging and monitoring.

### 4.5 Performance

- MVP should handle small watchlists and alert sets suitable for validation and demos.
- Target architecture should allow batching quote retrieval and alert evaluations.
- Database indexes should support common user, symbol, alert status, and timestamp queries.

### 4.6 Compliance and Data Handling

- The platform stores user configuration and alert history, not brokerage credentials or trading authority.
- Market data provider terms must be reviewed before live integration.
- Notification destinations must be handled as user data and protected accordingly.

## 5. Four-Layer Architecture Assumptions

### 5.1 Front-End Layer: VBS Dashboard UI

Tool: Oracle Visual Builder Studio / Visual Builder.

Responsibilities:

- User login and authenticated dashboard access.
- Watchlist and stock target configuration.
- Stock price graphs and monitoring widgets.
- Alert toggle buttons and threshold forms.
- Alert history and notification status views.
- Calls public APIs through OCI API Gateway, not directly to the Python engine.

MVP distinction:

- VBS UI is planned cloud integration scope.
- MVP will define API contracts and example payloads that the dashboard can consume later.

### 5.2 Security and Proxy Layer: OCI API Gateway

Tool: OCI API Gateway.

Responsibilities:

- Public HTTPS entry point on port 443.
- Dashboard user authentication and authorization.
- Request validation and routing.
- Header/token propagation to OIC and backend services.
- No direct public exposure of backend Python engine ports.
- Centralized public API policy enforcement.

MVP distinction:

- API Gateway is planned cloud integration scope.
- MVP APIs must be designed so routes, headers, auth context, and validation rules can be mapped into API Gateway later.

### 5.3 Orchestration Layer: OIC

Tool: Oracle Integration Cloud.

Responsibilities:

- Acts as the workflow brain.
- Handles dashboard-triggered actions.
- Runs alert orchestration rules.
- Invokes quote retrieval and stock evaluation flows.
- Routes OIC Switch branches for trigger/no-trigger/error paths.
- Sends downstream notifications such as email, SMS, Slack, or push channels.
- Propagates correlation IDs and identity context to backend services.

MVP distinction:

- OIC flows are planned cloud integration scope.
- MVP will expose internal REST APIs and document orchestration assumptions so OIC can call the engine later.

### 5.4 Core Engine and Data Layer: Ubuntu VM, Python Engine, Database

Tools: Ubuntu VM running Python engine plus database.

Responsibilities:

- Runs stock monitoring and alert evaluation logic.
- Integrates with market data providers through a provider abstraction.
- Stores watchlists, alert targets, quote snapshots, target history, execution logs, and notification audit records.
- Exposes internal REST APIs for OIC/API Gateway integration.
- Keeps service ports private/internal.

MVP distinction:

- Python engine, database schema, mock provider, and internal REST APIs are implemented first.
- VM deployment and production network hardening are planned cloud integration scope.

## 6. Security and Network Boundaries

- Internet clients may access only OCI API Gateway over HTTPS on port 443.
- VBS dashboard traffic must use API Gateway routes for backend operations.
- API Gateway routes requests to OIC and approved private backend endpoints.
- OIC invokes internal Python engine APIs using private networking or controlled service connectivity.
- Python engine listens only on private interfaces/security-list-controlled ports.
- Database is accessible only from the Python engine and approved administrative paths.
- Backend services must not trust unauthenticated public headers; propagated identity must come from trusted API Gateway/OIC context.
- Provider API keys and notification credentials must be stored outside the repository.
- Local MVP may run on localhost, but route naming and request contracts should mirror the future gateway shape.

## 7. Data Persistence Scope

Database persistence is part of the target architecture and must be planned from the beginning.

### 7.1 Required Entities

- Users or external user references.
- Watchlists.
- Alert targets.
- Quote snapshots.
- Target history.
- Alert evaluation executions.
- Notification audit records.
- Provider configuration metadata.
- System configuration and job state, if needed.

### 7.2 Persistence Expectations

- Watchlists and alert targets are durable configuration records.
- Quote snapshots support graphs, trend views, and alert auditability.
- Target history records threshold and enabled/disabled changes over time.
- Execution logs track each monitoring/evaluation run.
- Notification audit records track intended and actual delivery states.
- Soft delete or disabled states should be preferred where historical traceability matters.

### 7.3 MVP Database Expectations

- Include migrations or schema initialization from the first implementation phase.
- Use deterministic seed data for local development and CI.
- Add indexes for user ID, symbol, timestamps, enabled alerts, and notification status.
- Avoid provider-specific fields in core tables unless stored in generic metadata columns.

## 8. Market Data Provider Strategy

### 8.1 MVP Provider Strategy

- Use a mock provider for local development and CI.
- Mock provider returns deterministic quote sequences for known symbols.
- Mock scenarios should cover price above threshold, below threshold, unchanged, missing symbol, provider error, and stale data.
- Tests must run without live network access or provider credentials.

### 8.2 Future Live Provider Strategy

- Add live providers through a configurable provider abstraction.
- Provider selection should be environment-based or tenant/config based.
- Provider adapters must normalize external responses into internal quote snapshot models.
- Rate limits, retries, backoff, and provider-specific errors must be handled inside provider adapters.
- Candidate providers should be evaluated for licensing, latency, rate limits, market coverage, cost, and redistribution terms.

### 8.3 Provider Interface Assumptions

- Fetch latest quote by symbol.
- Fetch latest quotes by batch where provider supports it.
- Return normalized price, currency, timestamp, provider name, and raw provider reference.
- Return explicit errors for unknown symbol, rate limit, timeout, and provider unavailable.

## 9. Alert Rule and Notification Strategy

### 9.1 MVP Alert Rules

- Alert when latest price is greater than or equal to target threshold.
- Alert when latest price is less than or equal to target threshold.
- Alert can be enabled or disabled.
- Evaluation results are persisted whether or not an alert triggers.
- Duplicate notification suppression should prevent repeated notifications while a condition remains continuously true, unless a configured re-notification policy is added.

### 9.2 Future Alert Rules

- Percent movement over a configured time window.
- Moving average crossovers.
- Volume-based alerts.
- Market open/close-aware schedules.
- Multi-condition rules.
- User-configurable cooldown intervals and escalation paths.

### 9.3 MVP Notification Strategy

- Record notification intent in the database.
- Mark local notification status as simulated, pending, sent, skipped, or failed.
- Keep notification logic behind an adapter so OIC channels can replace or augment local behavior.

### 9.4 Future Notification Strategy

- OIC routes triggered notifications to email, SMS, Slack, or push.
- OIC Switch branches handle channel selection, delivery success, delivery failure, retry, and escalation.
- Notification audit updates are written back to the backend database.

## 10. Layer Responsibilities

### 10.1 OIC Orchestration Responsibilities

- Receive dashboard-triggered workflow requests from API Gateway.
- Validate workflow-level preconditions and route to the correct integration flow.
- Invoke quote retrieval and alert evaluation APIs on the Python engine.
- Use OIC Switch branches for trigger/no-trigger/error routing.
- Coordinate downstream notification channels.
- Update notification status and audit results.
- Preserve correlation IDs across the workflow.

### 10.2 VBS Dashboard Responsibilities

- Provide authenticated user interface.
- Render watchlists, quote graphs, monitoring widgets, alert toggles, threshold forms, alert history, and notification statuses.
- Call API Gateway endpoints only.
- Display validation errors, provider status, and notification status clearly.
- Avoid embedding backend secrets or direct internal service URLs.

### 10.3 API Gateway Responsibilities

- Serve as public HTTPS entry point on port 443.
- Enforce authentication and authorization policies.
- Validate request shape, methods, and route access.
- Route dashboard operations to OIC or approved backend paths.
- Propagate identity, authorization context, and correlation headers.
- Block direct public access to internal engine ports.

### 10.4 Python Engine Responsibilities

- Own stock monitoring business logic.
- Provide internal REST APIs for OIC/API Gateway integration.
- Retrieve quotes through provider adapters.
- Evaluate alert rules.
- Persist quote snapshots, target history, execution logs, and notification audit data.
- Expose health and readiness endpoints for internal operations.
- Emit structured logs with correlation IDs.

### 10.5 Database Responsibilities

- Persist durable user configuration and operational history.
- Enforce relational integrity for users, watchlists, alert targets, quote snapshots, executions, and notifications.
- Support query patterns for dashboard views and orchestration status checks.
- Maintain migration history and seed data for local/CI environments.
- Protect credentials and sensitive data through least-privilege database access.

## 11. API and Integration Planning Assumptions

### 11.1 MVP Internal API Candidates

- `GET /health`
- `GET /watchlists`
- `POST /watchlists`
- `PATCH /watchlists/{watchlistId}`
- `DELETE /watchlists/{watchlistId}`
- `GET /alerts`
- `POST /alerts`
- `PATCH /alerts/{alertId}`
- `DELETE /alerts/{alertId}`
- `POST /quotes/refresh`
- `GET /quotes?sym={symbol}`
- `POST /alerts/evaluate`
- `GET /alerts/history`
- `GET /notifications`
- `PATCH /notifications/{notificationId}/status`

### 11.2 Contract Expectations

- APIs accept propagated user identity in a future trusted header or token context.
- APIs return consistent error envelopes.
- APIs include correlation IDs in request and response handling.
- APIs are documented before VBS/OIC integration begins.
- MVP may use local auth stubs, but contract names should anticipate API Gateway and OIC.

## 12. Success Criteria

### 12.1 MVP Success Criteria

- A clean repository contains the PDCA plan and follow-on design path.
- Python engine can run locally with mock market data.
- Database schema supports watchlists, alert targets, quotes, history, execution logs, and notification audit records.
- Alert evaluation can trigger and suppress duplicate notifications deterministically.
- Local tests/CI can run without live provider credentials or network dependency.
- REST API contracts are documented for future VBS, API Gateway, and OIC integration.
- Documentation clearly distinguishes MVP implementation from planned cloud integration.

### 12.2 Target Architecture Success Criteria

- VBS dashboard users access the platform through authenticated HTTPS routes.
- OCI API Gateway is the only public backend entry point.
- Python engine remains private/internal.
- OIC orchestrates dashboard actions, alert evaluation workflows, switch branches, and notifications.
- Live provider integration can be enabled by configuration without rewriting alert logic.
- Notification status and audit records are visible in the dashboard.

## 13. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Market data provider licensing or rate limits block production usage | High | Medium | Start with provider abstraction, evaluate terms early, support provider switching |
| MVP drifts from target OCI architecture | High | Medium | Define contracts, route shapes, identity assumptions, and cloud boundaries in design docs |
| Python engine accidentally exposed publicly | High | Low | Require API Gateway public entry only, private subnet/security rules, no public listener in deployment docs |
| OIC responsibilities overlap too much with engine logic | Medium | Medium | Keep business evaluation logic in Python; keep workflow routing and notification orchestration in OIC |
| Duplicate notifications create user noise | Medium | Medium | Persist last evaluation state and notification audit; add cooldown/re-notification policy later |
| Mock provider hides live provider edge cases | Medium | Medium | Add provider error scenarios in mock tests; create adapter contract tests before live integration |
| Database schema under-plans history/audit needs | High | Medium | Include quote snapshots, target history, execution logs, and notification audit records from MVP |
| Authentication assumptions change during VBS/API Gateway setup | Medium | Medium | Keep identity propagation abstract in MVP and document required claims/headers during design |
| Notification channels fail or partially complete | Medium | Medium | Use notification audit states, retries in OIC, and failure branch handling |
| Scope expands into trading or portfolio management | High | Medium | Maintain explicit non-goals and enforce feature backlog boundaries |

## 14. Deliverables Checklist

### 14.1 Plan Deliverables

- [x] Project overview and goals.
- [x] MVP scope and future scope.
- [x] Functional requirements.
- [x] Non-functional requirements.
- [x] Four-layer architecture assumptions.
- [x] Security and network boundaries.
- [x] Data persistence scope.
- [x] Market data provider strategy.
- [x] Alert rule and notification strategy.
- [x] OIC orchestration responsibilities.
- [x] VBS dashboard responsibilities.
- [x] API Gateway responsibilities.
- [x] Python engine responsibilities.
- [x] Database responsibilities.
- [x] Success criteria.
- [x] Risks and mitigations.
- [x] Deliverables checklist.

### 14.2 Next PDCA Deliverables

- [ ] Technical design document covering architecture, data model, API contracts, OIC flow assumptions, deployment topology, and test strategy.
- [ ] Implementation guide for local MVP build order.
- [ ] Initial repository structure and service skeleton.
- [ ] Database migrations and seed data.
- [ ] Mock provider and provider abstraction.
- [ ] Alert evaluation tests.
- [ ] API contract documentation.
- [ ] Gap analysis after implementation.
- [ ] Completion report.

## 15. Schedule

| Phase | Target Date | Status |
|-------|-------------|--------|
| Plan | 2026-05-26 | In Progress |
| Design | TBD | Pending |
| Implementation | TBD | Pending |
| Check / Analyze | TBD | Pending |
| Act / Iterate | TBD | Pending |
| Report | TBD | Pending |

## 16. References

- PDCA status: `docs/.pdca-status.json`
- Planned design path: `docs/02-design/features/stock-monitoring-alerts.design.md`
- Planned analysis path: `docs/03-analysis/stock-monitoring-alerts.analysis.md`
- Planned report path: `docs/04-report/stock-monitoring-alerts.report.md`
