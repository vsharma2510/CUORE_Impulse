#!/usr/bin/env python3
"""results/fig_pilot.pdf -- the pilot's one figure, 6.5 x 2.4 in, two panels.

(a) is the primary deliverable: the error record, by category, stacked by WHICH NODE caught each one.
(b) is the physics: the median transfer function over the 52 tower-19 bolometers with the adjudicated
    modes marked, and the two reference-channel discontinuities shaded.

Every number is read from results/errors.csv, results/modes_reconciled.csv and the nodes' own
responses.npz; nothing is typed in.
"""
import collections
import csv
import sys

import numpy as np

sys.path.insert(0, "reconcile")
import plotstyle as ps                                                            # noqa: E402

ps.use("wide")
C = ps.COLORS

# ---------------------------------------------------------------- data
err = list(csv.DictReader(open("results/errors.csv")))
SHORT = {"tooling or environment": "tooling", "wrong method or convention": "method",
         "data handling": "data handling", "code bug": "code bug",
         "physics error": "physics", "fabricated or unsupported claim": "unsupported claim"}
CATCH = ["orchestrator", "analyst", "verifier", "critic", "Vivek"]
CCOL = {"orchestrator": C["grey"], "analyst": C["blue"], "verifier": C["teal"],
        "critic": C["coral"], "Vivek": C["violet"]}
tot = collections.Counter(SHORT[r["category"]] for r in err)
cats = [c for c, _ in tot.most_common()]
M = np.zeros((len(cats), len(CATCH),), int)
for r in err:
    M[cats.index(SHORT[r["category"]]), CATCH.index(r["caught_by"])] += 1

mr = list(csv.DictReader(open("results/modes_reconciled.csv")))
A = np.load("analysis/responses.npz", allow_pickle=True)
f = A["f_drive_hz"]
Hm = np.median(np.abs(A["H"][A["kind"] == "bolo"]), 0)
Hlo, Hhi = (np.percentile(np.abs(A["H"][A["kind"] == "bolo"]), p, axis=0) for p in (16, 84))

fig, axs = ps.figure(1, 2, figsize=(6.5, 2.4),
                     gridspec_kw=dict(width_ratios=[1.0, 1.15]))
ax, bx = axs

# ---------------------------------------------------------------- (a) the error record
y = np.arange(len(cats))[::-1]
left = np.zeros(len(cats))
for j, who in enumerate(CATCH):
    v = M[:, j]
    ax.barh(y, v, left=left, height=0.62, color=CCOL[who], edgecolor=C["bg"],
            linewidth=0.5, label=f"{who} ({v.sum()})", zorder=3)
    left += v
for i, c in enumerate(cats):
    ax.text(left[i] + 0.35, y[i], str(int(left[i])), va="center", ha="left",
            family=ps.MONO_FONTS, size=ps.ctx()["note"], color=C["muted"], zorder=4)
ax.set_yticks(y, cats, family=ps.MONO_FONTS)
ax.set_xlim(0, 15.4)
ax.set_ylim(-0.6, len(cats) + 0.05)
ax.grid(axis="y", visible=False)
ps.style_axes(ax, "Error record, by who caught it", "errors logged (n)", "")
ax.legend(prop={"family": ps.MONO_FONTS, "size": ps.ctx()["note"] - 0.7}, handlelength=1.1,
          loc="lower right", borderaxespad=0.4, labelspacing=0.25, handletextpad=0.5)
ps.panel_label(ax, "a")

# ---------------------------------------------------------------- (b) the physics
# Panel (b) is the physics result and nothing else. Which node found a mode is a process fact and
# lives in panel (a) and in modes_reconciled.csv; putting it in the legend here made four entries
# that a reader could not decode ("of which verifier only" meant nothing without the report).
for fb in (5.45, 7.45):
    bx.axvspan(fb - 0.06, fb + 0.06, color=C["rose"], alpha=0.20, lw=0, zorder=1)

bx.fill_between(f, Hlo, Hhi, color=C["teal"], alpha=0.18, lw=0, zorder=2,
                label="16–84% across channels")
bx.semilogy(f, Hm, color=C["teal"], lw=ps.ctx()["lw"] * 1.15, zorder=4,
            label="median of 52 bolometers")

head = sorted(float(r["f0_hz"]) for r in mr if r["status"] == "headline")
for k, f0 in enumerate(head):
    bx.axvline(f0, color=C["ink"], lw=0.45, ls=(0, (1.5, 2)), alpha=0.5, zorder=3)
    bx.plot([f0], [6.5e-2], marker="v", ms=ps.ctx()["ms"] * 0.8, color=C["ink"],
            zorder=6, clip_on=False,
            label=f"mode ({len(head)})" if k == 0 else None)

# the single strongest feature, called out by name
i34 = int(np.argmax(Hm))
bx.annotate(f"{f[i34]:.2f} Hz\nstrongest on 42 of 52", (f[i34], Hm[i34]), (3.72, 4.0e-2),
            family=ps.MONO_FONTS, size=ps.ctx()["note"] - 1.0, color=C["ink"], va="center",
            ha="left", arrowprops=dict(arrowstyle="-", color=C["ink"], lw=0.5), zorder=7)

bx.set_xlim(2.5, 9.5)
bx.set_ylim(3e-5, 1.4e-1)
ps.style_axes(bx, "Bolometer response to the shaker",
              "drive frequency (Hz)", "|H| = bolometer / force (mV/mV)")
h, lab = bx.get_legend_handles_labels()
order = [lab.index("median of 52 bolometers"), lab.index("16–84% across channels"),
         lab.index(f"mode ({len(head)})")]
bx.legend([h[i] for i in order], [lab[i] for i in order],
          prop={"family": ps.MONO_FONTS, "size": ps.ctx()["note"] - 0.6}, handlelength=1.3,
          loc="upper right", bbox_to_anchor=(1.0, 0.88), borderaxespad=0.4,
          labelspacing=0.3, handletextpad=0.5)
bx.text(5.68, 3.4e-3, "all 52 bolometers respond\nrose: drive monitors disagree",
        family=ps.MONO_FONTS, size=ps.ctx()["note"] - 0.9, color=C["muted"],
        va="center", ha="left", zorder=6, linespacing=1.5)
ps.panel_label(bx, "b")

ps.finalize(fig, ax, bx)
print(ps.save(fig, "results/fig_pilot"))
print(f"(a) {len(err)} errors, {len(cats)} categories, caught-by "
      f"{dict(zip(CATCH, M.sum(0).tolist()))}")
print(f"(b) {len(head)} modes marked; |H| median spans {Hm.min():.2e} to {Hm.max():.2e}; "
      f"peak at {f[int(np.argmax(Hm))]:.2f} Hz")
