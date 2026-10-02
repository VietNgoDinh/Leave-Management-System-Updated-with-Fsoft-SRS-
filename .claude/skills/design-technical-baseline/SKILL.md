---
name: design-technical-baseline
description: BA workflow Phase 6A for a new product — propose the technical architecture baseline (stack, architecture, repositories, API conventions, error handling, logging, testing, coding rules, security rules that enforce the permission matrix, the visual design system) and register services and repositories, for SA approval at GATE-09. Used by technical-baseline-agent; not for direct use.
user-invocable: false
---

# Phase 6A — Technical Architecture Baseline (designed)

| | |
|---|---|
| Input | Product overview, applications, integrations, objects (data model), requirements (the NON_FUNCTIONAL ones especially, with their criteria), the Other Requirements (`other-requirements/`: field controls, messages, list behaviour), the permission matrix (`high-level-requirements/permission-matrix.view.md`), technical constraints in `input-management/user-requirements/` and `reference-documents/`; context package `TECH_BASELINE.yaml` |
| Output | `technical/architecture/architecture.md`, `technical/coding-rules/frontend.md`, `technical/coding-rules/backend.md`, `technical/security/security-rules.md`, `technical/design-system.md`; catalogs `technical/architecture/services.yaml` (SVC) and `workflow/repositories.yaml` (REPO) |
| Consumers | The SA at GATE-09; API design (5.6, follows the API conventions); prototypes (5.3, follow the design system and the Other Requirements); coding (7); QA (8, testing conventions); user-guide screenshots (9) |

## Procedure

1. **Facts first.** Collect every technical constraint the stakeholders stated (hosting, existing identity provider, mandated language, data residency, browsers) and every NON_FUNCTIONAL requirement's criteria, and cite each one. Everything else you write is a **proposal**.
2. **Mark proposals.** For each choice the material doesn't make, write: **Proposed — SA to confirm:** <choice> — <one-line rationale>; alternative: <option>. When the choice really matters (database, identity, hosting, integration style), also add a TECHNICAL open question whose `related` lists the SVC, APP, ENT or INT it concerns (or leave it empty), and list its ID in the document's `open_questions`. The SA's GATE-09 decision settles it.
3. **Services.** One per deployable unit or bounded module that owns data:
   `tools/ba catalog add services --data '{"name": "...", "responsibility": "...", "repository": "REPO-...", "entities": ["ENT-..."], "integrations": ["INT-..."]}'`
   Register the repositories first.
4. **Repositories.** Each product repository, kept separate and never merged (master §2.1). They live next to this workspace:
   `tools/ba catalog add repositories --data '{"name": "room-booking-api", "type": "backend", "status": "PLANNED", "path": "../room-booking-api", "description": "..."}'`
   The coding agent creates them later and sets `status: ACTIVE`.
5. **Write the documents** with the headings below. `tools/ba validate` checks them.
   - **Testing Conventions** must name, for each repository: the unit test command; the API or integration test command; and the UI and end-to-end tool — **Playwright, installed in the frontend repository** (`npm i -D @playwright/test`, `npx playwright install`) — with its run command. QA (8.2) and the user-guide screenshots (9) use exactly these commands.
   - **API Conventions**: base path and versioning, resource naming, casing, pagination, filtering, standard status codes, the error body (it carries the message code: EMSG-…, IEM-…, so the UI shows the catalog text), idempotency, and all-or-nothing multi-item operations.
   - **Security rules — Authorization** enforces the **permission matrix** (functions × roles, generated from the use cases and approved at GATE-02). Don't repeat the matrix: refer to it, and define how it is enforced — deny by default, a server-side check on every request, how O* (own items) and O** (the stated scope) are checked against the object, what an out-of-scope request returns, how roles are resolved from the actors' role mappings. Data-level rules the matrix doesn't express (who may download a document, field masking) stay here.
   - **Design system — visual design only** (D-53): principles, layout and grid, breakpoints, colours, typography, and how each component and status looks. Behaviour conventions — field controls, message types, list columns, pagination, search, bulk actions, date formats — are the BA's Other Requirements, approved at GATE-02: make the components implement them, and refer to them rather than restating them. A visual choice that conflicts with them is an open question for the BA, not a silent override.
6. Stamp `architecture.md` first, then the other four (they record its hash). Then `tools/ba validate`.

**A project upgraded from an earlier kit version:** its design system held behaviour patterns (form validation, lists, dialogs, date formats). The overview agent carried them over to the Other Requirements; remove them from the design system and refer to `other-requirements/` instead. Replace the Authorization role/permission table by a reference to the permission matrix plus the enforcement rules above.

## Required headings

| Document | id | Headings |
|---|---|---|
| `technical/architecture/architecture.md` (`technical-architecture`) | ARCH | Technology Stack · Application Architecture · Repository Structure · API Conventions · Error Handling · Logging · Testing Conventions — add Database, Dependency Rules and Deployment when relevant |
| `technical/coding-rules/frontend.md` / `backend.md` (`coding-rules`) | CODING-FRONTEND / CODING-BACKEND | Conventions (naming, structure, state management, dependency rules, linting and formatting, commit message format `UC-007: …`) |
| `technical/security/security-rules.md` (`security-rules`) | SECURITY | Authentication · Authorization (enforcing the permission matrix) · Data Protection (personal data, retention, encryption) · Audit |
| `technical/design-system.md` (`design-system`) | DESIGN-SYSTEM | Principles · Layout · Components (visual). New products get a minimal default (D-27). |

Frontmatter for each (fill `id`, `artifact_type`, `title`):

```yaml
---
id: ARCH
artifact_type: technical-architecture
title: <product> — Technical Architecture
status: DRAFT
version: 1
baseline: TO_BE
origin: AI
open_questions: [Q-..., ...]
updated_at: ""
---
```

## Checklist

- [ ] Every stated constraint and NFR criterion is cited; every other choice is marked as a proposal for the SA.
- [ ] Every application has a repository and every object has an owning service.
- [ ] The testing conventions name runnable commands per repository, with Playwright in the frontend repository.
- [ ] Authorization enforces the permission matrix without copying it; every PERSONAL_DATA or SECURITY flagged use case is covered.
- [ ] The design system is visual only and refers to the Other Requirements for behaviour.
