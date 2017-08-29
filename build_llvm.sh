#!/usr/bin/bash

set +e

cmake -DCMAKE_C_FLAGS="-march=native -Wno-gnu-statement-expression" \
      -DCMAKE_CXX_FLAGS="-march=native" \
      -DLLVM_ENABLE_EXPENSIVE_CHECKS=OFF -DLLVM_CCACHE_BUILD=On \
      -DCMAKE_BUILD_TYPE=Release -DLLVM_LINK_LLVM_DYLIB=On -DLLVM_ENABLE_ASSERTIONS=On \
      -DLLVM_LIT_ARGS=" -v -j 3" -GNinja $1
shift
ninja $*

echo "BUILD SUCCESS"
