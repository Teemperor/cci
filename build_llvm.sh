#!/usr/bin/bash

set -e

export CC="clang"
export CXX="clang++"
export PATH="/usr/lib/ccache/bin/:$PATH"
export CCACHE_BASEDIR="`realpath ..`"
echo "$CCACHE_BASEDIR"

cmake -DCMAKE_C_FLAGS="-march=native -Wno-gnu-statement-expression" \
      -DCMAKE_CXX_FLAGS="-march=native" \
      -DLLVM_USE_SANITIZER="Address;Undefined" \
      -DLLVM_ENABLE_EXPENSIVE_CHECKS=OFF -DLLVM_CCACHE_BUILD=OFF \
      -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_ASSERTIONS=On \
      -DLLVM_LIT_ARGS=" -v -j 3" -DLLVM_PARALLEL_LINK_JOBS=1 -GNinja $1
shift
ninja $*

echo "BUILD SUCCESS"
