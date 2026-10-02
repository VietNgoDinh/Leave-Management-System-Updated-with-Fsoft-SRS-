---
name: elicit-requirements
description: BA workflow Phase 2 steps 2.1–2.3 and 2.6 — understand current and future need, gap analysis, and consolidation of stakeholder material into typed requirements (functional and non-functional), the glossary, assumptions and the elicitation summary (ba-ai/input-management/elicitation/elicitation-summary.md). Used by elicitation-agent; not for direct use.
user-invocable: false
---

# Phase 2 — Requirement Elicitation (2.1, 2.2, 2.3, 2.6)

| | |
|---|---|
| Input | Everything in `ba-ai/input-management/user-requirements/` (the client's requirement documents, briefs, emails), `meeting-minutes/` and `reference-documents/` (standards, style guides, external-system documents); context package `ba-ai/workflow/context/ELICITATION.yaml` |
| Output | `ba-ai/input-management/elicitation/elicitation-summary.md`; `requirements.yaml` (REQ, typed FUNCTIONAL or NON_FUNCTIONAL); `assumptions.yaml` (ASM); `ba-ai/appendices/glossary.yaml` (TERM); answers on `open-questions.yaml` |
| Consumers | Overview analysis (Phase 3), the BA at GATE-02 (requirements, NFRs and glossary are gate content), clarification questions (2.4), the SRS publication (Introduction, User Requirements, Non-Functional Requirements, Glossary) |

## Procedure

1. **Read every source.** For a `.docx`, extract the text, e.g. `textutil -convert txt -stdout <file>` on macOS, or `unzip -p <file> word/document.xml | sed -e 's/<[^>]*>/ /g'`. List each source with its date and author in *Sources*. Reference documents are context (standards, the company style guide, an external system's interface); they don't create requirements on their own.
2. **2.1 Current need (AS-IS):** the current problem, affected users, pain points, existing process, limitations, reason for change. Only what the sources say.
3. **2.2 Future need (TO-BE):** desired outcome, future process, expected user and system behaviour, business goals.
4. **2.3 Gap analysis:** a table of process, system, data, integration and policy gaps, plus *unresolved decisions*. Each unresolved decision becomes a clarification question (step 2.4, `generate-clarification-questions`).
5. **Requirements**, one REQ per distinct need, in stakeholder language, testable later. Reuse first: `tools/ba find <keywords>`. Every requirement has a `type` (D-54):
   - **FUNCTIONAL** — something the system does for an actor.
   - **NON_FUNCTIONAL** — a quality or constraint. It needs a `category` and measurable `criteria` (the company SRS's "Variables / Criteria"):

     | category | Company SRS section | Example criteria |
     |---|---|---|
     | PERFORMANCE, SCALABILITY, PLATFORM | Performance Requirements | "95% of submissions answered within 2 s at 3,000 concurrent users"; "Windows and macOS latest + 2 versions; phone, tablet, desktop" |
     | SAFETY | Safety Requirements | authenticity, privacy, encryption |
     | SECURITY | Security Requirements | authentication mode, session lifetime, attack detection |
     | USABILITY, ACCESSIBILITY, INTERNATIONALISATION | Software Quality Attributes | "WCAG 2.1 AA"; "English only" |
     | AVAILABILITY, RELIABILITY, ACCURACY, COMPLIANCE, CONSTRAINT | Software Quality Attributes | "99.5% monthly availability"; "GDPR"; release timeline |

     When the source states the quality but not how to measure it ("fast", "under heavy load"), write the criteria you can, and add an open question for the measurable target. Never invent a number.
   ```
   tools/ba catalog add requirements --data '{"name": "...", "description": "...", "type": "NON_FUNCTIONAL",
     "category": "PERFORMANCE", "criteria": "...", "source": "<file> §<section> (or meeting-minutes/<file>)", "priority": "HIGH"}'
   ```
   Priority comes from the source (must/should/could). If the source gives none, use MEDIUM and say so in *Decisions* as an assumption.
6. **Glossary** (D-54). First add the company defaults (abbreviations and notation) that the product's documents will use: `tools/ba catalog add glossary --file company-standards/glossary.yaml` (skip the ones already there). Then add the product's own terms — the business nouns, roles and statuses the sources use — with the definition the sources give: `tools/ba catalog add glossary --data '{"term": "Leave entitlement", "kind": "TERM", "definition": "..."}'`. Kinds: TERM, ABBREVIATION, NOTATION. Every later agent uses these words, and GATE-08 checks the user guide against them.
7. **Assumptions.** Where a reasonable reading fills a small gap, add an assumption the BA can confirm, instead of a requirement:
   `tools/ba catalog add assumptions --data '{"statement": "...", "reason": "...", "status": "OPEN", "related": ["REQ-..."]}'`
8. **2.6 Consolidation** (action REGENERATE, new meeting minutes):
   - For each open question the notes answer: `tools/ba catalog update Q-... --data '{"status": "ANSWERED", "answer": "...", "answer_source": "meeting-minutes/<file>"}'`.
   - New needs → new REQs. Changed needs → update the REQ and append the meeting to its `source`.
   - Confirmed or rejected assumptions → `status: CONFIRMED|REJECTED`.
   - Record each stakeholder decision in *Decisions*, with its source.
9. **A project upgraded from an earlier kit version** already has requirements, often amended by the BA at GATE-02. Keep their IDs and their BA-decided wording. Only add what is missing: the `type` of each one (and the category and criteria of the NON_FUNCTIONAL ones), the glossary, and the elicitation summary if there is none.
10. Write the summary (template below), then `tools/ba stamp ba-ai/input-management/elicitation/elicitation-summary.md` and `tools/ba validate`.

## Template

````markdown
---
id: ELICITATION
artifact_type: elicitation-summary
title: <product> — Elicitation Summary
status: DRAFT
version: 1
baseline: TO_BE
origin: AI
open_questions: [Q-..., ...]
assumptions: [ASM-..., ...]
updated_at: ""
---
# <product> — Elicitation Summary

## Sources
| Source | Kind (user requirement / meeting minutes / reference document) | Date | Author / stakeholder |
|---|---|---|---|

## Current Need
<AS-IS: problem, affected users, pain points, existing process, limitations, reason for change — cite sources>

## Future Need
<TO-BE: desired outcome, future process, expected user/system behaviour, business goals>

## Gap Analysis
| Gap | Type (process/system/data/integration/policy) | AS-IS | TO-BE | Requirement / question |
|---|---|---|---|---|

## Clarification Questions
<Open questions grouped by stakeholder; blocking ones first. IDs only — the text lives in open-questions.yaml>

## Decisions
| Decision | Source |
|---|---|

## Requirements Summary
| REQ | Name | Type | Priority | Source |
|---|---|---|---|---|
````

## Checklist

- [ ] Every REQ cites a source document; none comes from your own preference.
- [ ] Every REQ has a type; every NON_FUNCTIONAL one has a category and measurable criteria, or an open question for them.
- [ ] The glossary holds the notation and abbreviations the documents use and the product's own terms.
- [ ] AS-IS and TO-BE are in separate sections (Rule 2).
- [ ] Every unresolved decision is an open question, not a requirement.
- [ ] No question is ANSWERED without an `answer_source` pointing at `user-requirements/` or `meeting-minutes/`.
