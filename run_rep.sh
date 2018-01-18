#!/usr/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

while :
do
	python rep.py
	echo "rep.py crashed :("
	sleep 1
done
