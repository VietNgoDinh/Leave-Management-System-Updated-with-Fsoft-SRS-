---
name: pre-review-gate
description: AI pre-review before a human gate (addendum D-40) — check the gate's artifacts against their inputs, the producing method skills' checklists and the gate's review focus, then record PASS or FINDINGS with `tools/ba prereview record`. Used by review-agent; not for direct use.
user-invocable: false
---

# AI pre-review of a gate

| | |
|---|---|
| Input | The brief `ba-ai/workflow/context/<SUBJECT>-<GATE>-prereview.yaml` (artifacts, their inputs, method skills, review focus, earlier findings); the use case's context package when the subject is a use case |
| Output | A verdict recorded by `tools/ba prereview record` (stored in `ba-ai/reviews/pre-review/<SUBJECT>/<GATE>.json`, hashed like a gate request) |
| Consumers | The orchestrator: FINDINGS go back to the artifact's owner, then a new round (at most 2). PASS lets the gate be requested. The human reviewer sees any findings left over. |

## Procedure

1. Read the brief. Then read, in this order:
   - the artifacts under review, and the generated `views` the brief lists (the permission matrix, use case diagram, state transition, object relationship diagram): the human reads those, so read them as they will;
   - the inputs each was built from;
   - the *Checklist* and *Rules* of each producing method skill (`method_skills`).
2. Check each artifact:
   - **Faithful to its inputs.** Nothing contradicts an approved upstream artifact or catalog item. Nothing is added that the inputs don't support.
   - **Complete.** Every rule, step rule, AF, EF and AC the inputs require is covered. Every checklist item holds.
   - **Consistent.** Message codes and texts, error codes, field names, IDs and states agree across the artifacts of this gate and with the message and email catalogs.
   - **No invented decisions.** Unknowns are open questions or assumptions, not silent choices.
   - **The review focus.** Each bullet the human will check: would they send it back?
   - **What each gate adds** (addendum §14):
     - **GATE-02:** every requirement typed, every NFR with measurable criteria or an open question; the glossary covers the notation and the product's terms; every process has its workflow document; every use case is one function with an objective, an object and permissions that the requirements support (every O** with its scope), and the permission matrix has no X where a requirement grants access, nor an O without one; the lifecycle transitions are all performed by a use case; the common use cases and Other Requirements cite their adaptations.
     - **GATE-03:** each screen has the component table with source attributes, buttons that refer to a use case, list data source and sorting, and messages with their codes and catalog texts.
     - **GATE-05:** the activities flow matches the approved screens; every step rule is keyed to a step and typed; every Validating rule shows its message; every email template's recipients and placeholders are bound; a delta specification states only what differs from its common use cases; the acceptance criteria cover every step rule, AF and EF.
     - **GATE-09:** the security rules enforce the permission matrix without copying it; the design system holds visual rules only.
     - **GATE-08:** the guide uses the glossary's terms.
3. Previous round's findings (`previous_findings`): check whether each one was addressed. Don't repeat a finding the owner explained away unless the explanation is wrong; then say why.
4. Write the findings file in `ba-ai/workflow/context/<SUBJECT>-<GATE>-findings.yaml`:
   ```yaml
   findings:
     - artifact: ba-ai/functional-requirements/use-case-specifications/UC-007/behaviour.md
       severity: MAJOR          # MAJOR: the reviewer would send it back · MINOR: could be approved as is
       issue: "UC-007-BR-03 shows IEM-002 on a duplicate name; the API design returns 409 with EMSG-004 for the same check"
       suggestion: "Align with the API design (technical/api/UC-007.md, API-012 errors)"
   ```
   `artifact` must be one of the gate's artifacts. Name the precise place: ID, section or line.
5. Record:
   - `tools/ba prereview record <GATE> <SUBJECT> --verdict FINDINGS --file ba-ai/workflow/context/<SUBJECT>-<GATE>-findings.yaml`
   - or, with no MAJOR finding: `--verdict PASS`, with the file only if you have MINOR notes.

## Checklist

- [ ] Every finding is specific (artifact + ID/section) and says why it matters.
- [ ] No style-only findings; MINOR is used only for things the reviewer could accept as they are.
- [ ] Nothing was edited; the verdict was recorded with the CLI.
