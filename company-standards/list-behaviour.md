# List behaviour — company standard

Source: the company SRS template, *Other Requirements → View Columns Display, Pagination, Search Component, Bulk Action*. The template recommends following the development team's component library or the design team's suggestions when they exist; otherwise these rules apply. Unless a screen description says otherwise, every list of the system follows them.

## View Columns Display

- Colours and fonts are as in the approved screen designs.
- Text longer than the cell is cut at the end of its first line and "…" replaces the missing characters. Hovering over the "…" shows a tooltip with the full content of the cell.
- Column headers are unsorted by default. A sortable header shows an icon for its state: unsorted, sorted ascending, sorted descending.

## Pagination

- A new search (completely new, or within the current results) refreshes the table and goes back to page 1.
- Changing the number of items per page refreshes the table and goes back to page 1.
- On page 1, the "<<" and "<" buttons are disabled. On the last page, ">>" and ">" are disabled. Otherwise every button is enabled.
- "<" and ">" move back or forward by one page; "<<" and ">>" go to the first or the last page.
- With only one page, the pagination is still shown, with that one page.
- At the far left, the pagination shows how many records match the current condition (all, searched, filtered).
- Next to the total number of pages, the user can type the page number to go to.

## Search Component

- The search field is a Free Text (Single Line of Text) field and follows that control's rules.
- Search uses "contains" logic: the system returns the records in which any displayed column contains the typed value.
- The results refresh the table, and the pagination is updated.
- A blank search value resets the list to its default view.

## Bulk Action

- The first column of the list is a checkbox column for selecting records.
- The checkbox in the column header selects every record of the current page only.
- Selected records stay selected when the user moves between pages.
- The user applies a bulk action to the selected records from a dropdown list or from bulk action buttons, depending on the system:
  - **Dropdown list:** the default entry "Bulk Action" does nothing when applied. The value list contains "Bulk Action", "Export" and "Delete".
  - **Buttons** ("Delete", "Export"): enabled only when at least one record is selected.
