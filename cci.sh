#!/usr/bin/bash

LANG=C bash -x run_job.sh "$@" 2>&1 | ts
