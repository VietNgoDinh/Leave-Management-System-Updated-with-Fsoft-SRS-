---
name: compile-use-case-spec
description: BA Spec Engine step 5.8 — assemble the code-ready use-case specification in the company layout with `tools/ba compile` and write its two narrative sections (ba-ai/functional-requirements/use-case-specifications/<UC>/spec.md). Used by spec-agent; not for direct use.
user-invocable: false
---

# Step 5.8 — Compile the Code-Ready Use Case Specification

| | |
|---|---|
| Input | The behaviour (5.4), sequence (5.5), API design (5.6) and acceptance criteria (5.7); the screens and prototype when the use case has UI; the context package |
| Output | `ba-ai/functional-requirements/use-case-specifications/<UC>/spec.md` |
| Consumers | BA approval (GATE-05) → SA review (GATE-06) → acceptance tests (8.1), coding agent, QA; the SRS publication (the company sections) |

## How it is built (D-43, D-49)

`tools/ba compile <UC>` assembles the 18-section document. The company skeleton comes first, then the kit's technical sections:

| # | Section | From |
|---|---|---|
| 1 | Use Case Description | The objective, actor and permissions in the use case catalog; the trigger, pre- and post-condition in the behaviour |
| 2 | Activities Flow | The behaviour, after the steps of each common use case it follows |
| 3 | Business Rules | The company's Step \| BR Code \| Description table: the followed CMUCs' rules, then the use case's step rules |
| 4–5 | Alternate Flows, Error Flows | The behaviour |
| 6 | Common Business Rules | The policy and common rules (BR-…) the use case uses |
| 7 | Screens | The screen design (component tables), with the prototype's path; "Not applicable" for a system use case |
| 8–9 | Messages, Email Templates | The catalogs, for every code the screens and the behaviour cite |
| 10 | Data Entities | The data model |
| **11** | **Business Context** | **You** |
| 12–14 | Sequence Diagram, API Specification, Acceptance Criteria | Their documents |
| **15** | **Dependencies** | **You** |
| 16–18 | Assumptions, Open Questions, Traceability | The catalogs and the documents above |

- Copying is done by the tool rather than by you, so the specification can never drift from what was reviewed upstream. `tools/ba validate` rejects any hand edit to a generated section.
- **You write the two narrative sections.** Each starts with a `<!-- TODO(spec-agent): … -->` hint; replace the whole hint with the text:
  - **11 Business Context:** why the use case matters: its process step (BP-…-S…), the requirements it satisfies, and the business outcome. A few sentences.
  - **15 Dependencies:** the other use cases, integrations and open technical decisions it depends on, and what each one provides.

## Procedure

1. `tools/ba stamp ba-ai/functional-requirements/use-case-specifications/<UC>/acceptance.md` (if not done), then `tools/ba compile <UC>`.
2. Write the two narrative sections from the upstream artifacts and the context package:
   - **Compile, don't create.** Every statement comes from an upstream artifact or the context package. No new behaviour is introduced here.
   - A section that doesn't apply says "Not applicable." with a few words of why.
3. **Conflicts are surfaced, not resolved.** If two upstream artifacts disagree (a message code, an error code, a field rule), don't pick one. Add an open question and tell the orchestrator in your summary which artifact needs fixing. The generated sections show both versions, because they copy them.
4. `tools/ba stamp ba-ai/functional-requirements/use-case-specifications/<UC>/spec.md` → `tools/ba validate`.

**REGENERATE** (an upstream artifact changed): run `tools/ba compile <UC>` again. It refreshes the generated sections and keeps your narrative. Then update only the narrative sentences the change affects, and stamp.

## Checklist

- [ ] No TODO hint is left; no generated section was edited by hand.
- [ ] Every narrative statement traces to an upstream artifact or the context package.
- [ ] Conflicts between upstream artifacts are open questions and are reported, not silently resolved.
