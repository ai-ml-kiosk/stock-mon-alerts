# stock-monitoring-alerts - Design Document

> Version: 1.0.0 | Date: 2026-05-26 | Status: Draft
> Level: Enterprise | Plan: `docs/01-plan/features/stock-monitoring-alerts.plan.md`

---

## 1. Overview

### 1.1 Purpose

This document defines the High-Level Design (HLD) and Low-Level Design (LLD) for the Stock Monitoring and Alerts platform.

The design follows the approved PDCA plan and preserves the required target flow:

```text
VBS Dashboard
  -> OCI API Gateway over HTTPS :443
  -> OIC orchestration
  -> Python Engine on Ubuntu VM over private/internal HTTP
  -> Database
  -> Market Data Provider
  -> OIC notification flow
```

### 1.2 Design Goals

- Make OCI API Gateway the only public HTTPS boundary.
- Keep the Python engine private and inaccessible from the public internet.
- Use OIC as the orchestration brain for workflow routing and downstream notification handling.
- Use VBS as the user-facing dashboard only.
- Store monitoring history and audit records from the beginning.
- Default local development and CI to mock market data.
- Decouple live market providers through environment-driven configuration.
- Prevent secrets, credentials, provider keys, and OCI private material from entering source control.

### 1.3 MVP Versus Planned Cloud Integration

| Area | MVP Implementation | Planned Cloud Integration |
|------|--------------------|---------------------------|
| Dashboard | API contracts and sample payloads | VBS screens, auth, data binding, charts |
| Public entry | Local development server only | OCI API Gateway HTTPS :443 |
| Orchestration | Direct local API calls or smoke scripts | OIC integration flows and switch branches |
| Engine | Python REST service with mock provider | Private Ubuntu VM service called by OIC |
| Database | Local/dev database with migrations | Managed or VM-hosted database with backups |
| Market data | Mock provider by default | Live provider adapter selected by config |
| Notifications | Simulated audit records | OIC email/SMS/Slack/push delivery |

---

# Part 1: HLD

## 2. Four-Layer Architecture

### 2.1 Layers

| Layer | Tool | Primary Responsibility | Public Exposure |
|-------|------|------------------------|-----------------|
| Front-end | Oracle Visual Builder Studio / Visual Builder | Authenticated dashboard experience | Browser-facing only through VBS app |
| Security and proxy | OCI API Gateway | HTTPS boundary, auth, validation, routing, header propagation | Public HTTPS :443 |
| Orchestration | Oracle Integration Cloud | Workflow brain, switch branching, notification routing | Not directly public; reached through gateway |
| Core engine and data | Ubuntu VM, Python engine, database | Quote retrieval, alert evaluation, persistence, audit | Private/internal only |

### 2.2 Architecture Diagram

```text
                       Public Internet
                             |
                             | HTTPS :443
                             v
+-------------------+   +---------------------+   +----------------------+
| VBS Dashboard UI  |-->| OCI API Gateway     |-->| OIC Integration      |
| User-facing app   |   | Auth/proxy boundary |   | Workflow brain       |
+-------------------+   +---------------------+   +----------+-----------+
                                                            |
                                                            | Private/internal HTTP
                                                            v
                                                 +----------+-----------+
                                                 | Python Engine        |
                                                 | Ubuntu VM            |
                                                 +-----+----------+-----+
                                                       |          |
                                        SQL/private    |          | HTTPS egress
                                                       v          v
                                             +---------+--+   +---+----------------+
                                             | Database   |   | Market Data        |
                                             | History    |   | Provider           |
                                             | Audit      |   | Mock or Live       |
                                             +------------+   +--------------------+
                                                            |
                                                            | Notification results
                                                            v
                                                 +----------+-----------+
                                                 | OIC Notification     |
                                                 | Email/SMS/Slack/Push |
                                                 +----------------------+
```

## 3. System Context

### 3.1 Actors and External Systems

| Actor/System | Description |
|--------------|-------------|
| Dashboard user | Authenticated user who manages watchlists and alert thresholds |
| VBS dashboard | User-facing UI for watchlists, charts, toggles, thresholds, history |
| OCI API Gateway | Public HTTPS boundary and policy enforcement point |
| Identity provider | Authentication authority integrated with API Gateway/VBS |
| OIC | Orchestrates dashboard actions, evaluation flows, switches, notifications |
| Python engine | Owns monitoring logic, quote provider abstraction, persistence APIs |
| Database | Stores durable configuration, quote history, execution logs, audit records |
| Market data provider | Mock provider in MVP; live external provider later |
| Notification channels | Email, SMS, Slack, push, or simulated MVP audit sink |

### 3.2 Context Responsibilities

- Users never access engine endpoints directly.
- VBS never stores secrets or internal backend URLs.
- API Gateway validates public requests and propagates trusted identity context.
- OIC owns workflow sequencing and notification branching.
- Python owns domain decisions: provider normalization, alert evaluation, persistence state transitions.
- Database is the source of truth for configuration, monitoring history, and audit data.

## 4. Major Components

### 4.1 VBS Dashboard

- Login and dashboard shell.
- Watchlist table and symbol add/edit/remove actions.
- Alert target editor with operator, threshold, enabled state, cooldown display, and channel preference.
- Quote graph and monitoring widgets.
- Alert history table.
- Notification status table.
- API Gateway service connection definitions.

### 4.2 OCI API Gateway

