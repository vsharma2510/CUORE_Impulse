#!/bin/bash
#SBATCH --account=<NERSC_ACCOUNT>
#SBATCH --constraint=cpu
#SBATCH --qos=shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --job-name=impulse_extract
#SBATCH --output=logs/slurm_extract_%j.out
#SBATCH --error=logs/slurm_extract_%j.err

# Step 1 bolometer extraction for the agent-graph pilot. Read-only on all CUORE data; writes only
# into $VIBES/output (pscratch) and this project.
#
# Measured cost basis: 32.4 s wall and 172 MB RSS for one channel over the 17,770 s window.
# 283 channel-extractions in total, 13 in parallel  ->  about 5 min expected, 30 min requested.
# Charge: 16 of 128 cores for <= 0.5 h  =  about 0.06 node-hours.

set -uo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs
echo "host $(hostname)  job ${SLURM_JOB_ID}  started $(date -u +%FT%TZ)"
WORKERS=13 ./extract/extract_step1.sh
echo "finished $(date -u +%FT%TZ)"
