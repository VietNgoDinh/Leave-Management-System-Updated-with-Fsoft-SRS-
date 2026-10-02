---
name: write-acceptance-criteria
description: BA Spec Engine step 5.7 — testable Given/When/Then acceptance criteria covering the activities flow, every step rule, policy rule, alternate and error flow, and the permissions (ba-ai/functional-requirements/use-case-specifications/<UC>/acceptance.md). Used by spec-agent; not for direct use.
user-invocable: false
---

# Step 5.7 — Acceptance Criteria

| | |
|---|---|
| Input | The use case behaviour (5.4), the API design (5.6), the screens (when the use case has UI), the use case's permissions, context package |
| Output | `ba-ai/functional-requirements/use-case-specifications/<UC>/acceptance.md` |
| Consumers | Compiled spec (5.8), QA test cases (TC VERIFIES AC), coding agent, the user stories (an AC may name its story) |

## Rules

- One criterion per observable behaviour: `### <UC>-AC-01 — <title>` followed by **Given / When / Then** lines (validation fails without all three).
- **Testable:** concrete data and observable results — status, the message by its code and text, data change, HTTP code, the email sent (ET-…). Never "works correctly", "is fast", "user-friendly".
- End each criterion with `**Covers:**` listing what it verifies: activities-flow steps, step rules (<UC>-BR-…), policy rules (BR-…), <UC>-AF-…, <UC>-EF-….
- **Coverage is complete:** the main flow; every step rule; every policy and common rule the use case applies; every AF and EF; permission denial for every actor with X, and the scope limit of every O* and O**; at least one boundary case per numeric or date rule. Validation warns about a step rule, AF or EF that no criterion covers.
- For a "Manage X" use case that follows common use cases, cover the CMUC steps it uses as well as its own rules: the criteria test the whole function.
- When the use case has several user stories, add `**Story:** US-…` to each criterion so the story's acceptance criteria are known.
- IDs are stable: on revisions keep existing numbers and append new ones.
- Only behaviour defined upstream. If writing a criterion exposes a gap, add an open question instead of deciding.

## Template

````markdown
---
id: <UC>
artifact_type: acceptance-criteria
title: <use case name> — Acceptance Criteria
status: DRAFT
version: 1
baseline: TO_BE
origin: AI
relations:
  business_rules: [<BR>, ...]
  screens: [<SCR>, ...]
  apis: [<API>, ...]
  messages: [<IEM>, ...]
open_questions: []
updated_at: ""
---
# <UC> — <use case name>: Acceptance Criteria

## Acceptance Criteria

### <UC>-AC-01 — <title>
- **Given** …
- **When** …
- **Then** … IEM-003 "Enter a start date in the future or in the current month." is shown under [Start date]
- **Covers:** step (2), <UC>-BR-02, BR-001

## Coverage
| Item | Covered by |
|---|---|
| <UC>-BR-02 | <UC>-AC-01 |
| BR-001 | <UC>-AC-01 |
| <UC>-AF-01 | <UC>-AC-03 |
| <UC>-EF-01 | <UC>-AC-04 |
| Permission (X for Line Manager) | <UC>-AC-05 |
````

Every BR in `relations.business_rules` and every step rule, AF and EF of the behaviour must appear in the Coverage table with at least one criterion.
