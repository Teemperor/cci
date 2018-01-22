#!/usr/bin/bash

to_check=""

function try_rebase {
  # Try to rebase
  set +e
  git checkout "$git_branch"
  git reset --hard "teemperor/$git_branch"
  if [ $? -eq 0 ]; then
    current_project=$(basename "$PWD")
    echo "Adding $current_project to test queue"
    to_check="$to_check check-$current_project"
  fi

  git rebase master
  if [ $? -eq 0 ]; then
    echo "REBASE OK"
  else
    git rebase --abort
    echo "!!!REBASE FAILED!!!"
    exit 1
  fi
  set -e
}

function clang_format_check {
  set +e
  git clang-format --diff master
  git clang-format --diff master | grep -q "clang-format did not modify any files"
  if [ $? -eq 0 ]; then
    echo "CLANG-FORMAT-OK"
  else
    echo "CLANG-FORMAT-FAIL"
  fi
  git clang-format master
  set -e
}

function prepare_project {
  git reset --hard
  git clean -fd
  git checkout master
  git pull
  git fetch -a origin
  git fetch -a teemperor
  try_rebase
  clang_format_check
}

date

set -e

ccache -s
export CC="clang"
export CXX="clang++"

export PATH="/usr/lib/ccache/bin/:$PATH"

JOB="$1"

git_branch="$JOB"

cd llvm
prepare_project

cd tools/clang
prepare_project

cd ../lldb
prepare_project

cd ../../..

rm -rf build
mkdir build
cd build
ionice -t -c 3 nice -n 19 bash -x ../build_llvm.sh ../llvm all $to_check -j3
