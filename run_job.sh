#!/usr/bin/bash

date

set -e

ccache -s
export CC="clang"
export CXX="clang++"

export PATH="/usr/lib/ccache/bin/:$PATH"

JOB="$1"

git_target=false
git_branch=""
if [[ "$JOB" =~ ^git:* ]]; then
  git_target=true
  git_branch=$(echo "$JOB" | cut -c 5-)
else
  wget "https://reviews.llvm.org/${JOB}?download=true" -O patch.diff
fi

cd llvm
git reset --hard
git clean -fd
git checkout master
git pull
git fetch -a origin
git fetch -a teemperor

if [ "$git_target" = true ] ; then
  set +e
  git checkout "$git_branch"
  git reset --hard "teemperor/$git_branch"
  git rebase master || git rebase --abort
  set -e
fi

cd projects/compiler-rt
git reset --hard
git clean -fd
git pull
cd ../..

cd tools/clang/tools/extra
git reset --hard
git clean -fd
git pull

cd ../..
git reset --hard
git clean -fd
git checkout master
git pull
git fetch -a origin
git fetch -a teemperor

if [ "$git_target" = true ] ; then
  git checkout "$git_branch"
  git reset --hard "teemperor/$git_branch"
  git rebase master
  if [ $? -eq 0 ]; then
    echo "REBASE OK"
  else
    git rebase --abort
    echo "!!!REBASE FAILED!!!"
  fi
fi

set +e

if [ "$git_target" = true ] ; then
  git clang-format --diff HEAD^
  git clang-format --diff HEAD^ | grep -q "clang-format did not modify any files"
  if [ $? -eq 0 ]; then
    echo "CLANG-FORMAT-OK"
  else
    echo "CLANG-FORMAT-FAIL"
  fi
else
  echo "Trying with -p0"
  patch --dry-run -f -p0 < ../../../patch.diff
  if [ $? -eq 0 ]; then
    patch -f -p0 < ../../../patch.diff
    echo "Used -p0"
  else
    echo "Trying with -p1"
    patch --dry-run -f -p1 < ../../../patch.diff
    if [ $? -eq 0 ]; then
      echo "Using -p1"
      patch -f -p1 < ../../../patch.diff
    else
      echo "Patch file: "
      cat ../../../patch.diff
      echo "Giving up to patch file"
      exit 1
    fi
  fi
  git add *
  git clang-format --diff
  git clang-format --diff | grep -q "clang-format did not modify any files"
  if [ $? -eq 0 ]; then
    echo "CLANG-FORMAT-OK"
  else
    echo "CLANG-FORMAT-FAIL"
  fi
fi
set -e

cd ../../..

rm -rf build
mkdir build
cd build
cmake -DCMAKE_C_FLAGS="-march=native -Wno-gnu-statement-expression" \
      -DCMAKE_CXX_FLAGS="-march=native" \
      -DLLVM_ENABLE_EXPENSIVE_CHECKS=ON -DLLVM_CCACHE_BUILD=On \
      -DCMAKE_BUILD_TYPE=Release -DLLVM_LINK_LLVM_DYLIB=On -DLLVM_ENABLE_ASSERTIONS=On \
      -DLLVM_LIT_ARGS="-v -j 3" -GNinja ../llvm
ninja all check-clang -j3 -l 3

echo "BUILD SUCCESS"
