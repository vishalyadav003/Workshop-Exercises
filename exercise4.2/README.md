# Exercise 4.2 — Service Desk Performance Visualization

## Contents

- `analyze_performance.py`: modular CSV cleaning, descriptive statistics, and five Matplotlib chart exports.
- `tickets.csv`: 36 synthetic tickets, including open records with unavailable resolution durations.
- `INTERPRETATION.md`: concise guide to reading results and their limitations.
- `output/`: generated PNGs after running the script.

## Setup and run

```powershell
python -m pip install pandas matplotlib
python analyze_performance.py
```

## Interactive dashboard

Run `python app.py` and open <http://localhost:5402>. The HTML, CSS and JavaScript
dashboard loads the sample CSV by default, supports uploaded CSV files and live
filters, and exports the currently filtered records. The server uses Python's
standard library; pandas and Matplotlib are only needed for the analysis script.

Use `python analyze_performance.py --input another_export.csv --output charts` to select different paths. Required fields are `ticket_id`, `category`, `priority`, `opened_date`, `resolution_hours`, and `status`. Dates and numeric values are coerced; rows with unusable IDs, categories, priorities, dates, or statuses, negative durations, and duplicate IDs after the first are removed. Blank resolution time is allowed and excluded only from duration-based analysis. Unknown priority labels remain usable for the other analyses but do not appear in the coded-priority scatter plot.

The script prints the current mean, median, and maximum duration and data-quality counts. It creates `tickets_by_category.png`, `resolution_time_distribution.png`, `weekly_ticket_volume.png`, `priority_vs_resolution.png`, and `resolution_by_status.png` in the output folder.
