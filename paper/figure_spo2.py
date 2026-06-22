#!/usr/bin/env python3
"""SpO2 centerpiece figure — nightly MEAN vs MINIMUM overnight oxygen saturation.

Reads the raw Garmin sleepData.json export and plots, per night, the averageSPO2
(reads "normal") against the lowestSPO2 (the testimony), with clinical reference
bands. Saves paper/figure_spo2.png and prints the summary statistics (which double
as the verification of the §3.2 numbers). Requires matplotlib.

Run:  python3 paper/figure_spo2.py
"""
from __future__ import annotations

import glob
import json
import os
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE / "figure_spo2.png"
# Garmin sleep-export directory. Set GARMIN_EXPORT_DIR to your own export path; the
# default is a local, non-personal placeholder so no private path lives in shareable code.
GARMIN = os.path.expanduser(os.environ.get("GARMIN_EXPORT_DIR", "./data/garmin-sleep"))


def load_nights() -> list[tuple[datetime, float, float | None]]:
    nights = []
    for f in sorted(glob.glob(os.path.join(GARMIN, "*sleepData.json"))):
        data = json.load(open(f, encoding="utf-8", errors="replace"))
        for r in data if isinstance(data, list) else [data]:
            summ = r.get("spo2SleepSummary") if isinstance(r, dict) else None
            if not summ:
                continue
            lo, avg, day = summ.get("lowestSPO2"), summ.get("averageSPO2"), r.get("calendarDate")
            if day and isinstance(lo, (int, float)) and 50 < lo <= 100:
                nights.append((datetime.strptime(day, "%Y-%m-%d"), float(lo), float(avg) if avg else None))
    nights.sort()
    return nights


def main() -> int:
    nights = load_nights()
    dates = [n[0] for n in nights]
    lows = [n[1] for n in nights]
    n = len(lows)
    avg_pairs = [(d, a) for d, _, a in nights if a is not None]
    mean_avg = sum(a for _, a in avg_pairs) / len(avg_pairs)
    nadir = min(lows)
    b90 = sum(1 for x in lows if x < 90)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.axhspan(50, 85, color="#d62728", alpha=0.06)
    ax.axhspan(85, 88, color="#ff7f0e", alpha=0.06)
    ax.axhspan(88, 90, color="#ffbf00", alpha=0.06)
    for y, lab in [(90, "90% hypoxemia"), (88, "88% significant"), (85, "85% severe")]:
        ax.axhline(y, color="gray", ls="--", lw=0.8)
        ax.text(dates[0], y + 0.2, lab, fontsize=7, color="gray")

    ax.scatter(dates, lows, s=14, color="#d62728", label="nightly MINIMUM SpO₂ (the testimony)", zorder=3)
    ax.plot([d for d, _ in avg_pairs], [a for _, a in avg_pairs],
            color="#1f77b4", lw=1.6, label="nightly MEAN SpO₂ (reads 'normal')", zorder=2)
    ax.axhline(mean_avg, color="#1f77b4", ls=":", lw=1, alpha=0.7)
    ax.text(dates[-1], mean_avg + 0.3, f"mean {mean_avg:.1f}%", fontsize=8, color="#1f77b4", ha="right")
    ax.annotate(f"nadir {nadir:.0f}%", xy=(dates[lows.index(nadir)], nadir),
                xytext=(10, -12), textcoords="offset points", fontsize=8, color="#d62728",
                arrowprops=dict(arrowstyle="->", color="#d62728"))

    ax.set_ylim(72, 100)
    ax.set_ylabel("Overnight SpO₂ (%)")
    ax.set_title("The average reads normal; the minimum testifies\n"
                 f"{b90}/{n} nights ({100 * b90 / n:.0f}%) below 90%  ·  mean {mean_avg:.1f}%  ·  nadir {nadir:.0f}%")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(OUT, dpi=150)

    print(f"[DONE] {n} monitored nights -> {OUT}")
    print(f"  mean(avg)={mean_avg:.1f}%  nadir={nadir:.0f}%  <90%: {b90}/{n} ({100 * b90 / n:.0f}%)")
    for thr in (88, 85):
        c = sum(1 for x in lows if x < thr)
        print(f"  <{thr}%: {c}/{n} ({100 * c / n:.0f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
