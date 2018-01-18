#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

while :
do
  python rep.py
  echo "Rep stopped"
  date
  sleep 1
done
