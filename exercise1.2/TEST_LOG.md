# Edge-case test log

## Execution status

The CLI recovery and validation cases below remain manual checks. The dashboard booking flow was exercised through its request handlers with a temporary JSON store, leaving the sample `data/bookings.json` unchanged. Python compilation and JavaScript syntax checks passed. A live browser session could not be started in this sandbox because local socket binding is restricted.

| Executed dashboard check | Result |
|---|---|
| Load resource summary from temporary JSON data | Passed |
| Book an adjacent non-overlapping slot | Passed |
| Submit an overlapping slot | Conflict returned and wait-list entry persisted |
| Cancel an active booking | Passed; cancelled status retained |
| Export the daily CSV | Passed, including attachment filename |
| Generate usage report | Passed; saved in the date-organized report folder |

| Case | Procedure | Expected result |
|---|---|---|
| Missing data file | Temporarily move `data/bookings.json`, then start the app. | Notice says the file is missing; an empty store and starter resources are created and persisted. |
| Empty data file | Replace the JSON file with zero bytes, then start the app. | Notice says the file was empty; app initializes the starter catalogue and writes valid JSON. |
| Corrupted JSON | Save a copy, replace contents with `{ invalid`, then start the app. | Recovery warning; original is copied to `bookings.json.corrupt` when possible; app starts with clean starter resources. |
| Overlap | With sample data loaded, book `S-101` on `2026-10-12` from `10:00` to `11:00`. | Conflict with DEMO1001 is detected; no active booking is created, and the request is automatically added to the wait-list. |
| Adjacent slots | Book `S-101` on `2026-10-12` from `10:30` to `11:30`. | Allowed because intervals are half-open and DEMO1001 ends at 10:30. |
| Wait-list | Submit the overlapping request and inspect `data/bookings.json`. | New wait-list record is persisted automatically; there is no overlapping active booking. |
| Cancellation and queue | Cancel DEMO1001 after creating a matching wait-list entry. | Booking is retained with `cancelled` status; CLI identifies the oldest overlapping wait-list request for staff follow-up. |
| Invalid date/time | Try `2026-02-30`, `9:00`, equal start/end, or an end before start. | Clear validation error; no booking is stored. |

The sample dataset already demonstrates an active schedule and a cancelled record. No third-party packages are required.
