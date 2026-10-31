#!/usr/bin/env python3
"""Convert the Step 1 `.bin` extractions to float32 `.npy` plus `data/meta.json`.

Follows the convention of ~/CUORE_SHRED/scripts/convertTowerRun.py so the output is
interchangeable with that pipeline and usable by the WitnessDenoise shard builder: a per-channel
per-window offset (the median) is subtracted and recorded in meta.json, so the operation is
reversible and float32 precision is spent on the signal rather than the baseline.

Bulk arrays go to pscratch via the `data/arrays` symlink: /global/homes is at 85% of a 40 GiB quota
and the arrays total about 6 GiB (log E020). Small metadata stays in `data/` in the project.

    python3 -I extract/to_npy.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_vcts import ADC2MV, read_header, read  # noqa: E402

PROJ = Path(__file__).resolve().parents[1]
BINS = Path("<SCRATCH>/vibes_main/output")
AUX_FULLRUN = Path("<SCRATCH>/runRUNA/timestreams")
ARRAYS = PROJ / "data" / "arrays"

BOLO = list(range(937, 989))
AUX_RUNA = [1018, 1019, 1020] + list(range(1101, 1124))
AUX_RUNB = list(range(1101, 1124))

# label -> (run, t0, t1, aux source)   "extracted" = its own .bin; "slice" = cut from the full-run aux
WINDOWS = {
    "excitation": (RUNA, 3990, 21760, "slice"),
    "quiet1": (RUNA, 0, 250, "slice"),
    "quiet2": (RUNA, 1275, 1500, "slice"),
    "quiet3": (RUNA, 48025, 48800, "slice"),
    "quietrun": (RUNB, 0, 2456, "extracted"),
}

SB540_MAP = {
    1101: "geophone 4K-Y", 1102: "geophone 4K-Z", 1103: "accel y-beam new(A) X",
    1104: "accel y-beam new(A) Y", 1105: "accel msp X", 1106: "accel msp Y", 1107: "accel msp Z",
    1108: "accel y-beam (C) X", 1109: "accel y-beam (C) Y", 1110: "accel y-beam (C) Z",
    1111: "shaker FORCE (drive reference)", 1112: "shaker ACCEL",
    1113: "accel msp(new) X", 1114: "accel msp(new) Y", 1115: "accel msp(new) Z",
    1116: "accel y-beam new(A) Z", 1117: "seismo2 msp Z", 1118: "seismo2 msp Y",
    1119: "seismo2 msp X", 1120: "seismo2 ybeam(B) Z", 1121: "seismo2 ybeam(B) Y [BAD: check wire]",
    1122: "seismo2 ybeam(B) X", 1123: "accel y-beam new(B) Z",
    1018: "special channel 1018", 1019: "special channel 1019", 1020: "special channel 1020",
}


def bin_path(run, ch, t0, t1):
    return BINS / f"run{run}" / "timestreams" / f"run{run}_ch{ch:04d}_t{t0}_T{t1}.bin"


def convert(x, out):
    """Subtract the median (recorded), store float32 mV. Returns the stats dict."""
    x = x.astype(np.float64)
    offset = float(np.median(x[::100]))          # every 100th sample, as convertTowerRun does
    x -= offset
    y = x.astype(np.float32)
    tmp = out.with_suffix(".tmp.npy")
    np.save(tmp, y)
    tmp.rename(out)
    return dict(offset_mV=offset, rms_mV=float(y.std()), min_mV=float(y.min() + offset),
                max_mV=float(y.max() + offset), n=int(len(y)),
                n_nonfinite=int(np.count_nonzero(~np.isfinite(y))))


def main():
    if not ARRAYS.exists():
        print(f"ERROR: {ARRAYS} missing -- create the symlink to pscratch first", file=sys.stderr)
        return 1
    meta = {
        "run_excitation": RUNA, "run_quiet": RUNB,
        "sample_rate_hz": 1000.0, "units": "mV",
        "adc_to_mV": ADC2MV,
        "adc_to_mV_provenance": ("adc2mV in $VIBES/src/WriteTimestreamsFromDAQ.cpp; confirmed by provenance "
                                 "for aux channels, NOT independently verified for bolometer channels -- "
                                 "treat channel_gain.csv absolute scale as an assumption"),
        "utc_start": None,
        "utc_start_note": ("unavailable: the RunStartTime sheet of 'CUORE Vibrational Tests - Runs.xlsx' is "
                           "empty for runs 306428/306431/306438/RUNA. All times are SECONDS FROM RUN START."),
        "slice_offset_s": 3990,
        "slice_offset_note": ("the excitation arrays begin at t = 3990 s of run RUNA, NOT at 0. Any trigger "
                              "time, pulser time or step boundary quoted in run coordinates must have 3990 s "
                              "subtracted before indexing these arrays. See log E011 and SHRED_COMPAT.md."),
        "run_seconds_RUNA": 48818.0,
        "run_seconds_RUNB": 2456.0,
        "shaker": {"run": RUNA, "position": "MSP - X", "drive_amplitude": "100 mV pp",
                   "sweep": "1-20 Hz nominal, 0.1 Hz steps, 250 s dwell",
                   "extracted_band_hz": [2.52, 9.52], "n_steps_extracted": 71,
                   "drive_reference_channel": 1111, "drive_accel_channel": 1112,
                   "amplitude_constant": ("verified on run 306428: force RMS repeats to 0.1-0.2% over 12-13 "
                                          "repeats of each frequency, so the drive does not vary. Measured "
                                          "force does vary ~25% ACROSS frequency, which is the shaker/stinger/"
                                          "impedance-head response, not a drive change. No amplitude variation "
                                          "at fixed frequency exists in this run, so the linearity and "
                                          "quadratic-thermal-path checks are NOT APPLICABLE here.")},
        "bad_intervals_run_coords_s": [[1275, 1500]],
        "bad_intervals_note": ("225 s shaker dropout between the 1.32 Hz and 1.52 Hz steps (force RMS 5.5 mV "
                               "against 15-1520 mV when driven). Outside the excitation window; it is also "
                               "reused as quiet segment 'quiet2'."),
        "pulser": {"flag": 2, "n_total": 4882, "n_in_excitation_window": 1777,
                   "period_s": 10.0, "first_time_s": 5.002, "rate_hz": 0.1,
                   "channel_independent": True,
                   "times_file": "data/pulser_times.npy",
                   "warning": ("DETERMINISTIC 0.1 Hz heater pulser, synchronous on all bolometers. Its comb "
                               "falls on every multiple of 0.1 Hz, hence on EVERY drive frequency used. Step "
                               "boundaries are multiples of 250 s and 250/10 = 25 exactly, so the pulser is "
                               "PHASE-LOCKED to every frequency-step boundary: coherent step-onset averaging "
                               "accumulates it coherently and it looks MORE convincing the more steps are "
                               "averaged. Must be masked. See log E019.")},
        "physics_triggers": {"flag": 1, "n_in_tower19": 1, "times_s": [30959.916],
                             "n_in_excitation_window": 0,
                             "note": ("essentially no particle-event triggers in this run; the single flag-1 "
                                      "trigger (ch963) is outside the window. GetAllTriggersByTower wrote "
                                      "empty lists, so these came from the RDCF directly -- see log E018.")},
        "pt_harmonics_hz": [2.8, 4.2, 5.6, 7.0, 8.4],
        "pt_harmonics_note": ("multiples of 1.4 Hz inside the extracted band. Independently supported: in the "
                              "shaker-off segments of RUNA the ch1111 dominant peaks sit at 4.20 and 5.56 Hz, "
                              "i.e. 3x and 4x 1.4 Hz."),
        "known_resonance_hunts_hz": {"3.35-3.55": "runs 306468/306469/306470, 306486, 306492, 306503",
                                     "8.0-9.0": "runs 306477, 306485"},
        "channel_map_sb540": SB540_MAP,
        "channel_map_note": ("sb540 mapping from the 'Diagnostic Devs' sheet. The map CHANGES between service "
                             "breaks; runs 306428/306431 are sb522 and use a different one, where 1111-1116 "
                             "were pulse-tube antennas rather than shaker channels."),
        "reader_provenance": ("WriteContinuousDataToBinary from vibes GitLab main 6ca017a (2026-10-21), built "
                              "at <SCRATCH>/vibes_main; byte-identical to ~/WriteContinuousData"
                              "ToBinary.cpp. RDCF read from /global/cfs/.../syncData/CUORE/ContinuousData/."),
        "windows": {}, "channels": {},
    }

    for label, (run, t0, t1, auxmode) in WINDOWS.items():
        aux = AUX_RUNB if run == RUNB else AUX_RUNA
        (ARRAYS / label / "bolo").mkdir(parents=True, exist_ok=True)
        (ARRAYS / label / "aux").mkdir(parents=True, exist_ok=True)
        n_expect = int((t1 - t0) * 1000)
        print(f"=== {label}: run {run}, t=[{t0},{t1}] s, {n_expect:,} samples/ch", flush=True)
        st = {}
        for ch in BOLO:
            _, x = read(bin_path(run, ch, t0, t1))
            st[f"ch{ch:04d}"] = convert(x, ARRAYS / label / "bolo" / f"ch{ch:04d}.npy")
        print(f"    {len(BOLO)} bolometers done", flush=True)
        for ch in aux:
            if auxmode == "extracted":
                _, x = read(bin_path(run, ch, t0, t1))
            else:
                p = AUX_FULLRUN / f"run{run}_ch{ch}_t0_Tend.bin"
                if not p.exists():
                    continue
                h = read_header(p)
                raw = np.memmap(p, dtype="<i4", mode="r", offset=48, shape=(h["n_samples"],))
                x = np.asarray(raw[int(t0 * 1000):int(t1 * 1000)]) * ADC2MV
            s = convert(x, ARRAYS / label / "aux" / f"ch{ch:04d}.npy")
            s["source"] = auxmode
            st[f"ch{ch:04d}"] = s
        print(f"    {len([k for k in st]) - len(BOLO)} aux done", flush=True)
        meta["windows"][label] = {"run": run, "t0_s": t0, "t1_s": t1, "n_samples": n_expect,
                                  "bolometers": BOLO, "aux": aux, "aux_source": auxmode}
        meta["channels"][label] = st

    (PROJ / "data" / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"\nwrote data/meta.json ({len(json.dumps(meta))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
