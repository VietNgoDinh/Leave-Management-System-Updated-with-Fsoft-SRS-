---
name: define-use-cases
description: BA workflow Phase 3 step 3.6 — the use-case list, where each use case is one function of the system (objective, object, permission per actor, allowed states, transitions, common use cases followed), with process, actor, application, complexity, risk (D-23), requirements, rules and entities, plus the links back from processes and rules (ba-ai/high-level-requirements/use-cases.yaml). Used by overview-analysis-agent; not for direct use.
user-invocable: false
---

# Step 3.6 — Use Cases (functions)

| | |
|---|---|
| Input | Processes, rules, objects (data model with lifecycles), actors, applications, requirements, common use cases |
| Output | `high-level-requirements/use-cases.yaml` (UC); `related_use_cases` on rules; `use_cases` on process steps |
| Consumers | The BA at GATE-02 (with the generated use case diagram and permission matrix), planning (Phase 4), the Spec Engine (every context package), GATE-07 (risk) |

**A use case is one function of the system** (D-46): one row of the use case diagram ("This function allows <actors> to …") and one row of the permission matrix. It is also the unit that is specified, built and approved. There are no sub-functions.

## Procedure

1. **Find the functions.** One use case per thing an actor does in the system, or per system job. Name it verb + object: "Submit leave request", "Approve or reject leave request", "Cancel unreviewed leave requests at month end" (actor = the scheduler).
   - Operations that need **different permissions** are separate use cases. "Manage leave types" (create, edit and view, all Admin/HR) is one; if employees could also view leave types, "View leave types" would be another.
   - Plain create / view / update / delete / disable of one object is one "Manage X" use case that **follows** the matching common use cases (D-50). Its specification then states only what differs.
2. Reuse first (`tools/ba find <keywords>`), then add it:
   ```
   tools/ba catalog add use-cases --data '{
     "name": "Confirm or deny leave request",
     "objective": "confirm or deny the leave requests that selected them as confirming Project Manager",
     "business_process": "BP-001", "actor": "ACT-002", "application": "APP-001",
     "object": "ENT-006", "allowed_states": ["PENDING_CONFIRMATION"],
     "transitions": ["PENDING_CONFIRMATION -> PENDING_APPROVAL", "PENDING_CONFIRMATION -> DENIED"],
     "permissions": [{"actor": "ACT-002", "access": "SCOPED", "scope": "requests that selected them"}],
     "description": "<goal, main path, key variations, outcome>",
     "complexity": "MEDIUM", "risk_level": "MEDIUM", "risk_flags": ["COMPLIANCE"],
     "requirements": ["REQ-003"], "business_rules": ["BR-006", "BR-008"],
     "entities_read": ["ENT-006"], "entities_written": ["ENT-006", "ENT-008"]}'
   ```
3. **The function fields:**
   - **objective**: the end of "This function allows <actors> to …", in lower case and without a final period: "submit a leave request for future dates or for past dates in the current month". Validation rejects an objective that starts with "This function".
   - **object**: the entity (ENT) the function acts on; it groups the permission matrix.
   - **permissions**: one entry per actor who may perform it, with `access`:
     - `ALL` (O): on every item;
     - `OWN` (O*): on the items they created or own; add `scope` when "own" needs saying ("requests they submitted");
     - `SCOPED` (O**): within a scope; `scope` is required ("requests of employees in the unit they manage").
     Actors not listed may not perform it (X): access is denied unless granted. The primary `actor` must be listed with access other than NONE. Permissions come from the requirements and decisions; an unclear one is an open question (SECURITY), never a guess.
   - **allowed_states**: the states of the object's lifecycle in which the function is allowed. Leave it out when any state is fine (creation, lists).
   - **transitions**: the lifecycle transitions the function performs, `FROM -> TO` (`(new) -> …` for creation). Validation warns about a lifecycle transition that no use case performs, and rejects one that is not in the lifecycle.
   - **follows**: the common use cases (CMUC-…) a "Manage X" use case follows.
4. **Complexity** is LOW, MEDIUM or HIGH: number of screens, rules and branches, and integrations.
5. **Risk** (D-23) is a *proposal* that the BA confirms at GATE-02:
   - `risk_level` LOW / MEDIUM / HIGH / CRITICAL;
   - `risk_flags`, any of FINANCIAL, IRREVERSIBLE, SECURITY, COMPLIANCE, PERSONAL_DATA. Set a flag only when the use case really moves money, can't be undone, changes access, falls under regulation, or processes personal data.
   - HIGH, CRITICAL or any flag makes a human critical-flow test (GATE-07) mandatory after QA. Explain each flag in the description.
6. **Link back:**
   - each rule's `related_use_cases`: `tools/ba catalog update BR-... --data '{"related_use_cases": [...]}'`. The list is replaced, so repeat the existing values.
   - each process step's `use_cases` (see `model-business-processes`).
7. **Coverage check**, before returning:
   - every REQ of type FUNCTIONAL is satisfied by at least one use case;
   - every BR is used by at least one use case;
   - every process step that an actor performs has a use case;
   - every lifecycle transition is performed by a use case (`tools/ba validate` lists the gaps as warnings).
   Report the gaps. A gap is an open question, not a new invented use case.
8. After `tools/ba sync`, read the generated `high-level-requirements/use-case-diagram.view.md` and `permission-matrix.view.md` as the BA will at GATE-02.

## Checklist

- [ ] Every use case has objective, process, actor, application, object, permissions, description, complexity, risk_level and requirements.
- [ ] Every permission is supported by a requirement or decision; every O** states its scope.
- [ ] Operations with different permissions are separate use cases; plain CRUD follows the common use cases.
- [ ] Rules and entities are listed on the use case and linked back; risk flags are justified.
