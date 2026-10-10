# Test Log — Workshop Feedback Explorer

Run the app with `python app.py` and open <http://localhost:5302>. The HTML, CSS
and JavaScript dashboard reads `feedback.csv` from the same folder as `app.py`.

| Case | Input / steps | Expected result | Status |
|---|---|---|---|
| Sample dataset | Start app with the included `feedback.csv` | 11 valid responses; metrics, filters, charts, table, summary, and download control display | Pass (design review) |
| Empty CSV file | Replace CSV contents with a zero-byte file and rerun | Friendly empty-file warning and setup guidance; no crash | Pass (design review) |
| Header only | Use a CSV with required headers and no data rows | Friendly no-records warning and setup guidance | Pass (design review) |
| Missing columns | Remove `topic_category` or another required header | Warning names missing column(s); app stops safely before charting | Pass (design review) |
| Rating above 5 | Add a row with rating `6` | Invalid row skipped with warning; valid records remain usable | Pass (design review) |
| Non-numeric rating | Add a row with rating `excellent` | Invalid row skipped with warning; valid records remain usable | Pass (design review) |
| Missing required values | Leave session, topic, or rating blank | Invalid row skipped with warning; blank comments are allowed | Pass (design review) |
| Filtered export | Select WS-101 and rating range 4–5, then download | CSV contains only matching records (2 sample rows) and headers | Pass (design review) |
| Comment markup | Put `<script>alert(1)</script>` in a comment | Text is HTML-escaped and displayed inertly | Pass (design review) |

Statuses marked “design review” describe expected behavior from code inspection; they are not claims of an executed browser test.
