#!/bin/bash
source .workflow-scripts/utils/get_changed_files.sh
source .workflow-scripts/utils/utils.sh

function get_related_tox_file {
  local FILE_ARG="$1"
  if [[ "$FILE_ARG" == "" ]]
  then
    echo "Missing argument: FILE_ARG"
    return 1
  fi
  local TOX_PATH=""
  IFS="/"
  read -a DIRS <<< "$FILE_ARG"
  for i in "${DIRS[@]}"
  do
    TOX_PATH="${TOX_PATH}${i}/"
    local TOX_FILE="${TOX_PATH}tox.ini"
    if [[ -f "$TOX_FILE" ]]
    then
      echo "${TOX_FILE}"
      return 0
    fi
  done
}

function get_changed_tox_directories {
  local CHANGED_FILES_ARRAY
  if ! CHANGED_FILES_ARRAY="$(get_changed_files)"
  then
    echo "Failed to get changed files"
    echo "${CHANGED_FILES_ARRAY[@]}"
    return 1
  fi

  local CHANGED_TOX_FILES=()
  local RELATED_TOX_FILE
  while IFS= read -r CHANGED_FILE; do
    if ! RELATED_TOX_FILE="$(get_related_tox_file "$CHANGED_FILE")"
    then
      echo "Failed to get tox file related to file $CHANGED_FILE"
      echo "$RELATED_TOX_FILE"
      return 1
    elif [[ "$RELATED_TOX_FILE" != "" ]]
    then
      if ! [[ " ${CHANGED_TOX_FILES[*]} " =~ ${RELATED_TOX_FILE} ]]
      then
        CHANGED_TOX_FILES+=("$RELATED_TOX_FILE")
        echo "${RELATED_TOX_FILE%%"/tox.ini"}"
      fi
    fi
  done <<< "${CHANGED_FILES_ARRAY[@]}"
}

function look_for_changed_tox_directories {
  local CHANGED_FILES_ARRAY
  if ! CHANGED_FILES_ARRAY="$(get_changed_files)"
  then
    echo "Failed to get changed files"
    echo "${CHANGED_FILES_ARRAY[@]}"
    return 1
  fi
  print_header "Changed files:"
  echo "${CHANGED_FILES_ARRAY[@]}"

  print_header "Folders to test with tox:"
  local TOX_DIRS
  if ! TOX_DIRS="$(get_changed_tox_directories)"
  then
    echo "Failed to get affected tox files"
    echo "${TOX_DIRS}"
    return 1
  elif [[ "${TOX_DIRS}" == "" ]]
  then
    echo "None"
  else
    split_string_by_space "$TOX_DIRS"
    echo "::set-output name=should_test::true"
    echo "TOX_DIRS=${TOX_DIRS}" >> $GITHUB_ENV
  fi
}
