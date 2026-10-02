# Company SRS standards

The company's System Requirement Specification conventions, taken from the SRS template
(`test_input/Customer Name_Project Name_System Requirement Specification_v0.9 (3).docx`) and its embedded
"Common Field Controls" workbook. The BA team owns this folder.

These files are **kit defaults, not project data**. During the overview step (Phase 3) the overview agent
adapts them for the product, following `.claude/skills/adapt-company-standards/SKILL.md`. Each adapted copy then lives in `ba-ai/` and the BA approves it at GATE-02 (addendum D-53).

| File | Becomes, per project | Used by |
|---|---|---|
| [field-controls.md](field-controls.md) | `ba-ai/other-requirements/field-controls.md` | Screen component tables (the *Component Type* column), prototypes, coding |
| [message-configuration.md](message-configuration.md) | `ba-ai/other-requirements/message-configuration.md` | The message catalog, screens, prototypes, coding |
| [list-behaviour.md](list-behaviour.md) | `ba-ai/other-requirements/list-behaviour.md` | List screens: columns, pagination, search, bulk action |
| [common-use-cases.yaml](common-use-cases.yaml) | `ba-ai/functional-requirements/common-use-cases.yaml` (CMUC-NNN) | "Manage X" use cases, which follow these and specify only what differs (D-50) |
| [common-business-rules.yaml](common-business-rules.yaml) | Items of `kind: COMMON` in `ba-ai/high-level-requirements/business-rules.yaml` | Step rules that refer to them, e.g. the audit trail |
| [messages.yaml](messages.yaml) | Items in `ba-ai/appendices/messages.yaml` | Screens and step rules reuse them before creating new ones |
| [glossary.yaml](glossary.yaml) | Items in `ba-ai/appendices/glossary.yaml` | Every agent, for consistent wording; the SRS Abbreviations table |
| [email-templates.md](email-templates.md) | Conventions only | The email-template catalog (ET-NNN) |

## Notation

Every BA document follows the company notation (addendum D-55):

| Notation | Meaning | Example |
|---|---|---|
| `[Field]` | A field or attribute | [Start date] |
| `{Object}` | A record of an object | {Leave Request} |
| `"Value"` | A literal value | "Pending approval" |
| `<Special Value>` | A value the system supplies | <Today>, <Current User>, <Current Date Time> |
| `<<Placeholder>>` | A value filled into an email template | <<Employee Name>> |
| `(n)` | Step *n* of an activities flow | (4) |
| `O` / `O*` / `O**` / `X` | Permission matrix: allowed / on own items / within a scope / not allowed | O** |

Fixed labels:

- Step rules are titled `<Type> Rules`, e.g. "Screen Displaying Rules", "Validating Rules", "Submitting Rules".
- A screen is named `<Name> screen`, e.g. "Leave request form screen".
- An email template is named `Sending email to <recipient> after <event>`.
- A use case is named verb + object, e.g. "Submit leave request".

IDs follow the kit's convention, not Word numbering: `UC-007`, `BR-012`, `SCR-003`, `IEM-002`, `ET-001`, `CMUC-002`. The tool allocates them and never renumbers them (addendum D-14).

## Changes from the template

The template's flaws were not copied:

- The permission legend uses `O**` without defining it. Here it means "allowed within a scope", and every `O**` states its scope rule.
- The Site Map appears twice in the template; the SRS publication has it once, under High Level Requirements.
- Word cross-references ("Error! Reference source not found.") are replaced by stable IDs.
- The field-controls workbook lists 21 rows for 19 controls. The second "Rich text" row (which repeats the single-line text rules) and the second "Checkbox with Fill In" row are dropped. "Single Choice Radio Buttons with Fill In" got the fill-in behaviour its siblings have.
- CMUC 4 ("Update Item") said it opens the screen "at the new mode" and "will create a new item". It now opens the edit mode and updates the item.
- The template's Informing Message and Success Dialog overlap. Here SCD is the success dialog and INF is an informing or warning message that does not block the user.
- Sample texts that did not match their headings (e.g. a "submit" confirmation reused for "accept") are not carried over.
