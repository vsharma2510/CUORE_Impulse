#!/usr/bin/env python3
"""results/fig_timeline.pdf -- the pilot as a swimlane over real clock time, broken axis.

Every span is MEASURED: recording spans from each cast's header timestamp and its mtime, phase
boundaries from the mtime of the artefact that phase produced, two gates from frames rendered out of
the casts. Nothing is placed from the log headings, because E022 established those are overstated by
up to 122 minutes for the middle of the pilot. A gate with no direct measurement is drawn as the
bracket between the artefact submitted and the artefact that followed approval -- which is what the
gate was -- never as an invented point.

The axis is broken across the 05:33-11:20 usage-limit pause, which is dead time, not work.
"""
import datetime as dt
import sys

import matplotlib.dates as mdates

sys.path.insert(0, "reconcile")
import plotstyle as ps                                                            # noqa: E402

ps.use("wide")
C = ps.COLORS


def T(s):
    p = [int(x) for x in s.split(":")]
    while len(p) < 3:
        p.append(0)
    return mdates.date2num(dt.datetime(2026, 10, 31, *p))


LANES = ["Vivek", "critic", "verifier", "analyst", "orchestrator"]
BARS = {
    "orchestrator": [
        (T("02:07:45"), T("02:08:23"), "", C["grey"]),
        (T("02:08:23"), T("03:01:01"), "reconnaissance", C["teal"]),
        (T("03:01:01"), T("03:13:06"), "", C["grey"]),
        (T("03:13:06"), T("03:51:19"), "extract", C["teal"]),
        (T("03:51:19"), T("04:17:07"), "SPEC", C["teal"]),
        (T("04:17:07"), T("04:58:26"), "supervise", C["grey"]),
        (T("05:28:07"), T("05:33:27"), "", C["grey"]),
        (T("11:20:13"), T("12:32:39"), "reconcile", C["teal"]),
        (T("12:32:39"), T("12:43:00"), "deliver", C["grey"]),
        (T("12:43:00"), T("13:09:52"), "audit", C["teal"]),
        (T("13:09:52"), T("13:34:44"), "", C["grey"]),
        (T("13:34:44"), T("14:04:03"), "amend", C["teal"]),
        (T("14:04:03"), T("14:18:00"), "", C["grey"]),
    ],
    "analyst": [(T("04:17:50"), T("04:35:32"), "ERA", C["blue"]),
                (T("14:04:30"), T("14:15:30"), "causality", C["blue"])],
    "verifier": [(T("04:17:22"), T("04:22:20"), "", C["rose"]),
                 (T("04:24:19"), T("04:58:11"), "lock-in", C["teal"]),
                 (T("13:10:30"), T("13:31:06"), "damping", C["teal"])],
    "critic": [(T("05:28:07"), T("05:33:27"), "", C["coral"])],
    "Vivek": [(T("03:01:01"), T("03:13:06"), "", C["violet"]),
              (T("03:51:19"), T("04:16:17"), "", C["violet"]),
              (T("04:43:47"), T("04:45:30"), "", C["violet"]),
              (T("12:29:00"), T("12:30:18"), "", C["violet"]),
              (T("13:05:00"), T("13:09:52"), "", C["violet"]),
              (T("13:58:00"), T("14:04:03"), "", C["violet"])],
}
# (time, label, measured directly from a rendered cast frame?)
GATES = [(T("02:30"), "1", False), (T("03:07"), "2", False), (T("04:04"), "3", False),
         (T("04:43:47"), "models", True), (T("12:29"), "4", True),
         (T("13:07"), "4.3", False), (T("14:01"), "4.5", False)]
RECS = [(T("02:07:59"), T("02:08:23"), 0.4), (T("04:17:07"), T("04:58:26"), 25.5),
        (T("05:28:07"), T("09:11:50"), 6.8), (T("11:20:13"), T("12:32:39"), 13.9),
        (T("13:09:52"), T("13:34:44"), 3.5), (T("14:04:03"), T("14:17:33"), 13.5)]
# (point, lane, label, colour, dy, va, text_x)
NOTES = [(T("04:22:20"), "verifier", "attempt 1 blocked", C["rose"], +0.60, "bottom", T("04:35")),
         (T("04:16:17"), "orchestrator", "sentinel planted", C["muted"], -0.58, "top", T("03:40"))]

