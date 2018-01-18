#!/usr/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

  cd $DIR
  cd llvm
  git pull
  cd tools/clang
  git pull
  cd tools/extra
  git pull
  cd $DIR

  rm -rf build
  mkdir build
  cd build
  ionice -t -c 3 nice -n 19 bash -x ../../build_llvm.sh ../llvm  all  -j1 -l1
  sleep 6h
