#!/usr/bin/env bash 
JOBID="${1:-1090}"
export RREPO_PATH=$(pwd)/../OCTAD_core
export RREPO_OUTPUT=$(pwd)/static/data
export R_LIBS="$RREPO_PATH/renv/library/R-3.6/x86_64-apple-darwin15.6.0"
Rscript $RREPO_PATH/compute_sRGES_from_signatures.R $JOBID $RREPO_OUTPUT/$JOBID/dz_signature.csv true 50 1

