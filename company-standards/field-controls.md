# Common Field Controls — company standard

Source: the "Common Field Controls" workbook embedded in the company SRS template. The template recommends referring to the development team's component library when there is one; otherwise these rules apply.

A screen's component table names one of these controls, or one of the *Other component types* below, in its **Component Type** column. Unless a component's Description says otherwise, the control's attributes and behaviours apply.

## Common Field Controls

| Control | Also written as | Attributes | Format and Behaviors |
|---|---|---|---|
| Free Text (Single Line of Text) | Single Line of Text; Text box; Search box | • Allows all character types.<br>• Max length: 255 characters. | • No line break.<br>• Accepts ASCII characters only; no special character types (e.g. Unicode).<br>• View mode: content on a single line.<br>• Modify mode: input field the user types in.<br>• Includes all text fields and standard search boxes. |
| Text Area (Multi lines of text) | Multi lines of text; Multi-line text | • Allows all character types.<br>• Max length: 65,536 characters. | • Accepts ASCII characters only; no special character types (e.g. Unicode).<br>• View mode: content on several lines.<br>• Modify mode: text area the user types in; at most 10 lines, then a vertical scrollbar. |
| Rich Text | Rich text editor | N/A. | Text editor: refer to TinyMCE. |
| Label | Read-only text | N/A. | • Text longer than the display box (width) wraps to the next line, keeping whole words.<br>• On a one-line display, text longer than the box is cut and "…" replaces the missing characters.<br>• Text longer than the display box (height) is cut at the end of the last line, with "…".<br>• A tooltip on hover shows the full text. |
| Numeric / Number | Number; Numeric | • Numeric characters only.<br>• Unless the description says otherwise: integers equal to or greater than 0.<br>• Max length: 255 characters. | • No line break.<br>• View mode: a single line shown as a number.<br>• Modify mode: input field accepting number characters only. |
| Single Choice Dropdown List | Dropdown list; Dropdown; Select | • Placeholder: "Please select item".<br>• Value list defined for each case. | • Modify mode:<br>  – no duplicate entries;<br>  – focuses and shows the selected value when opened;<br>  – one blank entry on top; choosing it shows the placeholder "Please select item";<br>  – shows 5 entries, then a vertical scrollbar;<br>  – sorted alphabetically;<br>  – text longer than the box is cut at the end of the first line with "…", and a tooltip shows the full text;<br>  – typing in the field filters the entries by prefix.<br>• View mode: only the selected item or the placeholder. |
| Multiple Choice Dropdown List | Multi-select dropdown | • Placeholder: "Please select item".<br>• Value list defined for each case. | • Modify mode:<br>  – the user selects several items;<br>  – with nothing selected the field shows "Please select item";<br>  – shows 5 entries, then a vertical scrollbar;<br>  – sorted alphabetically;<br>  – selected values are separated by "," (value 1, value 2); text longer than the field ends in "…";<br>  – a tooltip shows the full text; typing filters the entries by prefix.<br>• View mode: the selected items, one per line.<br>• Usually used as a filter on a list. |
| Single/Multiple Choice Dropdown with Fill In | Dropdown with fill in | • Placeholder: "Please select item".<br>• Value list defined for each case. | • Like the single or multiple choice dropdown list, but the last item is an input field for a new value.<br>• The new value is not added to the value list; it is used only for the current record. |
| Checkbox | Check box | Value defined for each case. | • Modify mode: a single checkbox the user selects or clears.<br>• View mode: only the selected item. |
| Multiple Choice Checkboxes | Checkbox list | Value list defined for each case. | • Modify mode: the user selects or clears one or several items; an "All" option on top selects or clears every item.<br>• View mode: the selected items, one per line. |
| Checkbox with Fill In | — | Value list defined for each case. | • Like Checkbox, but the last item is an input field for a new value.<br>• The new value is not added to the value list; it is used only for the current record. |
| Single Choice Radio Buttons | Radio buttons; Radio group | Value list defined for each case. | • Modify mode: the user selects one item from the value list.<br>• View mode: the selected item as a single line of text. |
| Single Choice Radio Buttons with Fill In | Radio buttons with fill in | Value list defined for each case. | • Like Single Choice Radio Buttons, but the last item is an input field for a new value.<br>• The new value is not added to the value list; it is used only for the current record.<br>• View mode: the selected item as a single line of text. |
| Date Time – Date and Time | Date time; Date and time picker | N/A. | • 24-hour time.<br>• Modify mode: "/" and ":" are fixed; the user changes only DD, MM, YYYY, hh, mm and ss; default value: current date and time; integers only.<br>• View mode: date and time on a single line. |
| Date Time – Date Only | Date; Date picker | N/A. | • Format: DD/MM/YYYY.<br>• Modify mode: a date picker; default value: current date; integers only.<br>• View mode: the date on a single line. |
| Date Time – Time Only | Time; Time picker | N/A. | • Format: hh:mm:ss, 24-hour.<br>• Modify mode: a time picker; default value: current time; integers only.<br>• View mode: the time on a single line. |
| Single Choice User | User picker | • Allows all character types.<br>• Max length: 255 characters. | • Modify mode:<br>  – suggestions from the data source from the first typed character;<br>  – unless the description says otherwise, shows the User Name from the system's user list;<br>  – at most 5 suggestions, then a vertical scrollbar;<br>  – active users only; an unknown user shows the inline error "User does not exist." and is not shown in user format;<br>  – the selected user has an (x) button to remove it.<br>• View mode: the User Name as text. |
| Multiple Choice User | Multi user picker | Allows all character types. | • Like Single Choice User, but several users can be entered.<br>• Selected users are separated by "," (user 1, user 2); text longer than the field ends in "…". |
| Filter Date Range | Date range filter | N/A. | • Filters a list by a date range.<br>• Options: Today, Last 7 days, Last 30 days, Custom Date Range (From Date and To Date; From Date cannot be later than To Date).<br>• After a choice, the field shows "From Date - To Date".<br>• A custom range with only one of the two dates counts as blank. |

## Other component types

Components that are not input fields. Their Description in the component table says what they show or do.

| Component type | Use |
|---|---|
| Button | Starts an action. Its Description says when it is enabled and refers to the use case it triggers (`Refer to UC-…`). |
| Link | Opens another screen or record. |
| Column Header | A column of a list. Its Description says where the value comes from and how it is shown. |
| Table | A list of records, following the list behaviour conventions. |
| Search Bar | Free-text search on a list, following the search component conventions. |
| Filter | A filter on a list (often a dropdown or a Filter Date Range). |
| Pagination | Paging of a list, following the pagination conventions. |
| Tab | Switches between views of the same screen. |
| Section | Groups components; its Description lists what it holds. |
| Dialog | A modal dialog (confirmation, short input). |
| Message | An in-page message area (alert, error summary, banner). |
| Toolbar | Formatting or action buttons attached to a field. |
| Icon | An icon with a meaning, e.g. a status icon. |
| Image | A picture or illustration. |
