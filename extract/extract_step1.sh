#!/usr/bin/env bash
# Step 1 extraction, Route A. Writes raw .bin via the vibes writer; conversion to float32 .npy
# under data/ is a separate, cheap step (extract/to_npy.py).
#
#   WORKERS=13 ./extract/extract_step1.sh            # run it
#   DRYRUN=1   ./extract/extract_step1.sh            # print the command plan and exit
#
# Measured on 2026-10-31: one channel over the 17,770 s window takes 32.4 s wall, 172 MB RSS.
# Everything is read from /global/cfs/.../syncData/CUORE/ContinuousData/run<R>/ -- nothing is staged
# or copied, and CUORE data are only ever read.

set -o pipefail
cd "$(dirname "$0")/.."
source extract/vibes_env.sh

WORKERS="${WORKERS:-13}"
BOLO="937...988"                 # all 52 tower-19 bolometers
AUX="1101...1123"                # sb540 aux set; the writer skips any that do not exist

# run  tstart  tend     channels   label
JOBS=(
  "RUNA 3990  21760   $BOLO     excitation 2.52-9.52 Hz, 71 drive steps"
  "RUNA 0     250     $BOLO     quiet in-run segment 1"
  "RUNA 1275  1500    $BOLO     quiet in-run segment 2 (the 225 s shaker dropout)"
  "RUNA 48025 48800   $BOLO     quiet in-run segment 3"
  "RUNB 0     2456    $BOLO     quiet reference run, 40.9 min, sb540 pedestal"
  "RUNB 0     2456    $AUX      quiet reference run, aux channels"
)

# Expand "a...b" / "a,b" into a flat list so the channel set can be split across workers.
expand() {
  local spec="$1" out=() part
  IFS=',' read -ra parts <<< "${spec//.../-}"
  for part in "${parts[@]}"; do
    if [[ "$part" == *-* ]]; then
      out+=( $(seq "${part%%-*}" "${part##*-}") )
    else
      out+=( "$part" )
    fi
  done
  echo "${out[@]}"
}

join_commas() { local IFS=','; echo "$*"; }

total=0
for job in "${JOBS[@]}"; do
  read -r run t0 t1 chans label <<< "$job"
  all=( $(expand "$chans") )
  n=${#all[@]}
  per=$(( (n + WORKERS - 1) / WORKERS ))
  echo "=== run $run  t=[$t0, $t1] s  ${n} channels  --  $label"
  i=0
  while (( i < n )); do
    chunk=( "${all[@]:i:per}" )
    spec=$(join_commas "${chunk[@]}")
    if [[ -n "${DRYRUN:-}" ]]; then
      echo "    WriteContinuousDataToBinary -r $run -c $spec -t $t0 -T $t1"
    else
      WriteContinuousDataToBinary -r "$run" -c "$spec" -t "$t0" -T "$t1" \
        > "logs/extract_${run}_${t0}_${t1}_${i}.log" 2>&1 &
    fi
    total=$(( total + ${#chunk[@]} ))
    i=$(( i + per ))
  done
  [[ -z "${DRYRUN:-}" ]] && wait
done

echo
echo "channel-extractions issued: $total"
[[ -n "${DRYRUN:-}" ]] && { echo "(dry run, nothing executed)"; exit 0; }

echo "=== failures, if any ==="
grep -lE "Skip|Failed|error" logs/extract_*.log 2>/dev/null || echo "none"
echo "=== files written ==="
for run in RUNA RUNB; do
  d="$VIBES/output/run$run/timestreams"
  [[ -d "$d" ]] && printf '%s : %d files, %s\n' "run$run" "$(ls "$d" | wc -l)" "$(du -sh "$d" | cut -f1)"
done
