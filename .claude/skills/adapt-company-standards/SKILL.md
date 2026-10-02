---
name: adapt-company-standards
description: BA workflow Phase 3 — adapt the company's SRS standards (company-standards/) for the product — the Other Requirements (field controls, message configuration, list behaviour), the common use cases (CMUC), the common business rules and the default messages — for BA approval at GATE-02. Used by overview-analysis-agent; not for direct use.
user-invocable: false
---

# Step 3.8 — Adapt the company standards (addendum D-50, D-53)

| | |
|---|---|
| Input | `company-standards/` (the company defaults and its README); the requirements (the NON_FUNCTIONAL ones especially); the elicitation summary; the applications; for a project upgraded from an earlier kit version, the approved `technical/design-system.md` |
| Output | `ba-ai/other-requirements/field-controls.md`, `message-configuration.md`, `list-behaviour.md`; items in `functional-requirements/common-use-cases.yaml` (CMUC), `high-level-requirements/business-rules.yaml` (`kind: COMMON`) and `appendices/messages.yaml` |
| Consumers | The BA at GATE-02; screen design (5.2: component types, messages, list behaviour); behaviour (5.4: common use cases, common rules); prototypes (5.3); coding (7) |

These conventions belong to the BA (D-53). The company defines them once in `company-standards/`. Each project adapts them where its requirements differ, and the BA approves the result at GATE-02. They are common: many screens and use cases refer to them, so getting them right once saves every later review.

## Procedure

1. **Messages first**, because the common use cases cite them. Read `company-standards/messages.yaml`. Add the defaults the product needs: the common use cases you will add need "Please input in this field." and, if you add Delete or Disable, their confirmations.
   - Reuse before creating: `tools/ba find <words>`.
   - `tools/ba catalog add messages --data '{"type": "INLINE_ERROR", "text": "Please input in this field."}'` (the tool gives the code from the type, e.g. IEM-001).
2. **Common business rules.** Read `company-standards/common-business-rules.yaml`. Add each one the product needs as a business rule of `kind: COMMON`. Its `source` names the company standard and what makes it apply here: "Company SRS standard CBR1; security rules require an audit trail". If nothing in the material makes it apply, don't add it.
3. **Common use cases.** Read `company-standards/common-use-cases.yaml`. Add the operations the product's "Manage X" use cases need. Most products need View list, Create, Read and Update. Add Delete or Disable only when a requirement asks to remove items.
   - Replace each `[[message: …]]` with the message code from step 1, and each `[[rule: …]]` with the BR ID from step 2. Validation rejects a placeholder left in.
   - Adapt a text only where the product differs, and say so in your summary.
   - `tools/ba catalog add common-use-cases --data '{…}'`. Leave out the IDs: the tool allocates CMUC-NNN and numbers the step rules CMUC-NNN-BR-01, -02, …
   - A product with no "Manage X" function needs none: run `tools/ba catalog init common-use-cases` so GATE-02 can record that there are none.
4. **The three Other Requirements documents.** Copy each of `field-controls.md`, `message-configuration.md` and `list-behaviour.md` from `company-standards/` to `ba-ai/other-requirements/`, add the frontmatter below, then adapt it:
   - Keep every company rule that applies to the product.
   - Change a rule the requirements contradict. Example: the product needs a file upload control the company list lacks; add a "File Upload" row. Record each change and its source (REQ, decision) in a short *Project adaptations* list at the end of its section.
   - Never invent a convention the material doesn't support. When a choice is open (a date format, a page size), keep the company default and add an open question (`target_stakeholder: UX`).
   - Keep the column names of the tables: screen validation reads *Control* and *Also written as* in Common Field Controls, and *Component type* in Other Component Types.
5. **Upgraded project.** An approved design system already holds behaviour conventions that the SA approved at GATE-09: validation timing, page sizes, date formats, list filters, confirmation dialogs. Under the company layout they are BA conventions (D-53). Carry each one over to the matching section, citing "carried over from technical/design-system.md (approved at GATE-09)". List every difference from the company default in your summary, so the BA decides it at GATE-02. The technical baseline agent then removes them from the design system.
6. Stamp each document (`tools/ba stamp ba-ai/other-requirements/<file>.md`), then `tools/ba validate`.

## Frontmatter

```yaml
---
id: FIELD-CONTROLS                 # MESSAGE-CONFIGURATION · LIST-BEHAVIOUR
artifact_type: field-controls      # message-configuration · list-behaviour
title: <product> — Common Field Controls
status: DRAFT
version: 1
baseline: TO_BE
origin: AI
open_questions: []
updated_at: ""
---
```

Required headings:
- `field-controls`: Common Field Controls, Other Component Types.
- `message-configuration`: Common Messages Configuration.
- `list-behaviour`: View Columns Display, Pagination, Search Component, Bulk Action.

## Checklist

- [ ] Every common use case cites existing message codes and BR IDs, and no `[[…]]` placeholder is left.
- [ ] Every common business rule of kind COMMON cites why it applies to this product.
- [ ] The field-controls tables keep their column names; every control the screens will need is listed.
- [ ] Every adaptation cites its source; open choices are open questions, not decisions.
