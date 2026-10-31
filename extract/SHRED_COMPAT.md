# Is the `.bin` pipeline compatible with the SSM/SHRED analysis?

Orchestrator, 2026-10-31, answering Vivek's question during the Step 1 extraction. Assessed by
reading `~/CUORE_SHRED/scripts/convertTowerRun.py`, `tower/{rootmeta,decimate,geometry,windows,
spectral}.py` and `~/Denoising/WitnessDenoisingAE/src/`, not by assumption.

**CORRECTED 2026-10-31 04:55 UTC.** The first version of this note claimed the S4D encoder "does
not exist on this system". That was wrong -- see the correction in section 4 and error E017. Vivek
pointed to `~/ML_denoising_ssm/DenoisingAux/`, which the original search never covered.

**Short answer: compatible at the array level, broken at the metadata level, and the S4D encoder the
brief names is already implemented and already tuned on ch 975.** The arrays line up. What does not
line up is the event metadata SHRED needs *besides* the samples.

## What lines up, with no work

| requirement | our `.bin` slice | verdict |
| --- | --- | --- |
| input sample rate | 1 kHz | matches `decimate.FS_IN = 1000.0` |
| decimation to 200 Hz | `tower/decimate.py`: 401-tap Kaiser, 90 Hz cutoff, `resample_poly`, delay-compensated | works directly on our stream, no change |
| dtype convention | int32 ADC counts -> subtract per-channel median -> float32 | exactly what `convertTowerRun.convert_channel` does; `np.save` output is interchangeable |
| bolometer channel set | 937-988 | `geometry.tower_channels(19)` returns precisely this |
| SHRED input/target split | 23 aux in, 52 bolometers out | the sparse-sensor shape SHRED is built for |
| GPU | `pyT_ssm` carries torch 2.5.1.post303 with CUDA available | fine |

So `extract/to_npy.py` can emit `.npy` files that drop straight into
`data/tower19/runRUNA/stream/ch<CCCC>.npy`, and `tower/windows.py` and `tower/spectral.py` will
read them.

## What is broken, and why

### 1. There is no event metadata for run RUNA, and there cannot be

`convertTowerRun.py` builds `events.npz` holding, per bolometer, `trig_<ch>` (trigger times),
`bad_<ch>` (bad intervals) and `tw_<ch>` (the pre-selected 50 s windows). All of it comes from
`denoise/ChannelRunData_tower<NN>.root` under `rootmeta.OUTPUT`, i.e. kjvetter's tree. That tree
covers **run304931-run305791 only**; there is no 3064xx run in it, so for RUNA the file simply does
not exist. `meta.json["run_seconds"]`, read from `runtimeBolo` in the same file, is missing too.

This is not cosmetic. `windows.valid_starts()` keeps a window only if **no bolometer of the set has a
trigger in `[start - hold, end + post]`** and no bad interval overlaps. Without triggers that rule
cannot be applied at all, and a particle pulse landing inside an averaging window would bias both
the FRF and any SHRED target.

**Fix, and it is cheap:** `$VIBES` already has `GetAllTriggersByRun` and `GetAllTriggersByTower`
built, and the sources are in the fresh clone. Usage is
`GetAllTriggersByTower <run> <tower> <dataset>` and
`GetAllTriggersByRun <run> <runType> <dataset> <path to QRaw files>`. Run RUNA is dataset
3183 per the spreadsheet. That regenerates triggers from DIANA for this run and closes the gap
without depending on kjvetter reprocessing anything. `run_seconds = 48818 s` we already have from the
reader's own output, confirmed against the witness header.

### 2. Our stream is a 17,770 s slice, not a whole run

The pipeline's convention is explicit: "sample i is at `t = i / 200` s from run start". Our slice
starts at **t = 3990 s**. Feeding it in as though it began at zero would silently shift every
trigger time, bad interval and window boundary by 3990 s. `meta.json` must carry the slice offset,
and either the trigger times get translated by `-3990 s` or the stream gets padded. This is a
one-line hazard that would produce plausible-looking, wrong results, so it is called out here and
will be stated in `data/meta.json`.

### 3. The aux channel set is hard-coded too narrow

`convertTowerRun.AUX_CHANNELS = list(range(1101, 1120))` gives 1101-1119 and so **drops 1120-1123**
— the seismo2 y-beam (B) axes and accel y-beam (B) Z that sb540 added, which are four of the 23
sensors we are extracting. A one-line change, but it has to be made deliberately or those channels
are silently unused.

### 4. CORRECTION: the S4D encoder exists, is implemented, and is already tuned on ch 975

