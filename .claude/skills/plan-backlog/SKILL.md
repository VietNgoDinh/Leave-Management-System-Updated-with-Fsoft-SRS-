---
name: plan-backlog
description: BA workflow Phase 4 — group the approved use cases into epics with priorities, dependencies, readiness and user stories, and write the delivery backlog through `tools/ba backlog plan` (ba-ai/agile-project/backlog.yaml, user-stories.yaml). Used by planning-agent; not for direct use.
user-invocable: false
---

# Phase 4 — BA Planning (delivery backlog and user stories)

| | |
|---|---|
| Input | Context package `PLANNING.yaml`: the use cases (with process, actor, object, application, complexity, risk), requirements and their priorities, open questions, the current backlog and user stories |
| Output | `agile-project/backlog.yaml` and `agile-project/user-stories.yaml` — written only by `tools/ba backlog plan --file <plan>` |
| Consumers | `tools/ba next` (what to specify next, in priority order), `/ba-spec`, the BA (who adjusts priority, status and dependencies); the generated epic pages and the SRS *Agile Project* chapter |

## Procedure

1. **Epics.** Group the use cases by the business capability they deliver, usually one business process or one coherent part of it. An epic should be deliverable and demonstrable on its own.
2. **Priority** (HIGH / MEDIUM / LOW) for each epic and each use case comes from the priorities of the requirements it satisfies: the highest one wins. Ties are broken by dependency order. Don't invent a business priority. If the requirements don't separate two epics, keep them equal and say so.
3. **Dependencies.** UC-B depends on UC-A when B's specification needs A's approved screens, APIs or data. For example, "modify a request" depends on "submit a request". The spec engine starts B only after A's GATE-05. Keep the list minimal; the tool rejects cycles.
4. **Readiness**, as a proposal the BA can change in the YAML:
   - `READY` — the use case can be specified now.
   - `BACKLOG` — not yet. Its HIGH open questions are unanswered, or it's deliberately later. Give the reason in your summary.
   - `BLOCKED`, with `blocked_reason` — something outside the BA's control stops it.
5. **User stories** (D-60) are tracking items for the team; the use case stays the specification and delivery unit, so stories carry no gate. Write **one story per use case** by default: "As a <actor>, I want to <objective>, so that <benefit from the requirements>". Split a use case into several stories only when its parts can be delivered and demonstrated separately: a "Manage X" use case following several common use cases may get one story per operation (create, update, view list). The benefit comes from the requirements; when they don't state one, say "so that <the requirement's name> is met" rather than inventing a motive.
6. **Write the plan** to `ba-ai/workflow/context/PLANNING-plan.yaml`:
   ```yaml
   epics:
     - name: Leave request lifecycle        # omit epic_id for a new epic; keep it for an existing one
       priority: HIGH
       description: Employees request leave; managers confirm and approve.
       use_cases:
         - use_case_id: UC-001
           priority: HIGH
           status: READY
           dependencies: []
           stories:                          # omit id for a new story; keep it to update one
             - name: Submit a leave request
               story: As an Employee, I want to submit a leave request, so that my absence is approved in time.
         - {use_case_id: UC-003, priority: MEDIUM, status: READY, dependencies: [UC-001]}
   ```
   Then run `tools/ba backlog plan --file ba-ai/workflow/context/PLANNING-plan.yaml`.
   - Every use case in the catalog must appear exactly once.
   - On a re-plan, copy the current entries from the context package: started use cases keep their status (the tool never undoes progress), existing epics keep their `epic_id`, and existing stories keep their `id`. Stories the plan doesn't mention stay as they are.
   - Planning is complete when every use case is planned and has at least one story.
7. Read the result with `tools/ba status`, and the generated `agile-project/epics/<EPIC>.view.md`.

## Checklist

- [ ] Every catalog use case is in exactly one epic and has at least one user story.
- [ ] Priorities trace to requirement priorities; dependencies follow data and screen reuse.
- [ ] Every `BACKLOG` use case has its reason stated in your summary; every story's benefit comes from the requirements.
