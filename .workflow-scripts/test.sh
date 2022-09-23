#!/bin/bash

function split_string_by_space {
  local STRING="$1"
  if [[ "$STRING" == "" ]]
  then
    echo "Missing argument: STRING"
    return 1
  fi
  IFS=' '
  read -a WORDS <<< "$STRING"
  for word in "${WORDS[@]}"
  do
    echo "$word"
  done
}

function get_previous_release {
  local LATEST_TAG
  local LATEST_TAG_BRANCH
  LATEST_TAG="$(gh api repos/knowit/dataplattform/releases/latest --jq .tag_name)"
  LATEST_TAG_BRANCH="$(gh api repos/knowit/dataplattform/releases/latest --jq .target_commitish)"
  gh api repos/knowit/dataplattform/releases | jq -r -c ".[] | select( .target_commitish == \"$LATEST_TAG_BRANCH\" ) | select( .name != \"$LATEST_TAG\" ) | .tag_name"
}

function get_tag_sha {
  local TAG_NAME="$1"
  if [[ "$TAG_NAME" == "" ]]
  then
    echo "Failed to get tag SHA"
    echo "Missing argument: TAG_NAME"
    return 1
  fi

  git fetch --all
  git show-ref "$TAG_NAME" | cut -f 1 -d " "
}

function get_previous_release_sha {
  local TAG_NAME
  if ! TAG_NAME="$(get_previous_release)"
  then
    echo "$TAG_NAME"
    return 1
  fi

  local TAG_SHA
  if ! TAG_SHA="$(get_tag_sha "$TAG_NAME")"
  then
    echo "$TAG_SHA"
    return 1
  fi

  echo "$TAG_SHA"
}

function get_diff_by_sha {
  local TARGET_SHA="$1"
  if [[ "$TARGET_SHA" == "" ]]
  then
    echo "Failed to fetch changed files"
    echo "Missing argument: TARGET_SHA"
    return 1
  fi

  git diff --name-only "$TARGET_SHA"
}

function get_changed_files_in_release {
  local PREV_SHA
  if ! PREV_SHA="$(get_previous_release_sha)"
  then
    echo "Failed to fetch list of changed files in release"
    echo "$PREV_SHA"
    return 1
  fi

  local DIFF
  if ! DIFF="$(get_diff_by_sha "$PREV_SHA")"
  then
    echo "$DIFF"
    return 1
  fi

  local FILES=""
  while IFS= read -r FILE; do
    FILES="$FILES $FILE"
  done <<< "$DIFF"

  if [[ "$FILES" != "" ]]
  then
    echo "$FILES"
  fi
}

function get_changed_files {
  if [[ "$EVENT_TYPE" == "" ]]
  then
    echo "Missing environment variable: EVENT_TYPE"
    return 1

  elif [[ "$EVENT_TYPE" == "release" ]]
  then
      if ! CHANGED_FILES="$(get_changed_files_in_release)"
      then
        echo "Failed to get changed files in release"
        echo "$CHANGED_FILES"
        return 1
      fi

  elif [[ "$CHANGED_FILES" == "" ]]
  then
    echo "Missing environment variable: CHANGED_FILES"
    return 1
  fi

  split_string_by_space "$CHANGED_FILES"
}

function get_changed_service_files {
  local CHANGED_FILES_ARRAY
  if ! CHANGED_FILES_ARRAY="$(get_changed_files)"
  then
    echo "Failed to get changed files"
    echo "$CHANGED_FILES_ARRAY"
    return 1
  fi
  while IFS= read -r FILE; do
    if [[ "$FILE" == services/* ]]
    then
      echo "$FILE"
    fi
  done <<< "${CHANGED_FILES_ARRAY[@]}"
}

function get_related_serverless_file {
  local SERVICE_FILE="$1"
  if [[ "$SERVICE_FILE" == "" ]]
  then
    echo "Missing argument: SERVICE_FILE"
    return 1
  fi
  local SERVICE_PATH=""
  IFS="/"
  read -a FILES <<< "$SERVICE_FILE"
  for i in "${FILES[@]}"
  do
    SERVICE_PATH="$SERVICE_PATH$i/"
    SERVERLESS_PATH="${SERVICE_PATH}serverless.yml"
    if [[ -f "$SERVERLESS_PATH" ]]
    then
      echo "$SERVERLESS_PATH"
      return
    fi
  done
}

function get_changed_services {
  local SERVICES=()
  local CHANGED_SERVICE_FILES
  if ! CHANGED_SERVICE_FILES="$(get_changed_service_files)"
  then
    echo "Failed to get changed service files"
    echo "$CHANGED_SERVICE_FILES"
    return 1
  fi

  if [[ "$CHANGED_SERVICE_FILES" == "" ]]
  then
    return
  fi

  while IFS= read -r FILE; do
    if ! SERVERLESS_FILE="$(get_related_serverless_file "$FILE")"
    then
      echo "Failed to find related serverless file: $FILE"
      echo "$SERVERLESS_FILE"
      return 1
    fi
    SERVICE="${SERVERLESS_FILE%%"/serverless.yml"}"
    if ! [[ " ${SERVICES[*]} " =~ ${SERVICE} ]]
    then
      SERVICES+=("$SERVICE")
    fi
  done <<< "${CHANGED_SERVICE_FILES[@]}"
  echo "${SERVICES[*]}"
}

function print_header {
  local MSG="$1"
  if [[ "$MSG" == "" ]]
  then
    echo "Missing argument: MSG"
    return 1
  fi
  echo -e "\n------------------------------"
  echo "| $MSG"
  echo "------------------------------"
}

function look_for_changed_services {
  print_header "Changed files:"
  get_changed_files

  print_header "Services to be deployed:"

  local SERVICES
  if ! SERVICES="$(get_changed_services)"
  then
    echo "Failed to get changed services"
    echo "${SERVICES}"
    exit 1

  elif [[ "${SERVICES}" == "" ]]
  then
    echo "None"

  else
    echo "::set-output name=should_deploy::true"
    echo -e "SERVICES=\"${SERVICES}\"" >> $GITHUB_ENV
    echo "$SERVICES"
    split_string_by_space "$SERVICES"
  fi
}
