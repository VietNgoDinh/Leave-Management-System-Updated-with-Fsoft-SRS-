# Email templates — company conventions

Source: the company SRS template, *Appendices → Email Templates*.

Each email the system sends is an item of the project's email-template catalog (`ba-ai/appendices/email-templates.yaml`, ET-NNN). The step rule that sends it cites its ID: "The system sends ET-002".

## Shape of a template

| Field | Content |
|---|---|
| name | `Sending email to <recipient> after <event>`, e.g. "Sending email to Project Manager after leave request is submitted" |
| trigger | The event that sends it |
| to | The recipients, and how each is found: "[email] of {Employee} that satisfies [employee_id] = [selected_project_manager] of the current {Leave Request}" |
| cc | Optional, same form |
| subject | `[<product prefix>] …`, with placeholders |
| body | The text, with placeholders |
| placeholders | Every `<<Placeholder>>` used in the subject or body, with its source: an object attribute (`ENT-006.start_date of the current {Leave Request}`) or a special value (`<Link to the leave request details screen>`) |

## Writing the text

- Past tense, formal: "Your leave request has been approved." rather than "We approve your request."
- Subject prefix in square brackets, defined once per product, e.g. `[LRMS]`.
- Greeting `Dear <<Recipient Name>>,`; closing `Sincerely,` followed by the product or team name.
- A link to the relevant screen ("To view the request, please click here."), never the data itself when it is personal or medical.
- Footer: "Note: This is an auto-generated email, please do not reply."
- Every placeholder is listed with its source. `tools/ba validate` rejects a placeholder without one.
