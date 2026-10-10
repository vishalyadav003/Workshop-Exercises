# Service Desk Performance: Interpretation Guide

## What to look for

The category bar chart shows where the recorded workload is concentrated. A larger bar means more tickets in this sample, not necessarily poorer service or greater effort per ticket. Compare category totals before deciding where capacity might be needed, and consider ticket complexity as well as volume.

The resolution-time histogram shows the shape and spread of durations among records with a numeric resolution time. A long right tail means a small number of tickets took much longer than the typical case; the mean is sensitive to those values, while the median gives the middle observation. Missing resolution times are retained for workload counts but omitted from duration statistics.

The weekly line chart counts tickets by their opened date. Peaks can help identify periods for further investigation, but this sample does not explain why a peak occurred. Check whether the date range is complete and compare with staffing and calendar context before making operational conclusions.

The priority scatter chart places priority on an ordered code axis (Low through Urgent) and displays individual duration observations. The codes express order, not equal numeric spacing. The plot is descriptive and cannot establish that priority caused a ticket to take longer or shorter: complexity, assignment practices, service targets, and staffing may differ across priority groups.

The status comparison describes recorded durations associated with current Open and Resolved/Closed status. It is not a causal comparison. In a real snapshot, open tickets are often still in progress, so their elapsed time may be incomplete (right-censored), while resolved tickets have a completed duration. This sample leaves open-ticket resolution hours blank, so those rows appear in counts but cannot contribute to the duration comparison. Do not interpret a missing open-ticket duration as zero.

## Reading this sample responsibly

The provided CSV is synthetic and intentionally small. Use the mean, median, and maximum printed by the script as summary descriptions of the available numeric durations, not as service-level guarantees. Validate definitions (especially whether hours mean elapsed or business hours), date coverage, duplicate handling, and status labels before applying the script to an operational export. The cleaning summary reports retained and excluded records so changes in data quality remain visible.

## Run and outputs

Install `pandas` and `matplotlib`, then run `python analyze_performance.py` in this folder. The script reads `tickets.csv` by default and creates five PNG charts inside `output/`. Supply alternate paths with `--input` and `--output`. The console summary is recalculated from the CSV on each run.
