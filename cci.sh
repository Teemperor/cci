#!/usr/bin/bash
set -o pipefail
set +e
LANG=C bash -x run_job.sh "$@" 2>&1 | ts "%H:%M:%S"
if [ $? -eq 0 ]; then
    echo "END OF LOG"
else
    echo "build failure"
fi
