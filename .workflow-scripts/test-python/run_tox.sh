#!/bin/bash
source .workflow-scripts/utils/utils.sh

# Kjører tox i en gitt liste av mapper. Listen er en enkelt streng delt med mellomrom
function run_tox {
  local TOX_DIRS="$1"
  if [[ "$TOX_DIRS" == "" ]]
  then
    echo "Missing argument: TOX_DIRS"
    return 1
  fi

  local TOX_DIRS_ARRAY
  if ! TOX_DIRS_ARRAY="$(split_string_by_space "$TOX_DIRS")"
  then
    echo "Failed to parse tox-directory array"
    echo "${TOX_DIRS_ARRAY[@]}"
    return 1
  fi

  local ROOT_DIR
  ROOT_DIR="$(pwd)"

  while IFS= read -r TOX_DIR; do
    if ! cd "$TOX_DIR"
    then
      echo "Failed to run command: cd $TOX_DIR"
      return 1
    fi
    tox -r
    if ! cd "$ROOT_DIR"
    then
      echo "Failed to run command: cd $ROOT_DIR"
      return 1
    fi
  done <<< "${TOX_DIRS_ARRAY[@]}"
}