The first version of this note stated that no S4D code existed anywhere, based on searching
`~/CUORE_SHRED` and `~/Denoising`. That search was incomplete and the conclusion was wrong. Vivek
pointed to `~/ML_denoising_ssm/DenoisingAux/`, which holds both of the components the brief names:

- **`WitnessDenoise/`** -- a mature project (131 KB `EXPERIMENT_LOG.md`, 58 KB `PROGRESS.md`, pytest
  suite, Perlmutter and Pitt CRC setups). `src/witnessdenoise/models/ssm.py` implements
  `S4DDenoiser1D`: a **bidirectional diagonal state-space model** (S4D, Gu et al. 2022), interface
  `(B, numWitnesses, T) -> (B, T)`, one forward and one independent backward kernel summed into a
  two-sided filter, FFT convolution zero-padded to 2T. With the defaults (`d_model` 48, `d_state` 64,
  4 layers, 19 witnesses) it is **about 70k parameters** -- squarely inside the brief's 70-300k range,
  and deliberately matched to the 67k of the 200 Hz TCN baseline.
- **`RootReader/`** -- `read_root_output_config.yaml`, `read_root_output.py`, `ConvertROOTOutput.py`,
  `writeBolos.cpp`: exactly the reader the brief lists as a candidate.

Two details make this much better than a from-scratch build:

1. The model config declares **`decimate: {factor: 5, fs: 1000.0}`** -- a 1 kHz input decimated to a
   200 Hz core. **Our `.bin` is 1 kHz**, so the rate convention already matches with no change.
2. **ch 975 is the project's primary channel.** The configs are named
   `ch975_w19_demeanPsd0p1to50HzLogGuard50to70_withinRun_ds5_s4d.yaml` and similar, with `w19` = 19
   witness channels, and there are sibling configs for ch273, ch533, ch714, ch858. So Vivek's request
   for ch 975 was not arbitrary: it is the established study channel for the S4D witness-denoising
   work, which also reframes E007 -- a channel chosen for denoising research may well have been
   chosen *because* it is noisy.

The split machinery the brief's Step 6 asks for also already exists: the config's
`split: {mode: within_run, block_windows: 120, val_every: 5, gap_windows: 2}` is contiguous blocks
with a gap, implemented in `data/splits.py`.

**Data format it consumes.** `data/shards.py` reads per-run `.npy` shards shaped
`(numSlices, sliceLength, numChannels)` with **channel 0 the bolometer target and the rest witness
channels**, built by `scripts/buildDataset.py`, plus a single global per-channel normalisation from
`data/stats.py` (the docstring is explicit that per-window normalisation would erase the noise-power
variation the model must learn). The existing `stats_demean_withinRun.json` for channel0975 carries
20 means and 20 stds = 1 bolometer + 19 witnesses.

So feeding our extraction in means building shards of shape
`(numSlices, sliceLength, 1 + 23)` per bolometer at 1 kHz -- the same layout with 23 aux instead of
19. That is a data-preparation task against an existing, tested pipeline, **not** a model build.

### 5. Step 6's windowing premise inherits the E004 problem

Step 6 specifies windows "2 s before to 20 s after each impulse" and a split "by impulse". There are
no impulses — there are 71 frequency steps of 250 s. The split must become a split **by frequency
step** (contiguous blocks, gap of at least one window between blocks, as the brief intends), and the
window length should follow `tower/windows.py`'s own default of 25 s with 12.5 s hop rather than the
impulse geometry. `results/shred_split.json` would then list held-out **step indices**, not impulse
indices, and must still be committed before any training.

## Recommendation

1. Convert `.bin -> .npy` in the `convertTowerRun` convention (median subtracted and recorded, 1 kHz
   kept for Step 3; decimate to 200 Hz only for Step 6).
2. Regenerate triggers and bad intervals for RUNA with `GetAllTriggersByTower` **before** any
   averaging, so the no-trigger validity rule can actually be applied in Step 3 as well as Step 6.
   This is the one item that affects the main physics result, not just the optional step.
3. Record the 3990 s slice offset in `meta.json` and translate trigger times into slice coordinates
   in one place, with a test.
4. Widen the aux set to 1101-1123 if any SHRED code is reused.
5. Step 6 model 2 is now **an import plus data preparation**, not a model build, because
   `S4DDenoiser1D` exists and is tuned. The remaining work is shards in the
   `(numSlices, sliceLength, 1 + nAux)` layout, a stats file, and a config pointing at them. Far
   more feasible than this note first concluded -- though still gated behind stop point 4.
6. For the Step 3 interpretability comparison, the S4D poles convert to frequency and damping as the
   brief specifies, and `d_state 64` gives 32 complex modes per channel per layer to compare against
   `results/comparison.csv`.
