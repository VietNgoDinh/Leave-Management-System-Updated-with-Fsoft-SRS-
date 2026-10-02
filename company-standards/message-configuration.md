# Common Messages Configuration — company standard

Source: the company SRS template, *Other Requirements → Common Messages Configuration* and *Appendices → Messages List*.

Every message the user can see is an item of the project's message catalog (`ba-ai/appendices/messages.yaml`). Its code shows its type. Screens and step rules cite the code and show the text next to it.

## Common Messages Configuration

| Message type | Code | Remarks |
|---|---|---|
| In-line Error Message | IEM-NNN | • Red italic text, below the field in error.<br>• The field is highlighted in red.<br>• Shown when the field fails validation. |
| In-field Error Message | IEM-NNN (alternative presentation) | Used only when the project chooses it instead of the in-line presentation.<br>• Red italic text inside the field, covering its content.<br>• Selecting the field hides the message and shows the content again.<br>• The field is highlighted in red. |
| Error Message | EMSG-NNN | • Pop-up with the title "Error Message", the message and a "Close" button.<br>• Clicking outside the pop-up does not close it; only "Close" does.<br>• After closing, the user is back on the current screen.<br>• Shown when an action fails. |
| Confirmation Message | CFD-NNN | • Pop-up with the title "Confirmation", the message and two buttons, "Yes" and "No" (or "OK" and "Cancel").<br>• Clicking outside the pop-up does not close it.<br>• Yes/OK closes the pop-up and continues the action; No/Cancel closes it and cancels the action. Each step rule that uses one says what follows. |
| Success Dialog | SCD-NNN | • Dialog with the title "Success", the message and an "OK" button.<br>• Closes automatically after 5 seconds.<br>• Shown after the system completed an action. |
| Informing Message | INF-NNN | • Information or warning that does not block the user, e.g. "This request exceeds your entitlement".<br>• Shown in the page, or as a pop-up that disappears after 10 seconds, as the screen description states. |
| Standard platform message | — | A message the platform shows by itself (browser, operating system). Not catalogued. |

## Writing messages

- One message per meaning. Reuse an existing message before creating a new one (`tools/ba find <words>`).
- Say what happened and what to do next: "Enter a start date in the future or in the current month."
- A message with a variable part uses a placeholder in braces: "Leave type "{name}" was created."
- Confirmation messages are questions: "Are you sure you want to delete this item?"
