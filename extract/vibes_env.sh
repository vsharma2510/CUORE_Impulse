#!/usr/bin/env bash
# Environment for the Step 1 bolometer extraction (Route A).
#
# Sourced, not executed:  source extract/vibes_env.sh
#
# Three things have to be true and none of them is the default:
#
#   1. DIANA must come from $CUORE_INSTALL. The ~/.bashrc lines that were meant to source it are all
#      commented out and all three paths they name are missing (log E005).
#   2. VIBES must point at a checkout that actually has src/VibesUtil.hh. The long-standing checkout
#      on cfs is at master of 2025-08-02 and does not (log E010); this uses a fresh clone of GitLab
#      `main` instead.
#   3. The CUORE DB endpoint advertised by cuoresw/setup.sh (stuart.lbl.gov:5432) REFUSES
#      connections. The only reachable endpoint is the override that was hand-added to the old
#      checkout's setup.sh. `make` regenerates setup.sh from a template that omits that override, so
#      a fresh clone silently loses it. We re-import those four variables at runtime from the old
#      file, which keeps the password in the one place it already lives -- it is never copied into
#      this repo, printed, or logged.

VIBES_FRESH="${VIBES_FRESH:-<SCRATCH>/vibes_main}"
VIBES_OLD="${VIBES_OLD:-<CUORE_SCRATCH>/vibes}"

# cuoresw/setup.sh reads variables that may be unset, which is fatal under `set -u` in a
# non-interactive shell, so relax it across the source and restore afterwards.
_had_u=0; case "$-" in *u*) _had_u=1;; esac
set +u
source /global/common/software/<NERSC_ACCOUNT>/csoft13/soft/cuoresw/setup.sh >/dev/null 2>&1
[ "$_had_u" = 1 ] && set -u
unset _had_u

export VIBES="$VIBES_FRESH"
export PATH="$VIBES/bin:$PATH"

# DB override, imported quietly. No echo, no set -x, nothing written to disk.
eval "$(grep -E '^export CUORE_DB_(HOST|PORT|USER|PWD)=' "$VIBES_OLD/setup.sh")"

echo "  [env] CUORE_INSTALL = $CUORE_INSTALL"
echo "  [env] VIBES         = $VIBES"
echo "  [env] CUORE_DB_HOST = ${CUORE_DB_HOST}:${CUORE_DB_PORT} (user ${CUORE_DB_USER}, password set: $([ -n "$CUORE_DB_PWD" ] && echo yes || echo NO))"
