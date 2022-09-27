#!/bin/bash
source .workflow-scripts/utils/get_changed_files.sh
source .workflow-scripts/utils/utils.sh

# Ser etter en tox.ini fil i pathen til en gitt fil.
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

# Printer en liste av alle mapper som både inneholder en endret fil og en tox.ini fil.
function get_changed_tox_directories {
  local CHANGED_FILES_ARRAY
  if ! CHANGED_FILES_ARRAY="$(get_changed_files)"
  then
    echo "Failed to get changed files"
    echo "${CHANGED_FILES_ARRAY[@]}"
    return 1
  fi

  local CHANGED_TOX_DIRECTORIES=()
  local RELATED_TOX_FILE
  while IFS= read -r CHANGED_FILE; do
    if ! RELATED_TOX_FILE="$(get_related_tox_file "$CHANGED_FILE")"
    then
      echo "Failed to get tox file related to file $CHANGED_FILE"
      echo "$RELATED_TOX_FILE"
      return 1
    elif [[ "$RELATED_TOX_FILE" != "" ]]
    then
      local CHANGED_TOX_DIRECTORY="${RELATED_TOX_FILE%%"/tox.ini"}"
      if ! [[ " ${CHANGED_TOX_DIRECTORIES[*]} " =~ ${CHANGED_TOX_DIRECTORY} ]]
      then
        CHANGED_TOX_DIRECTORIES+=("$CHANGED_TOX_DIRECTORY")
      fi
    fi
  done <<< "${CHANGED_FILES_ARRAY[@]}"

  if ! [[ "${CHANGED_TOX_DIRECTORIES[*]}" == "" ]]
  then
    echo "${CHANGED_TOX_DIRECTORIES[*]}"
  fi
}

# Printer en liste med alle endrede filer
# Printer deretter en liste med alle mapper med tox.ini fil som også inneholder endrede filer
# Til slutt settes nødvendige outputs for å kunne kjøre run_tox.sh i neste steg i workflowen
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
