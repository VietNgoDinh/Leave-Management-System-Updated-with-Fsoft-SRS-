---
name: build-data-model
description: BA workflow Phase 3 steps 3.4 and 3.5 — the objects of the data model (entities, attributes with their constraints, identifiers, relationships, cardinality, ownership) with each stateful object's lifecycle as its state model (ba-ai/high-level-requirements/objects.yaml). Used by overview-analysis-agent; not for direct use.
user-invocable: false
---

# Steps 3.4 and 3.5 — Objects (data model) and State Transitions

| | |
|---|---|
| Input | Requirements, elicitation summary, actors, applications |
| Output | `high-level-requirements/objects.yaml` (ENT); each stateful object's `lifecycle` |
| Consumers | **The BA at GATE-02 — a mandatory review artifact**, read with the generated Object Relationship Diagram, State Transition and object pages; screen components (5.2), behaviour (5.4), API design (5.6), QA state-transition tests (8.1) |

The company SRS calls these *objects*; the kit keeps them as structured entities (IDs ENT-NNN) and generates the company's views from them: the Object Relationship Diagram, the State Transition diagrams and one Object specification page per object (D-59).

## Procedure

1. Find the business nouns in the requirements: things that are created, changed, approved or counted. Each becomes an object. Its `name` is the business term (as in the glossary), and its ID comes from the tool (D-14).
2. Reuse first: `tools/ba find <noun>`. Then add:
   ```
   tools/ba catalog add entities --data '{
     "name": "Leave Request", "description": "...", "owner": "<application or external system that owns it>",
     "attributes": [{"name": "request_id", "type": "identifier", "generated": "LR-<YYYY>-<5-digit sequence>"},
                    {"name": "start_date", "type": "date", "mandatory": true, "description": "..."},
                    {"name": "reason", "type": "text", "max_length": 500}],
     "relationships": [{"to": "ENT-002", "cardinality": "N:1", "description": "requested by"}]}'
   ```
   - **Attributes**: name, type (identifier, string, text, integer, decimal, date, datetime, boolean, enum, reference, file) and a description where the meaning isn't obvious. Mark the identifier. Use only attributes the material implies. A plausible but unsupported attribute becomes an open question (DATA).
   - **Constraints** (optional, D-56), when the material states them: `mandatory`, `unique` (true/false), `max_length` (a whole number), `format` (e.g. DD/MM/YYYY), `allowed_values` (a list), `default` (a value or a special value such as <Today>), `generated` (the format of a generated value). The screen components then cite them instead of restating them. Never invent a limit: an unknown one is an open question.
   - **Relationships**: `to` an existing ENT, with cardinality `1:1`, `1:N`, `N:1` or `N:M`, and a description that reads as a sentence.
   - **Ownership**: the system of record. A copy of data owned elsewhere is still an object, with that system as owner. Say so in the description.
3. **State model (3.4)**, for every object with a status:
   ```
   tools/ba catalog update ENT-... --data '{"lifecycle": {
     "states": ["DRAFT", "SUBMITTED", "APPROVED"],
     "transitions": ["(new) -> DRAFT: employee starts a request",
                     "DRAFT -> SUBMITTED: employee submits"],
     "invalid_transitions": ["APPROVED -> DRAFT: an approved request cannot be edited"]}}'
   ```
   - Every transition reads `FROM -> TO: triggering event` (`(new)` for creation).
   - The validator rejects states that aren't listed.
   - Name who or what triggers each transition: each one is performed by a use case (its `transitions`), and the permission matrix groups functions by state.
   - List the transitions the business forbids, because QA tests them.
   - An unclear transition is an open question, never a guess.
4. After the rules and use cases exist, check that every object is read or written by at least one use case. An orphan object is either out of scope (remove it) or a missing use case (an open question).

## Checklist

- [ ] Each object has an identifier, an owner and attributes, and every relationship has a cardinality.
- [ ] Constraints are stated only where the material states them.
- [ ] Each stateful object has a lifecycle with transitions and invalid transitions.
- [ ] No attribute, constraint, state or relationship is invented. The unsupported ones are open questions.
