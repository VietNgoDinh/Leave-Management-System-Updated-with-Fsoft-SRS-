---
name: extract-business-rules
description: BA workflow Phase 3 step 3.3 — business rules with stable BR IDs, each a POLICY (a constraint the business imposes) or a COMMON rule (a procedure several use cases apply by reference), traced to its source requirement, entities and use cases (ba-ai/high-level-requirements/business-rules.yaml). Used by overview-analysis-agent; not for direct use.
user-invocable: false
---

# Step 3.3 — Business Rules (policy and common)

| | |
|---|---|
| Input | Requirements, elicitation summary (decisions), the data model, `company-standards/common-business-rules.yaml` |
| Output | `high-level-requirements/business-rules.yaml` (BR) |
| Consumers | The BA at GATE-02, screen design (5.2), the use case behaviour (5.4: step rules apply them), acceptance criteria (5.7), QA (8.1); the SRS (Common Business Rule) |

Business rules come on two levels (D-47):
- **BR-NNN, here:** rules shared by use cases, approved at GATE-02 before any UI exists, so wrong business logic is caught early. They are published as the SRS's *Common Business Rules*.
- **Step rules** (`<UC>-BR-nn`), written per use case at step 5.4: what the system does at one step of the flow ("Validating Rules", "Submitting Rules"). A step rule applies BR-NNN rules by citing them. You don't write step rules here.

## Procedure

1. Each BR has a `kind`:
   - **POLICY:** a constraint or calculation the business imposes: eligibility, limits, deadlines, approvals, calculations, visibility. Not a UI preference or a technical choice.
   - **COMMON:** a procedure several use cases apply by reference, such as logging the audit trail (the company's CBR). Start from `company-standards/common-business-rules.yaml` (`adapt-company-standards`).
2. One rule per constraint, stated so it can be tested: who, when, what limit, and what happens on violation.
3. Reuse first (`tools/ba find <keywords>`), then:
   ```
   tools/ba catalog add business-rules --data '{
     "name": "Leave only on working days", "kind": "POLICY", "description": "...testable statement...",
     "source": "REQ-003 (URS §4.1)", "applies_to": "Leave Request submission",
     "requirements": ["REQ-003"], "related_entities": ["ENT-005"]}'
   ```
   Add `related_use_cases` once the use cases exist (`define-use-cases` links them back).
4. A rule the material implies but doesn't settle (the limit value, the exception, the violation behaviour) gets recorded with the known part. The unknown part becomes an open question related to the BR (BUSINESS, or COMPLIANCE for regulatory rules).
5. Never merge two rules because they share a sentence in the source. Never split one rule into several because it has several examples.
6. **A project upgraded from an earlier kit version:** its rules are policy rules; set `kind: POLICY` on each (`tools/ba catalog update BR-… --data '{"kind": "POLICY"}'`), and add the common rules the product needs.

## Checklist

- [ ] Every rule has a kind and cites a REQ or a recorded stakeholder decision in `source`.
- [ ] Every policy rule names what happens on violation (block, warn, flag for review), or has an open question for it.
- [ ] No technical or UI rule here. Those belong in the baseline, the Other Requirements or the screen design.