- Public route definitions under `/api/v1`.
- HTTPS/TLS enforcement.
- Authentication and authorization policy.
- Request validation and payload size controls.
- Header propagation to OIC:
  - `X-Correlation-Id`
  - `X-Authenticated-User-Id`
  - `X-Authenticated-User-Email`
  - `X-Auth-Scopes`
- Backend route mapping to OIC integration endpoints.

### 4.3 OIC Integrations

- Dashboard command flow.
- Watchlist management flow.
- Quote refresh flow.
- Alert evaluation flow.
- Notification dispatch flow.
- Notification status update flow.
- Error handling and dead-letter/audit branch.

### 4.4 Python Engine

- REST API layer.
- Authentication context adapter for trusted headers.
- Watchlist service.
- Alert target service.
- Quote service.
- Provider adapter registry.
- Alert evaluation service.
- Notification audit service.
- Execution logging service.
- Database repositories.
- Health/readiness endpoints.

### 4.5 Database

- Relational schema for user references, watchlists, alert targets, snapshots, history, executions, and notifications.
- Migration history.
- Seed data for local development.
- Indexes for dashboard and orchestration query patterns.
- Optional JSON metadata columns for provider and notification extensions.

## 5. Public and Private Network Boundaries

### 5.1 Public Boundary

- Public ingress is only OCI API Gateway over HTTPS on port 443.
- VBS dashboard calls only API Gateway public routes.
- API Gateway denies direct routing to Python engine public IPs because no such public route should exist.

### 5.2 Private Boundary

- OIC reaches Python engine through private/internal HTTP connectivity.
- Python engine listens on an internal interface or private subnet address only.
- Database accepts connections only from the Python engine and approved administration paths.
- Python engine may make controlled outbound HTTPS calls to live market providers.

### 5.3 Local MVP Boundary

- Local development may run the Python engine on `127.0.0.1`.
- Local smoke tests may call engine endpoints directly.
- Route names, headers, and payloads must mirror the future API Gateway/OIC path.

## 6. End-to-End Flows

### 6.1 VBS Dashboard Flow

```text
User opens VBS dashboard
  -> User authenticates
  -> VBS loads watchlists through API Gateway
  -> User edits watchlist or alert target
  -> VBS sends command to API Gateway
  -> API Gateway validates and forwards to OIC
  -> OIC invokes Python engine private API
  -> Python engine persists update and returns result
  -> OIC maps response
  -> API Gateway returns response
  -> VBS refreshes dashboard data bindings
```

### 6.2 OCI API Gateway Auth and Proxy Flow

```text
HTTPS request arrives at API Gateway
  -> TLS termination
  -> Authentication policy validates token/session
  -> Authorization policy checks scope/role
  -> Request schema validation
  -> Correlation ID generated or propagated
  -> Identity headers are set from trusted claims
  -> Route maps request to OIC integration endpoint
  -> Gateway returns OIC response to VBS
```

### 6.3 OIC Orchestration Flow

```text
OIC receives gateway request
  -> Validate required identity/correlation headers
  -> Normalize request envelope
  -> Invoke Python engine private endpoint
  -> Switch branch on engine result
     -> success: map response to dashboard payload
     -> alert_triggered: call notification dispatch flow
     -> validation_error: return 400-style response
     -> provider_error: audit and return degraded result
     -> system_error: audit and return 500-style response
  -> Update notification audit where needed
  -> Return normalized response to API Gateway
```

### 6.4 Alert Evaluation Flow

```text
Scheduled or dashboard-triggered evaluation
  -> OIC starts alert evaluation integration
  -> OIC calls Python /internal/v1/alerts/evaluate
  -> Engine loads enabled alert targets
  -> Engine fetches latest quotes through configured provider
  -> Engine persists quote snapshots
  -> Engine evaluates thresholds and duplicate suppression
  -> Engine writes execution logs
  -> Engine creates notification audit rows for triggered alerts
  -> OIC Switch routes triggered notification rows to channel flows
  -> OIC updates notification audit status
```

## 7. Python Engine and Database Responsibilities

### 7.1 Python Engine Responsibilities

- Validate engine-level payloads and user context.
- Keep user data scoped to propagated identity.
- Normalize market data provider responses.
- Evaluate alert conditions deterministically.
- Prevent uncontrolled duplicate notification creation.
- Persist every material state change and execution outcome.
- Expose internal REST APIs for OIC/API Gateway integration.
- Emit structured logs and correlation IDs.

### 7.2 Database Responsibilities

- Store durable user watchlist and alert configuration.
- Store quote snapshots for monitoring history and graphs.
- Store target history for audit and change tracking.
- Store execution logs for operational review.
- Store notification audit rows for OIC delivery status.
- Enforce foreign keys and integrity where practical.
- Support retention and archival policies.

## 8. Market Data Provider Integration

### 8.1 Provider Abstraction

The engine uses a provider interface so the alert logic never depends on a provider-specific response model.

```text
MarketDataProvider
  -> get_quote(symbol)
  -> get_quotes(symbols)
  -> health()
```

### 8.2 Provider Selection

| Environment | Default Provider | Configuration |
|-------------|------------------|---------------|
| local | mock | `MARKET_DATA_PROVIDER=mock` |
| ci | mock | deterministic test fixtures |
| staging | mock or live sandbox | environment variable |
| production | live provider | secret-backed provider credentials |

### 8.3 Live Provider Concerns

- API keys come from environment/secret manager, never source code.
- Rate limiting and retries are adapter responsibilities.
- Provider errors map into normalized engine error codes.
- Raw provider metadata may be stored in a JSON metadata field for audit.

