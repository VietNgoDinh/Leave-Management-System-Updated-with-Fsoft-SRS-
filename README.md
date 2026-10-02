# BA End-to-End AI Workflow — Claude Code kit

A stateful Business Analyst workflow for Claude Code. It runs from stakeholder material to a delivered, tested and documented use case, with human approval gates, stop/resume, a traceability graph and parallel agents. Its artifacts follow the company's System Requirement Specification structure, and it publishes the SRS on demand.

- What it is and why: [docs/master-spec.md](docs/master-spec.md) + [docs/implementation-decisions.md](docs/implementation-decisions.md)
- How it runs: [ba-ai/workflow/workflow.md](ba-ai/workflow/workflow.md)
- Status: **milestone 2**, the full MODE_B route for a new product (addendum §13), in the company SRS structure (addendum §14):
  - elicitation → overview (GATE-02) → technical baseline (GATE-09) → planning (backlog and user stories) → site map;
  - per use case: Spec Engine — screens (GATE-03), prototype (GATE-04), behaviour, sequence, API, acceptance criteria, compiled specification (GATE-05) → technical review (GATE-06) → acceptance tests → coding → QA and fix loop → code review (GATE-10) → critical-flow test (GATE-07, risky use cases only) → user guide (GATE-08). A scheduled job without screens skips the screen and prototype steps.
  - Before each human gate (except GATE-07), an AI reviewer with a fresh context checks the work first.

  Reverse engineering of an existing product (MODE_A) and the change-request engine (MODE_C) come later.

## Start a new product (MODE_B)

1. Open this folder in VS Code and start Claude Code **in this folder**. Hooks and skills load at startup. The first `tools/ba` call creates `.venv` (needs Python 3.9+ and internet once).
2. Put the client's requirement documents, briefs, transcripts, emails and screenshots in `ba-ai/input-management/user-requirements/`, and standards, style guides or external-system documents in `ba-ai/input-management/reference-documents/`. Set the project name in `ba-ai/workflow/state.json` (`project.name`).
3. Type `/ba-next`. Claude runs elicitation and stops when it needs you:
   - **Stakeholder questions:** hold the conversation, save the minutes in `ba-ai/input-management/meeting-minutes/` (or paste the answers in chat), then `/ba-next`.
   - **Gates:** review the files listed, then `/ba-approve <SUBJECT> <GATE>` or `/ba-changes <SUBJECT> <GATE> <what to change>`. The gates come in this order:
     - GATE-02 (overview, BA): requirements and NFRs, glossary, objects, workflows, use cases as functions with the permission matrix, business rules, company conventions;
     - GATE-09 (technical baseline, SA);
     - then per use case: GATE-03, GATE-04 and GATE-05 (BA), GATE-06 (SA), GATE-10 (developer, code review of the tested code), GATE-07 (critical-flow test, risky use cases only), GATE-08 (user guide).
   - **Questions an agent can't answer alone:** Claude asks you in the session; your answer is recorded with you as its source.
   - **Defects only a human can resolve** (spec gaps, environment problems, a defect still failing after 3 fix attempts): decide or fix, then tell Claude.
4. `/ba-status` shows where everything stands at any time.
5. Ask Claude to **publish the SRS** whenever you want the specification in the company format: `ba-ai/srs/SRS.md`, plus one page per node of the company documentation tree. Ask for Word and Claude converts it with the docx skill.

## Commands

| Command | Does |
|---|---|
| `/ba-status` | Where things stand, what waits for you |
| `/ba-next [UC\|EPIC]` | Resume from exactly where it stopped, through every phase |
| `/ba-spec [UC\|EPIC]` | Run only the Spec Engine |
| `/ba-approve <SUBJECT> <GATE> [comment]` | Approve a gate |
| `/ba-changes <SUBJECT> <GATE> <comments>` | Request changes |

Only you can approve. Your typed `/ba-approve` is recorded by a hook before Claude sees it, and Claude is blocked from writing decision records. If the hook ever fails, record the decision yourself in a terminal: `tools/ba decide approve <SUBJECT> <GATE> "comment"`.

## Product repositories

