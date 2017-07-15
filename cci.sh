#!/usr/bin/bash

set +e
LANG=C bash -x run_job.sh "$@" 2>&1 | ts "%H:%M:%S"
some_command
if [ $? -eq 0 ]; then
    echo "END OF LOG"
else
    echo "build failure"
fi
