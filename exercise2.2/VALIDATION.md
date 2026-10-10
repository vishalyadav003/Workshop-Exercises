# Exercise 2.2 — Validation and accessibility notes

## Validation test table

Run `python app.py`, open <http://localhost:5202>, and try each case in the browser. For valid cases, a confirmation should appear in the request summary with a generated request reference. Invalid cases should show a clear inline error and move keyboard focus to the first invalid field. Pass when the observed behavior matches the expected result; otherwise mark Fail and record the actual result.

| # | Inputs / action | Expected behavior | Pass/fail criteria |
|---|---|---|---|
| 1 | Submit the untouched form. | Submission is blocked; category, urgency, title, description, and contact errors are shown. Focus moves to Issue category. | Pass if no request is created, feedback is visible, and focus is on the first invalid control. |
| 2 | Valid category and urgency, title `Wi-Fi issue`, description `My laptop cannot connect to the campus network today.`, contact Email. | Form submits; safe confirmation and summary show the request ID, title, category, urgency, contact, and next step. | Pass if summary is rendered and the form resets. |
| 3 | Enter a 4-character title and a 19-character description; complete all other fields. | Both length limits are reported and submission is blocked. | Pass if both fields are identified and no summary is created. |
| 4 | Enter a title longer than 100 characters or a description longer than 2,000 characters. | Browser length limits prevent additional input; submission does not accept over-limit text. | Pass if input cannot exceed the stated maximum and invalid data is not submitted. |
| 5 | Change category select value using developer tools to an unlisted value, complete other fields, then submit. | Restricted category validation rejects the value with a clear message. | Pass if no request is created and category error is shown. |
| 6 | Complete the form but leave contact method unselected. | Submission is blocked and contact method error is shown. | Pass if the contact group is identified and no summary is created. |
| 7 | Search ticket list for `VPN`, then select `Hardware` category. | Search returns the VPN request; the category filter returns only hardware tickets; no-results text appears when there are no matches. | Pass if rows, result count, and empty state update together. |
| 8 | Use Tab/Shift+Tab and arrow keys to navigate the page and radio group; activate the skip link. | All controls can be reached and operated, focus remains visible, and skip link moves focus/viewport to main content. | Pass if no interaction requires a pointer and the active control is visibly indicated. |

## Accessibility checklist

- [x] Semantic landmarks: `header`, labeled `nav`, `main`, labeled sections, `aside`, table caption, and `footer`.
- [x] Explicit labels match control `for`/`id`; the contact choices use a `fieldset` and `legend`.
- [x] Keyboard-operable native select, input, textarea, radio, links, and button controls.
- [x] Visible `:focus-visible` styles and a keyboard-accessible “Skip to main content” link.
- [x] Inline validation is associated to controls with `aria-describedby`; status and filter counts use live regions.
- [x] Color is not the only validation/status cue; messages and text labels are present. Reduced-motion preference is respected.
- [ ] Manual check with a screen reader and at 200% zoom remains recommended before deployment.

## Implementation notes

This is a static front-end demonstration. Form submissions stay in the browser and are not persisted or sent to a helpdesk. Existing tickets are synthetic sample data. The user-entered values are inserted as text nodes; the interface does not display server errors, stack traces, or debug information. Production deployment would need an authenticated backend, server-side validation, and a real contact workflow.
