---
name: design-api
description: BA Spec Engine step 5.6 — specify every API the use case needs (reused, modified, new) from the sequence flow and the use case's step rules (ba-ai/technical/api/<UC>.md). Used by technical-analysis-agent; not for direct use.
user-invocable: false
---

# Step 5.6 — API Analysis and Design

| | |
|---|---|
| Input | `ba-ai/technical/sequence/<UC>.md`, the use case behaviour (step rules, messages, emails), API conventions in `technical/architecture/architecture.md`, `technical/security/security-rules.md`, the permission matrix (the use case's permissions in the context package), `technical/api/api-catalog.yaml`, context package |
| Output | `ba-ai/technical/api/<UC>.md`; catalog entries; screens' `apis` updated |
| Consumers | Acceptance criteria (5.7), compiled spec (5.8), SA review (GATE-06), acceptance tests (8.1), coding (7) |

## Procedure

1. Take each API ID in the sequence. It must already be in the catalog (step 5.5 registered it).
2. Specify it with the YAML block in the template. Follow the API conventions exactly: paths, casing, pagination, status codes, error body, all-or-nothing behaviour for multi-item operations.
3. **Authorization** comes from the use case's permissions (the permission matrix) and the security rules: name the access level (O, O*, O**) and how the scope is checked. **Validation** comes from the step rules: every server-side check names the step rule it implements (`UC-001-BR-02`), the policy rule behind it (BR-…) when there is one, and the error it returns with the message code the UI shows (`422 START_DATE_OUT_OF_WINDOW → IEM-003`).
4. **An API is defined in full once.** The use case that introduces or modifies it holds the full definition. Other use cases list it in the summary and write "defined in technical/api/<other UC>.md".
5. Link screens to APIs: `tools/ba catalog update SCR-00x --data '{"apis": ["API-00a", "API-00b"]}'` (the list is replaced). A system use case has no screens to link.
6. **Don't make SA decisions.** Anything needing an architect (caching, pagination limits beyond the conventions, an external system's real endpoint, idempotency keys) goes under *Unresolved Technical Decisions* as an open question with `target_stakeholder: TECHNICAL`.

## Template

````markdown
---
id: <UC>
artifact_type: api-design
title: <use case name> — API Design
status: DRAFT
version: 1
baseline: TO_BE
origin: AI
relations:
  apis: [<API>, ...]
  business_rules: [<BR>, ...]
  entities_read: [<ENT>, ...]
  entities_written: [<ENT>, ...]
  screens: [<SCR>, ...]
  messages: [<IEM>, ...]
open_questions: []
updated_at: ""
---
# <UC> — <use case name>: API Design

## API Summary
| API | Method | Endpoint | Change | Purpose | Called from |
|---|---|---|---|---|---|

## API Details

### <API> — <METHOD> <endpoint>
```yaml
api_id: <API>
method: POST
endpoint: /api/v1/...
purpose: ...
caller: <SCR> (<APP>)          # or the scheduler for a system use case
service: <SVC>
authentication: ...
authorization: ...            # the permission: e.g. Employee O* (own requests), from the permission matrix
request:
  body: {}                    # field: type, required, constraints
response:
  "201": {}
validation:
  - "start_date — not before the first day of the current month (UC-001-BR-02, BR-001) → 422 DATE_OUT_OF_WINDOW / IEM-003"
step_rules: [<UC>-BR-02, <UC>-BR-03]
business_rules: [<BR>]
entities: {reads: [<ENT>], writes: [<ENT>]}
errors:
  - {status: 409, code: CODE, message: EMSG-…, when: "...", rule: <UC>-BR-…}
emails: [ET-…]                # sent through the notification service
downstream_calls: []          # other APIs or integrations (INT-…)
```

## Unresolved Technical Decisions
- <Q-ID> — decision needed from SA/Developer (or "None")
````