## 9. Notification Architecture

### 9.1 MVP Notification Model

- Engine creates notification audit records with `simulated` or `pending` status.
- Local smoke tests inspect audit rows instead of sending real messages.
- Notification adapter remains replaceable.

### 9.2 Cloud Notification Model

```text
Python creates notification audit row
  -> OIC receives triggered notification list
  -> OIC Switch chooses channel branch
     -> email
     -> sms
     -> slack
     -> push
     -> unsupported_channel
  -> OIC calls downstream connector/service
  -> OIC calls engine to update notification audit status
```

### 9.3 Notification Statuses

- `pending`
- `simulated`
- `sent`
- `skipped`
- `failed`
- `retry_scheduled`

## 10. Security Model

### 10.1 Authentication

- User authentication is handled at VBS/API Gateway using the configured identity provider.
- API Gateway derives trusted user headers from validated identity claims.
- Python engine trusts identity headers only from private OIC/API Gateway network paths.
- Local MVP uses configured test identity headers for smoke tests.

### 10.2 Authorization

- API Gateway enforces route-level authorization.
- OIC validates workflow-level requirements.
- Python enforces data ownership on every user-scoped query.
- Admin/internal endpoints are separated from dashboard-facing endpoints.

### 10.3 Secret Management

- `.env` and `.env.*` are ignored by Git.
- `.env.example` may be committed with non-secret placeholders.
- Live provider credentials are stored in environment variables or secret management.
- OCI keys, wallets, certificates, and Terraform variable files are not committed.

### 10.4 Data Protection

- HTTPS is required at the public boundary.
- Private network paths are restricted by subnet/security-list rules.
- Database credentials use least privilege.
- Audit logs avoid storing secrets, raw tokens, or sensitive notification message bodies.

## 11. Operations Model

### 11.1 Logging

- All layers propagate `X-Correlation-Id`.
- Python logs structured JSON in staging/production.
- OIC flow instances retain correlation IDs and engine execution IDs.
- Provider errors and notification failures are logged with normalized error codes.

### 11.2 Metrics

Minimum target metrics:

- Quote refresh duration.
- Provider call success/failure count.
- Alert evaluation count.
- Triggered alert count.
- Notification status count by channel.
- API error count by route and status code.
- Database operation failures.

### 11.3 Health Checks

- Python `/health` confirms process liveness.
- Python `/ready` confirms database connectivity and provider configuration readiness.
- OIC integrations should expose operational status through OIC monitoring.
- API Gateway route health is verified with smoke calls.

### 11.4 Backup and Retention

- Database backups are required before production launch.
- Quote snapshots may have retention by age or aggregation level.
- Audit records should retain enough history for support and compliance review.

## 12. Deployment View

### 12.1 MVP Deployment

```text
Developer workstation / CI
  -> Python engine
  -> Local database
  -> Mock provider fixtures
  -> Simulated notification audit
```

### 12.2 Target Cloud Deployment

```text
VBS hosted dashboard
  -> OCI API Gateway public endpoint HTTPS :443
  -> OIC integration instance
  -> Private Ubuntu VM running Python engine
  -> Private database
  -> External market data provider over controlled outbound HTTPS
  -> OIC notification connectors
```

### 12.3 Deployment Controls

- Environment-specific configuration.
- No secrets in repository.
- Database migrations run before engine deployment.
- Smoke tests verify health, watchlist CRUD, alert evaluation, and notification audit update.

---

# Part 2: LLD

## 13. API Design

### 13.1 API Conventions

- Public API prefix: `/api/v1`
- Internal engine prefix: `/internal/v1`
- JSON only for request and response bodies.
- All timestamps use ISO 8601 UTC.
- All money/price values use decimal strings in API payloads to avoid float drift.
- All requests include or receive a correlation ID.

### 13.2 Common Headers

| Header | Direction | Required | Description |
|--------|-----------|----------|-------------|
| `Authorization` | VBS to Gateway | Yes in cloud | Bearer/session token validated by gateway |
| `X-Correlation-Id` | All layers | Recommended | Generated if absent |
| `X-Authenticated-User-Id` | Gateway/OIC to engine | Yes for user APIs | Trusted user reference |
| `X-Authenticated-User-Email` | Gateway/OIC to engine | Optional | User email for display/audit |
| `X-Auth-Scopes` | Gateway/OIC to engine | Optional | Route authorization scopes |

### 13.3 Common Response Envelope