SPANS = [(T("02:00"), T("05:45")), (T("11:15"), T("14:25"))]
fig, axs = ps.figure(1, 2, figsize=(6.9, 3.0), sharey=True,
                     gridspec_kw=dict(width_ratios=[(b - a) for a, b in SPANS], wspace=0.04))
y = {n: len(LANES) - 1 - i for i, n in enumerate(LANES)}
YB = -1.05

for ax, (x0, x1) in zip(axs, SPANS):
    ax.axvspan(T("12:43"), T("14:18"), color=C["teal"], alpha=0.05, lw=0, zorder=0)
    ax.axvspan(T("02:08:23"), T("04:17:07"), color=C["coral"], alpha=0.07, lw=0, zorder=0)
    for lane, bars in BARS.items():
        for a, b, lab, col in bars:
            if b < x0 or a > x1:
                continue
            ax.barh(y[lane], b - a, left=a, height=0.46, color=col, alpha=0.92,
                    edgecolor=C["ink"], linewidth=0.4, zorder=3)
            if lab and (b - a) > (x1 - x0) * 0.105:
                ax.text(a + (b - a) / 2, y[lane], lab, ha="center", va="center",
                        family=ps.TEXT_FONTS, size=ps.ctx()["note"] - 1.2, color="white", zorder=5)
    for t, lab, meas in GATES:
        if not (x0 <= t <= x1):
            continue
        ax.axvline(t, color=C["violet"], lw=0.45, ls=(0, (2, 2)), alpha=0.6, zorder=1)
        ax.plot([t], [y["Vivek"] + 0.40], marker="v", ms=ps.ctx()["ms"] * 0.9,
                color=C["violet"] if meas else C["bg"], mec=C["violet"], mew=0.8,
                clip_on=False, zorder=6)
        ax.text(t, y["Vivek"] + 0.60, lab, ha="center", va="bottom", family=ps.MONO_FONTS,
                size=ps.ctx()["note"] - 1.2, color=C["violet"], zorder=6)
    for t, lane, lab, col, dy, va, tx in NOTES:
        if x0 <= t <= x1:
            ax.annotate(lab, (t, y[lane]), (tx, y[lane] + dy), ha="center", va=va,
                        family=ps.MONO_FONTS, size=ps.ctx()["note"] - 1.8, color=col,
                        arrowprops=dict(arrowstyle="-", color=col, lw=0.5), zorder=6)
    for a, b, live in RECS:
        if b < x0 or a > x1:
            continue
        ax.barh(YB, b - a, left=a, height=0.30, color=C["rule"], edgecolor=C["ink"],
                linewidth=0.4, zorder=3)
        ax.barh(YB, (b - a) * min(live / ((b - a) * 1440), 1.0), left=a, height=0.30,
                color=C["green"], edgecolor="none", zorder=4)
    ax.set_xlim(x0, x1)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.grid(axis="y", visible=False)

axs[0].set_ylim(-1.75, len(LANES) - 0.1)
axs[0].set_yticks(list(y.values()) + [YB], LANES + ["recording"], family=ps.MONO_FONTS)
axs[0].text(T("03:12"), 3.42, "no video\n129 min, 24 of 51 ledger rows",
            ha="center", va="center", family=ps.MONO_FONTS, size=ps.ctx()["note"] - 1.2,
            color=C["coral"], linespacing=1.5)
axs[0].text(T("02:03"), YB - 0.50, "dark = live, pale = idle", family=ps.MONO_FONTS,
            size=ps.ctx()["note"] - 1.8, color=C["muted"], va="top", ha="left")
axs[1].text(T("11:17"), len(LANES) - 0.42, "64 live min of 730", ha="left", va="bottom",
            family=ps.MONO_FONTS, size=ps.ctx()["note"] - 1.2, color=C["muted"])
for ax, side in ((axs[0], "right"), (axs[1], "left")):
    ax.spines[side].set_linestyle((0, (2, 2)))
    ax.spines[side].set_alpha(0.5)
axs[1].tick_params(left=False)
fig.suptitle("Pilot timeline, measured", family=ps.TEXT_FONTS, weight="bold",
             size=ps.ctx()["title"], color=C["ink"])
for ax in axs:
    ax.set_xlabel("2026-10-31 (UTC)", family=ps.MONO_FONTS)
    for lab in ax.get_xticklabels():
        lab.set_family(ps.MONO_FONTS)
axs[1].set_xlabel("after the usage pause; 4.3/4.5 amend the spec", family=ps.MONO_FONTS)
ps.finalize(fig, *axs)
print(ps.save(fig, "results/fig_timeline"))
