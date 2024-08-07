#!/bin/bash

set -e

while getopts ":p:b:h" opt; do
  case ${opt} in
    p )
      SEARCH_PATH=$OPTARG
      ;;
    b )
      BUILD_DIR=$OPTARG
      ;;
    h )
      ;;
    \? )
      echo "Invalid option: $OPTARG" 1>&2
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      ;;
  esac
done
shift $((OPTIND -1))

if [[ $BUILD_DIR == "" ]]; then
  BUILD_DIR="build"
fi

for file in $(find "$SEARCH_PATH" -name samconfig.toml -print0 | xargs -0 realpath); do
  path=$(dirname "$file")
  cd "$path" || { echo "Failed to change dir to $path"; exit 1; }
  rm -fr "$path/build"
done
