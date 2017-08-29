#!/bin/bash

export CC="clang"
export CXX="clang++"
export PATH="/usr/lib/ccache/bin/:$PATH"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

while :
do
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
  bash -x ../../build_llvm.sh ../llvm  all  -j1 -l1
done