The technical baseline registers the product repositories in `ba-ai/workflow/repositories.yaml`, next to this folder (`../<name>`). They stay separate and are never merged. The coding agent creates a repository that doesn't exist yet. Each use case gets its own git worktree, `<repo>-worktrees/<UC>/` on branch `ba/<UC>-<slug>`, so several can be coded in parallel. Nothing is pushed, merged or opened as a pull request unless you ask. After you merge a delivered use case, remove its worktree with `git worktree remove`. UI tests and user-guide screenshots use Playwright installed in the frontend repository.

So Claude Code can reach them, add their paths and their `-worktrees` folders to `permissions.additionalDirectories` in `.claude/settings.json`. That file is protected, so do it in maintenance mode (below).

## Layout

```text
CLAUDE.md            orchestrator rules (the main Claude session)
.claude/agents/      elicitation, overview-analysis, technical-baseline, planning, ui, technical-analysis,
                     spec, coding, qa, documentation and review agents
.claude/skills/      commands (/ba-*) and the BA method skills used by agents
.claude/settings.json  gate hooks + permissions
company-standards/   the company's SRS conventions (field controls, messages, list behaviour, common use cases,
                     common rules, glossary, email templates), adapted per project by the overview agent
tools/ba             bookkeeping CLI (state, IDs, gates, validation, graph, planning, coding, views, publish)
tools/schemas/       catalog and artifact schemas
tools/tests/         regression tests (.venv/bin/python -m unittest discover -s tools/tests)
tools/patches/       protected-file changes waiting for maintenance mode
ba-ai/               all workflow artifacts (your project data), in the company SRS structure:
  input-management/          meeting minutes, user requirements, reference documents, elicitation
  high-level-requirements/   overview, actors, applications, objects, processes and workflows, rules,
                             use cases (functions), integrations, site maps, generated diagrams and matrix
  functional-requirements/   use case specifications, mockup screens and prototypes, common use cases
  agile-project/             backlog (epics) and user stories
  non-functional-requirements/  generated view of the NFRs
  other-requirements/        field controls, message configuration, list behaviour
  appendices/                message list, email templates, glossary
  technical/ qa/ user-guide/ the technical design and delivery beyond the SRS
  srs/                       the published SRS (tools/ba publish)
docs/                master spec + implementation decisions
```

## Writing inputs by hand

You can still write the overview, technical baseline or backlog yourself instead of letting the agents draft them:
- Catalog items are added with `tools/ba catalog add <catalog> --data '{…}'` (or `--file` with one item or a list), which allocates the IDs. Required fields are in `tools/schemas/catalogs.yaml`.
- The backlog and its user stories are written with `tools/ba backlog plan --file <plan.yaml>`.
- Documents need the frontmatter and headings listed in `tools/schemas/artifacts.yaml`. `tools/ba validate` reports what is missing.
- Once GATE-02 or GATE-09 is approved, the steps before it count as done.
- Every catalog has a readable view next to it, `<name>.view.md`, and `tools/ba sync` also generates the company views: object relationship diagram, state transition, use case diagram, permission matrix, workflows, one page per object, screen and epic, and the non-functional requirements. The YAML stays the source of truth.

## Upgrading a workspace from the earlier layout

`tools/ba migrate --dry-run` lists what would move; `tools/ba migrate` moves the files to the company folders and rewrites the paths they record (addendum D-63). Gate approvals given under the old paths no longer hold, so the BA reviews the regenerated artifacts again. Then `/ba-next`.

## Maintaining the kit

Hook-protected files — `.claude/settings.json`, `tools/ba`, `tools/ba_cli/hooks.py`, `tools/ba_cli/gates.py` — can only be edited by Claude when you start it with `BA_MAINTENANCE=1 claude`. Everything else (skills, schemas, agents, company standards) can be improved normally (Rule 8).

**Pending:** [tools/patches/d13-coding-hook.md](tools/patches/d13-coding-hook.md) switches on the hook that blocks product-repository writes before GATE-05, GATE-06 and GATE-09 are approved (D-13). Start a maintenance session and ask Claude to apply it.