```json
{
  "data": {},
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

### 13.4 Common Error Envelope

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more fields are invalid.",
    "details": [
      {
        "field": "symbol",
        "reason": "Symbol is required."
      }
    ]
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

## 14. REST Endpoint Specs

### 14.1 Health

#### `GET /internal/v1/health`

Returns process liveness.

Response:

```json
{
  "data": {
    "status": "ok",
    "service": "stock-monitoring-engine"
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

#### `GET /internal/v1/ready`

Returns dependency readiness.

Response:

```json
{
  "data": {
    "status": "ready",
    "database": "ok",
    "marketDataProvider": "mock"
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

### 14.2 Watchlists

#### `GET /api/v1/watchlists`

Gateway route to OIC, then engine `GET /internal/v1/watchlists`.

Response:

```json
{
  "data": {
    "items": [
      {
        "watchlistId": "wl_001",
        "symbol": "ORCL",
        "displayName": "Oracle Corporation",
        "enabled": true,
        "createdAt": "2026-05-26T09:00:00Z",
        "updatedAt": "2026-05-26T09:00:00Z"
      }
    ]
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

#### `POST /api/v1/watchlists`

Request:

```json
{
  "symbol": "ORCL",
  "displayName": "Oracle Corporation",
  "enabled": true
}
```

Response:

```json
{
  "data": {
    "watchlistId": "wl_001",
    "symbol": "ORCL",
    "displayName": "Oracle Corporation",
    "enabled": true,
    "createdAt": "2026-05-26T09:00:00Z",
    "updatedAt": "2026-05-26T09:00:00Z"
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

#### `PATCH /api/v1/watchlists/{watchlistId}`

Request:

```json
{
  "displayName": "Oracle",
  "enabled": false
}
```

#### `DELETE /api/v1/watchlists/{watchlistId}`

Soft-deletes or disables the watchlist row while preserving history.

Response:

```json
{
  "data": {
    "watchlistId": "wl_001",
    "deleted": true
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

### 14.3 Alert Targets

#### `GET /api/v1/alerts`

Response:

```json
{
  "data": {
    "items": [
      {
        "alertId": "al_001",
        "watchlistId": "wl_001",
        "symbol": "ORCL",
        "ruleType": "price_threshold",
        "operator": "gte",
        "threshold": "140.00",
        "currency": "USD",
        "enabled": true,
        "notificationChannel": "email",
        "lastEvaluationState": "not_triggered",
        "createdAt": "2026-05-26T09:00:00Z",
        "updatedAt": "2026-05-26T09:00:00Z"
      }
    ]
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

#### `POST /api/v1/alerts`

Request:

```json
{
  "watchlistId": "wl_001",
  "ruleType": "price_threshold",
  "operator": "gte",
  "threshold": "140.00",
  "currency": "USD",
  "enabled": true,
  "notificationChannel": "email"
}
```

Response:

```json
{
  "data": {
    "alertId": "al_001",
    "watchlistId": "wl_001",
    "ruleType": "price_threshold",
    "operator": "gte",
    "threshold": "140.00",
    "currency": "USD",
    "enabled": true,
    "notificationChannel": "email"
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

#### `PATCH /api/v1/alerts/{alertId}`

Request:

```json
{
  "threshold": "145.00",
  "enabled": true,
  "notificationChannel": "slack"
}
```

#### `DELETE /api/v1/alerts/{alertId}`

Soft-deletes or disables the alert target.

### 14.4 Quotes

#### `POST /api/v1/quotes/refresh`

Dashboard-triggered quote refresh. OIC calls engine `POST /internal/v1/quotes/refresh`.

Request:

```json
{
  "symbols": ["ORCL", "AAPL"]
}
```

Response:

```json
{
  "data": {
    "provider": "mock",
    "quotes": [
      {
        "quoteSnapshotId": "qs_001",
        "symbol": "ORCL",
        "price": "139.42",
        "currency": "USD",
        "quoteTime": "2026-05-26T09:00:00Z",
        "provider": "mock"
      }
    ],
    "errors": []
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

#### `GET /api/v1/quotes?symbol=ORCL&limit=100`

Returns persisted quote snapshots for charting.

### 14.5 Alert Evaluation

#### `POST /api/v1/alerts/evaluate`

Dashboard or schedule-triggered evaluation. OIC calls engine `POST /internal/v1/alerts/evaluate`.

Request:

```json
{
  "symbols": ["ORCL"],
  "dryRun": false,
  "triggerSource": "dashboard"
}
```

Response:

```json
{
  "data": {
    "executionId": "ex_001",
    "provider": "mock",
    "evaluatedCount": 2,
    "triggeredCount": 1,
    "notifications": [
      {
        "notificationAuditId": "nt_001",
        "alertId": "al_001",
        "symbol": "ORCL",
        "channel": "email",
        "status": "pending",
        "reason": "price 141.10 gte threshold 140.00"
      }
    ],
    "errors": []
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:00:00Z"
  }
}
```

#### `GET /api/v1/alerts/history?symbol=ORCL&limit=50`

Returns evaluation and target history records.

### 14.6 Notifications

#### `GET /api/v1/notifications?status=pending&limit=50`

Returns notification audit records.

#### `PATCH /internal/v1/notifications/{notificationAuditId}/status`

Used by OIC after channel dispatch.

Request:

```json
{
  "status": "sent",
  "providerMessageId": "email-123",
  "failureReason": null,
  "deliveredAt": "2026-05-26T09:01:00Z"
}
```

Response:

```json
{
  "data": {
    "notificationAuditId": "nt_001",
    "status": "sent",
    "updatedAt": "2026-05-26T09:01:00Z"
  },
  "meta": {
    "correlationId": "corr-123",
    "timestamp": "2026-05-26T09:01:00Z"
  }
}
```

## 15. Data Model Placeholders

### 15.1 Naming and Type Assumptions

- IDs are string IDs in API payloads and UUID-compatible values in storage.
- Timestamps are UTC.
- Prices are stored as decimal/numeric, never binary floating point.
- Soft delete uses `deleted_at` where historical audit matters.

### 15.2 Users or External User References

```sql
CREATE TABLE users (
  user_id VARCHAR(128) PRIMARY KEY,
  email VARCHAR(320),
  display_name VARCHAR(255),
  external_subject VARCHAR(255),
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

### 15.3 Watchlist Model

```sql
CREATE TABLE watchlists (
  watchlist_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL REFERENCES users(user_id),
  symbol VARCHAR(16) NOT NULL,
  display_name VARCHAR(255),
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  deleted_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  UNIQUE (user_id, symbol)
);

CREATE INDEX idx_watchlists_user_enabled
  ON watchlists(user_id, enabled);
```

### 15.4 Alert Rule Model

```sql
CREATE TABLE alert_targets (
  alert_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL REFERENCES users(user_id),
  watchlist_id VARCHAR(64) NOT NULL REFERENCES watchlists(watchlist_id),
  rule_type VARCHAR(64) NOT NULL,
  operator VARCHAR(16) NOT NULL,
  threshold NUMERIC(18, 6) NOT NULL,
  currency VARCHAR(8) NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  notification_channel VARCHAR(32) NOT NULL,
  last_evaluation_state VARCHAR(32) NOT NULL DEFAULT 'unknown',
  last_triggered_at TIMESTAMP NULL,
  cooldown_seconds INTEGER NULL,
  metadata_json TEXT NULL,
  deleted_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_alert_targets_user_enabled
  ON alert_targets(user_id, enabled);

CREATE INDEX idx_alert_targets_watchlist
  ON alert_targets(watchlist_id);
```

Allowed `rule_type` values:

- `price_threshold`

Allowed `operator` values:

- `gte`
- `lte`

Allowed `last_evaluation_state` values:

- `unknown`
- `not_triggered`
- `triggered`
- `suppressed_duplicate`
- `error`

### 15.5 Quote Snapshot Model

```sql
CREATE TABLE quote_snapshots (
  quote_snapshot_id VARCHAR(64) PRIMARY KEY,
  symbol VARCHAR(16) NOT NULL,
  price NUMERIC(18, 6) NOT NULL,
  currency VARCHAR(8) NOT NULL,
  quote_time TIMESTAMP NOT NULL,
  provider VARCHAR(64) NOT NULL,
  provider_reference VARCHAR(255),
  raw_metadata_json TEXT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_quote_snapshots_symbol_time
  ON quote_snapshots(symbol, quote_time DESC);
```

### 15.6 Target History Model

```sql
CREATE TABLE target_history (
  target_history_id VARCHAR(64) PRIMARY KEY,
  alert_id VARCHAR(64) NOT NULL REFERENCES alert_targets(alert_id),
  user_id VARCHAR(128) NOT NULL REFERENCES users(user_id),
  change_type VARCHAR(32) NOT NULL,
  previous_value_json TEXT NULL,
  new_value_json TEXT NOT NULL,
  changed_by VARCHAR(128) NOT NULL,
  changed_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_target_history_alert_time
  ON target_history(alert_id, changed_at DESC);
```

Allowed `change_type` values:

- `created`
- `threshold_updated`
- `enabled`
- `disabled`
- `channel_updated`
- `deleted`

### 15.7 Execution Log Model

```sql
CREATE TABLE execution_logs (
  execution_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(128),
  trigger_source VARCHAR(32) NOT NULL,
  provider VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  evaluated_count INTEGER NOT NULL DEFAULT 0,
  triggered_count INTEGER NOT NULL DEFAULT 0,
  error_count INTEGER NOT NULL DEFAULT 0,
  correlation_id VARCHAR(128),
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP NULL,
  details_json TEXT NULL
);

CREATE INDEX idx_execution_logs_time
  ON execution_logs(started_at DESC);
```

### 15.8 Notification Audit Model

```sql
CREATE TABLE notification_audit (
  notification_audit_id VARCHAR(64) PRIMARY KEY,
  execution_id VARCHAR(64) REFERENCES execution_logs(execution_id),
  alert_id VARCHAR(64) NOT NULL REFERENCES alert_targets(alert_id),
  user_id VARCHAR(128) NOT NULL REFERENCES users(user_id),
  symbol VARCHAR(16) NOT NULL,
  channel VARCHAR(32) NOT NULL,
  destination_ref VARCHAR(255),
  status VARCHAR(32) NOT NULL,
  reason TEXT NOT NULL,
  provider_message_id VARCHAR(255),
  failure_reason TEXT,
  created_at TIMESTAMP NOT NULL,
  sent_at TIMESTAMP NULL,
  delivered_at TIMESTAMP NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_notification_audit_user_status
  ON notification_audit(user_id, status);

CREATE INDEX idx_notification_audit_created
  ON notification_audit(created_at DESC);
```

Allowed `status` values:

- `pending`
- `simulated`
- `sent`
- `skipped`
- `failed`
- `retry_scheduled`

## 16. Mapping Logic

### 16.1 Gateway to OIC Mapping

| Public Route | OIC Integration | Notes |
|--------------|-----------------|-------|
| `GET /api/v1/watchlists` | `StockDashboardWatchlistFlow` | Query user watchlist |
| `POST /api/v1/watchlists` | `StockDashboardWatchlistFlow` | Create symbol entry |
| `PATCH /api/v1/watchlists/{id}` | `StockDashboardWatchlistFlow` | Update enabled/display name |
| `DELETE /api/v1/watchlists/{id}` | `StockDashboardWatchlistFlow` | Soft delete |
| `GET /api/v1/alerts` | `StockDashboardAlertFlow` | Query alert targets |
| `POST /api/v1/alerts` | `StockDashboardAlertFlow` | Create alert target |
| `PATCH /api/v1/alerts/{id}` | `StockDashboardAlertFlow` | Update target |
| `POST /api/v1/quotes/refresh` | `StockQuoteRefreshFlow` | Refresh quotes |
| `POST /api/v1/alerts/evaluate` | `StockAlertEvaluationFlow` | Evaluate alerts |
| `GET /api/v1/notifications` | `StockNotificationStatusFlow` | Query notification audit |

### 16.2 OIC to Engine Mapping

| OIC Action | Engine Endpoint | Mapping |
|------------|-----------------|---------|
| List watchlists | `GET /internal/v1/watchlists` | Pass user headers |
| Create watchlist | `POST /internal/v1/watchlists` | Normalize symbol uppercase |
| Update alert | `PATCH /internal/v1/alerts/{id}` | Preserve ID path param |
| Refresh quotes | `POST /internal/v1/quotes/refresh` | Pass symbols array |
| Evaluate alerts | `POST /internal/v1/alerts/evaluate` | Include trigger source |
| Update notification | `PATCH /internal/v1/notifications/{id}/status` | Send channel result |

### 16.3 Provider Mapping

Provider responses map to:

- `symbol`
- `price`
- `currency`
- `quote_time`
- `provider`
- `provider_reference`
- `raw_metadata_json`

Provider-specific fields stay out of the core alert evaluation logic.

## 17. Validation Rules

### 17.1 Symbol Validation

- Required.
- Trim whitespace.
- Convert to uppercase.
- Length 1 to 16.
- Allowed characters: uppercase letters, numbers, `.`, `-`.
- MVP mock provider may reject unknown fixtures with `SYMBOL_NOT_FOUND`.

### 17.2 Price and Threshold Validation

- Required for threshold alerts.
- Decimal string in API payload.
- Greater than zero.
- Maximum precision: 6 decimal places.
- Currency required, uppercase ISO-style code, length 3 to 8.

### 17.3 Alert Validation

- `ruleType` must be `price_threshold` for MVP.
- `operator` must be `gte` or `lte`.
- `notificationChannel` must be one of:
  - `email`
  - `sms`
  - `slack`
  - `push`
  - `simulated`
- Disabled watchlist items cannot create enabled alerts unless explicitly re-enabled.

### 17.4 Identity Validation

- User-scoped APIs require `X-Authenticated-User-Id` after gateway/OIC.
- Local MVP may use `LOCAL_DEV_USER_ID`.
- Engine returns `UNAUTHENTICATED` if user context is absent for user routes.

## 18. Error Handling Rules

### 18.1 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHENTICATED` | 401 | Missing or invalid identity context |
| `FORBIDDEN` | 403 | Authenticated user lacks permission |
| `NOT_FOUND` | 404 | Resource not found or not owned by user |
| `VALIDATION_ERROR` | 400 | Invalid payload or route parameter |
| `SYMBOL_NOT_FOUND` | 422 | Provider cannot resolve symbol |
| `PROVIDER_RATE_LIMITED` | 429 | Live provider rate limit reached |
| `PROVIDER_UNAVAILABLE` | 503 | Provider timeout or outage |
| `DUPLICATE_RESOURCE` | 409 | Duplicate watchlist/alert conflict |
| `SYSTEM_ERROR` | 500 | Unexpected engine failure |

### 18.2 Layer Error Behavior

- API Gateway rejects invalid auth and malformed public requests before OIC.
- OIC maps engine errors into dashboard-friendly envelopes.
- Python engine logs full internal context but returns safe error messages.
- Provider failures do not abort an entire batch if other symbols can be evaluated.
- Notification failures update audit status and may schedule retry through OIC.

## 19. OIC Switch Branch Structures

### 19.1 Alert Evaluation Switch

```text
Switch: EvaluationResult
  Case triggeredCount > 0
    -> For each notification: invoke NotificationDispatchFlow
    -> Return triggered summary
  Case triggeredCount == 0 and errorCount == 0
    -> Return no-trigger summary
  Case errorCount > 0 and evaluatedCount > 0
    -> Return partial-success summary
  Case provider unavailable
    -> Write audit failure branch
    -> Return degraded response
  Otherwise
    -> System error branch
```

### 19.2 Notification Channel Switch

```text
Switch: NotificationChannel
  Case email
    -> Email adapter
  Case sms
    -> SMS adapter
  Case slack
    -> Slack adapter
  Case push
    -> Push adapter
  Case simulated
    -> Mark simulated
  Otherwise
    -> Mark skipped with unsupported_channel
```

### 19.3 Dashboard Command Switch

```text
Switch: DashboardCommand
  Case create_watchlist
  Case update_watchlist
  Case delete_watchlist
  Case create_alert
  Case update_alert
  Case delete_alert
  Case refresh_quotes
  Case evaluate_alerts
  Default validation_error
```

## 20. Module-Level Python Engine Design

### 20.1 Proposed Package Structure

```text
stock_monitoring_engine/
  app.py
  config.py
  api/
    dependencies.py
    routes_health.py
    routes_watchlists.py
    routes_alerts.py
    routes_quotes.py
    routes_notifications.py
    error_handlers.py
  domain/
    models.py
    alert_rules.py
    errors.py
  services/
    watchlist_service.py
    alert_service.py
    quote_service.py
    evaluation_service.py
    notification_audit_service.py
    execution_log_service.py
  providers/
    base.py
    mock_provider.py
    live_provider.py
    registry.py
  repositories/
    database.py
    users_repository.py
    watchlists_repository.py
    alerts_repository.py
    quotes_repository.py
    history_repository.py
    notifications_repository.py
    executions_repository.py
  migrations/
  tests/
```

### 20.2 Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `config.py` | Environment loading, provider selection, local mode |
| `api/*` | Request parsing, response envelopes, route handlers |
| `domain/alert_rules.py` | Pure alert evaluation logic |
| `providers/base.py` | Provider protocol/interface |
| `providers/mock_provider.py` | Deterministic local/CI quotes |
| `providers/live_provider.py` | Future live integration adapter |
| `services/evaluation_service.py` | Orchestrates quote fetch, persistence, rule evaluation |
| `repositories/*` | Database access and transaction boundaries |

### 20.3 Key Configuration

```text
APP_ENV=local
DATABASE_URL=sqlite:///data/local/stock_mon.db
MARKET_DATA_PROVIDER=mock
LOCAL_DEV_USER_ID=local-user
MOCK_PROVIDER_SCENARIO=default
LOG_LEVEL=INFO
```

Live provider configuration uses secret-backed values:

```text
MARKET_DATA_PROVIDER=live
MARKET_DATA_API_BASE_URL=<secret-backed-or-configured>
MARKET_DATA_API_KEY=<secret>
```

## 21. Alert Evaluation Logic

### 21.1 Algorithm

```text
load enabled alert targets
group targets by symbol
fetch latest quotes for symbols
persist quote snapshots
for each alert target:
  compare latest quote price with threshold using operator
  if condition false:
    set state not_triggered
  if condition true and previous state was triggered:
    set state suppressed_duplicate
  if condition true and previous state was not triggered/unknown/error:
    set state triggered
    create notification audit row
write execution log summary
return evaluated count, triggered count, notification audit IDs
```

### 21.2 Comparison Rules

| Operator | Trigger Condition |
|----------|-------------------|
| `gte` | latest price >= threshold |
| `lte` | latest price <= threshold |

### 21.3 Duplicate Suppression

- If the previous state is `triggered` and the condition remains true, do not create a new notification.
- If the condition becomes false, transition to `not_triggered`.
- If the condition becomes true again after false, create a new notification.
- Future cooldown logic may allow periodic reminders.

## 22. VBS Screen and Data-Binding Assumptions

### 22.1 Screens

| Screen | Purpose | Data Sources |
|--------|---------|--------------|
| Login | User authentication | Identity provider/VBS auth |
| Dashboard | Summary widgets and quote graph | `/quotes`, `/alerts/history` |
| Watchlist | Add/edit/delete symbols | `/watchlists` |
| Alert Targets | Configure thresholds and toggles | `/alerts` |
| Alert History | View evaluations and target changes | `/alerts/history` |
| Notifications | View delivery/audit status | `/notifications` |

### 22.2 Data Binding

- Watchlist table binds to `data.items` from `GET /api/v1/watchlists`.
- Alert form binds to selected watchlist row and alert model.
- Graph binds to quote snapshots ordered by `quoteTime`.
- Notification status chips bind to `status`.
- Error banners bind to common error envelope.

### 22.3 UX Behavior

- Save buttons disable during in-flight API calls.
- Toggle actions optimistically update only after API success.
- Validation messages are shown next to fields when gateway/OIC/engine returns field details.
- Notification statuses refresh after alert evaluation completes.

## 23. API Gateway Route, Header, and Auth Mapping

### 23.1 Route Mapping

| Gateway Route | Method | Target |
|---------------|--------|--------|
| `/api/v1/watchlists` | GET/POST | OIC watchlist integration |
| `/api/v1/watchlists/{watchlistId}` | PATCH/DELETE | OIC watchlist integration |
| `/api/v1/alerts` | GET/POST | OIC alert integration |
| `/api/v1/alerts/{alertId}` | PATCH/DELETE | OIC alert integration |
| `/api/v1/quotes/refresh` | POST | OIC quote refresh integration |
| `/api/v1/quotes` | GET | OIC quote query integration |
| `/api/v1/alerts/evaluate` | POST | OIC alert evaluation integration |
| `/api/v1/alerts/history` | GET | OIC alert history integration |
| `/api/v1/notifications` | GET | OIC notification status integration |

### 23.2 Header Mapping

| Source Claim/Header | Gateway Output Header |
|---------------------|-----------------------|
| subject/user id claim | `X-Authenticated-User-Id` |
| email claim | `X-Authenticated-User-Email` |
| scope/roles claim | `X-Auth-Scopes` |
| request ID or generated ID | `X-Correlation-Id` |

### 23.3 Authorization Scopes

Suggested scopes:

- `stock.watchlist.read`
- `stock.watchlist.write`
- `stock.alert.read`
- `stock.alert.write`
- `stock.quote.read`
- `stock.alert.evaluate`
- `stock.notification.read`

## 24. OIC Integration Flow Steps

### 24.1 Watchlist Flow

```text
Receive request from API Gateway
Validate identity headers
Switch by method/path action
Map request payload to engine payload
Invoke engine private endpoint
Map engine response to common dashboard envelope
Return to API Gateway
```

### 24.2 Alert Target Flow

```text
Receive request
Validate user context and payload
Invoke create/update/delete/list alert endpoint
If threshold changed, engine writes target history
Return normalized alert payload
```

### 24.3 Quote Refresh Flow

```text
Receive symbols
Validate symbol list
Invoke engine quote refresh
Switch on provider errors
Return quotes and partial errors
```

### 24.4 Alert Evaluation Flow

```text
Receive dashboard or schedule trigger
Invoke engine alert evaluation
Switch on triggeredCount/errorCount
For triggered notifications, invoke NotificationDispatchFlow
Patch notification statuses back to engine
Return evaluation summary
```

### 24.5 Notification Dispatch Flow

```text
Receive notification audit item
Switch on channel
Invoke downstream connector
On success, patch notification status sent/simulated
On failure, patch failed or retry_scheduled
Return channel result
```

## 25. Test Cases and Smoke Tests

### 25.1 Unit Tests

- Alert `gte` triggers when price equals threshold.
- Alert `gte` triggers when price is above threshold.
- Alert `gte` does not trigger when price is below threshold.
- Alert `lte` triggers when price equals threshold.
- Alert `lte` triggers when price is below threshold.
- Alert `lte` does not trigger when price is above threshold.
- Duplicate suppression skips notification when previous state is triggered.
- Transition from triggered to not triggered resets duplicate suppression.
- Mock provider returns deterministic quote fixtures.
- Provider error maps to normalized provider error code.

### 25.2 API Tests

- `GET /internal/v1/health` returns `ok`.
- `GET /internal/v1/ready` returns database and provider readiness.
- `POST /internal/v1/watchlists` creates uppercase symbol.
- Duplicate watchlist symbol returns `DUPLICATE_RESOURCE`.
- Missing user header returns `UNAUTHENTICATED`.
- Invalid threshold returns `VALIDATION_ERROR`.
- `POST /internal/v1/alerts/evaluate` creates notification audit for triggered alert.
- `PATCH /internal/v1/notifications/{id}/status` updates notification audit status.

### 25.3 Integration Tests

- Seed user, watchlist, and alert target.
- Run mock quote refresh.
- Run alert evaluation.
- Verify quote snapshot row exists.
- Verify execution log row exists.
- Verify notification audit row exists when threshold triggers.
- Verify no duplicate notification when condition remains true.

### 25.4 Smoke Tests

Local MVP smoke sequence:

```text
start engine
GET /internal/v1/health
GET /internal/v1/ready
POST /internal/v1/watchlists
POST /internal/v1/alerts
POST /internal/v1/quotes/refresh
POST /internal/v1/alerts/evaluate
GET /internal/v1/notifications
```

Cloud smoke sequence:

```text
VBS or test client calls API Gateway /api/v1/watchlists
API Gateway validates auth and routes to OIC
OIC calls private engine
Engine persists response
OIC returns mapped payload
API Gateway returns HTTPS response
Alert evaluation creates OIC notification branch
Notification audit status is patched back to engine
```

### 25.5 Security Tests

- Direct public access to Python engine endpoint fails.
- API Gateway route without auth fails.
- Engine user route without trusted identity header fails.
- User cannot read another user's watchlist or alerts.
- `.env`, provider keys, wallets, and Terraform variable files remain untracked.

## 26. Implementation Phases

### 26.1 Phase 1: Local Foundation

- Python service skeleton.
- Configuration loader.
- Database migrations.
- Mock provider.
- Health/readiness endpoints.

### 26.2 Phase 2: Domain and Persistence

- Watchlist model and CRUD.
- Alert target model and CRUD.
- Target history.
- Quote snapshots.
- Execution logs.
- Notification audit.

### 26.3 Phase 3: Alert Evaluation MVP

- Rule evaluator.
- Duplicate suppression.
- Mock provider scenarios.
- Evaluation endpoint.
- Local smoke tests.

### 26.4 Phase 4: API Contract Readiness

- OpenAPI or contract documentation.
- Error envelope standardization.
- Gateway/OIC header mapping documentation.
- VBS payload examples.

### 26.5 Phase 5: Cloud Integration

- API Gateway routes and policies.
- OIC integration flows and switch branches.
- Private VM deployment.
- Notification connectors.
- Live provider adapter.

## 27. Design Risks

| Risk | Design Response |
|------|-----------------|
| MVP bypasses OIC assumptions | Keep `/api/v1` and `/internal/v1` route mapping explicit |
| Engine receives spoofed identity headers | Accept trusted headers only on private path; gateway/OIC own public auth |
| Live provider behavior differs from mock | Add provider adapter contract tests and fixture-based error cases |
| Duplicate notifications spam users | Store last evaluation state and audit every notification |
| OIC becomes business logic owner | Keep price comparisons and state transitions inside Python |
| Database grows with quote history | Add retention policy and symbol/time indexes |

## 28. Design Completion Checklist

- [x] Four-layer architecture.
- [x] System context.
- [x] Major components.
- [x] Public/private network boundaries.
- [x] VBS dashboard flow.
- [x] OCI API Gateway auth/proxy flow.
- [x] OIC orchestration flow.
- [x] Python engine and database responsibilities.
- [x] Market data provider integration.
- [x] Notification architecture.
- [x] Security model.
- [x] Operations model.
- [x] Deployment view.
- [x] REST API endpoint specs.
- [x] JSON request/response payloads.
- [x] Database schema placeholders.
- [x] Alert rule model.
- [x] Watchlist model.
- [x] Quote snapshot model.
- [x] Target history model.
- [x] Notification audit model.
- [x] OIC Switch branch structures.
- [x] Mapping logic.
- [x] Validation rules.
- [x] Error handling rules.
- [x] Module-level Python engine design.
- [x] VBS screen/data-binding assumptions.
- [x] API Gateway route/header/auth mapping.
- [x] OIC integration flow steps.
- [x] Test cases and smoke tests.

