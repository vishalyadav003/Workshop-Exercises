"""Analyze service desk tickets and export summary charts.

Run from this directory with: python analyze_performance.py
Optional input CSV: python analyze_performance.py --input path/to/tickets.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

REQUIRED_COLUMNS = ["ticket_id", "category", "priority", "opened_date", "resolution_hours", "status"]
PRIORITY_CODES = {"Low": 1, "Medium": 2, "High": 3, "Urgent": 4}
COLORS = {"Open": "#e69f00", "Resolved": "#0072b2"}


def load_and_clean(path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    """Load records, coerce types, and remove rows unusable for required analysis."""
    raw = pd.read_csv(path)
    missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
    df = raw[REQUIRED_COLUMNS].copy()
    before = len(df)
    df["ticket_id"] = df["ticket_id"].astype("string").str.strip()
    for col in ("category", "priority", "status"):
        df[col] = df[col].astype("string").str.strip()
    df["category"] = df["category"].replace("", pd.NA)
    df["priority"] = df["priority"].str.title().replace({"": pd.NA})
    df["status"] = df["status"].str.title().replace({"": pd.NA})
    df["opened_date"] = pd.to_datetime(df["opened_date"], errors="coerce")
    df["resolution_hours"] = pd.to_numeric(df["resolution_hours"], errors="coerce")
    df["priority_code"] = df["priority"].map(PRIORITY_CODES)
    # An absent resolution value is meaningful for an open ticket; malformed non-empty
    # values become NaN. Keep those rows for counts, but exclude them from duration plots.
    usable = df["ticket_id"].notna() & df["category"].notna() & df["priority"].notna() & df["opened_date"].notna() & df["status"].notna()
    usable &= df["resolution_hours"].isna() | df["resolution_hours"].ge(0)
    df = df.loc[usable].drop_duplicates(subset="ticket_id", keep="first").copy()
    removed = before - len(df)
    return df, {"input_rows": before, "retained_rows": len(df), "removed_or_duplicate_rows": removed,
                "missing_resolution_hours": int(df["resolution_hours"].isna().sum())}


def print_summary(df: pd.DataFrame, quality: dict[str, int]) -> pd.DataFrame:
    durations = df["resolution_hours"].dropna()
    summary = pd.DataFrame({"Metric": ["Tickets retained", "Mean resolution (hours)", "Median resolution (hours)",
                                          "Maximum resolution (hours)", "Tickets with resolution time"],
                            "Value": [len(df), durations.mean(), durations.median(), durations.max(), len(durations)]})
    print("\nSERVICE DESK PERFORMANCE SUMMARY")
    print(summary.to_string(index=False, formatters={"Value": lambda v: f"{v:,.2f}" if isinstance(v, (float, int)) and pd.notna(v) else "N/A"}))
    print("\nDATA QUALITY")
    print(pd.DataFrame([quality]).to_string(index=False))
    return summary


def _save(fig: plt.Figure, output: Path, filename: str) -> None:
    fig.tight_layout()
    fig.savefig(output / filename, dpi=160, bbox_inches="tight")
    plt.close(fig)


def create_charts(df: pd.DataFrame, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    counts = df["category"].value_counts().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(counts.index, counts.values, color="#2878a5", label="Tickets")
    ax.set(title="Ticket Count by Category", xlabel="Category", ylabel="Number of tickets")
    ax.tick_params(axis="x", labelrotation=30)
    ax.legend(frameon=False)
    _save(fig, output, "tickets_by_category.png")

    durations = df["resolution_hours"].dropna()
    fig, ax = plt.subplots(figsize=(9, 5))
    if not durations.empty:
        ax.hist(durations, bins="auto", color="#48a999", edgecolor="white", label="Tickets with recorded resolution")
    ax.set(title="Distribution of Resolution Times", xlabel="Resolution time (hours)", ylabel="Ticket count")
    if not durations.empty:
        ax.legend(frameon=False)
    else:
        ax.text(.5, .5, "No valid resolution times", transform=ax.transAxes, ha="center")
    _save(fig, output, "resolution_time_distribution.png")

    weekly = df.set_index("opened_date").resample("W-MON").size()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(weekly.index, weekly.values, marker="o", linewidth=2, color="#665191", label="Tickets opened")
    ax.set(title="Weekly Ticket Volume", xlabel="Week beginning", ylabel="Tickets opened")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.legend(frameon=False)
    _save(fig, output, "weekly_ticket_volume.png")

    scatter = df.dropna(subset=["priority_code", "resolution_hours"])
    fig, ax = plt.subplots(figsize=(9, 5))
    for name, group in scatter.groupby("priority"):
        ax.scatter(group["priority_code"], group["resolution_hours"], alpha=.7, s=38, label=name)
    ax.set_xticks([1, 2, 3, 4], ["Low", "Medium", "High", "Urgent"])
    ax.set(title="Priority and Resolution Time", xlabel="Priority (ordered code)", ylabel="Resolution time (hours)")
    ax.legend(title="Priority", frameon=False)
    ax.text(.01, -.25, "Exploratory association only: priority codes are ordinal, and workload, complexity, staffing,\nand policy may also affect duration. This plot cannot establish that priority causes resolution time.",
            transform=ax.transAxes, fontsize=8, va="top")
    _save(fig, output, "priority_vs_resolution.png")

    comparison = df.dropna(subset=["resolution_hours"]).copy()
    statuses = comparison["status"].str.lower()
    comparison["status_group"] = statuses.map(lambda x: "Open" if x == "open" else "Resolved" if x in {"resolved", "closed"} else None)
    comparison = comparison.dropna(subset=["status_group"])
    fig, ax = plt.subplots(figsize=(8, 5))
    groups = [comparison.loc[comparison.status_group == name, "resolution_hours"] for name in ("Open", "Resolved")]
    nonempty = [(g, n) for g, n in zip(groups, ("Open", "Resolved")) if not g.empty]
    if nonempty:
        ax.boxplot([item[0] for item in nonempty], tick_labels=[item[1] for item in nonempty], patch_artist=True,
                   boxprops={"facecolor": "#d9e8f0"}, medianprops={"color": "#b23a48", "linewidth": 2})
        for i, (group, name) in enumerate(nonempty, start=1):
            ax.scatter([i] * len(group), group, color=COLORS[name], alpha=.35, s=15, label=f"{name} tickets")
        ax.legend(frameon=False)
    else:
        ax.text(.5, .5, "No comparable records with resolution times", transform=ax.transAxes, ha="center")
    ax.set(title="Recorded Resolution Times by Current Status", xlabel="Current status", ylabel="Resolution time (hours)")
    ax.text(.01, -.20, "Descriptive comparison only. Open-ticket durations may be incomplete or right-censored;\ndifferences do not show that status caused a faster or slower resolution.",
            transform=ax.transAxes, fontsize=8, va="top")
    _save(fig, output, "resolution_by_status.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("tickets.csv"), help="Input ticket CSV")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"), help="Chart output directory")
    args = parser.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"Input CSV not found: {args.input}")
    data, quality = load_and_clean(args.input)
    if data.empty:
        raise SystemExit("No usable ticket rows remain after cleaning.")
    print_summary(data, quality)
    create_charts(data, args.output)
    print(f"\nCharts saved to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
