#!/bin/bash

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
  local CHANGED_FILES

  if [[ "$EVENT_TYPE" == "" ]]
  then
    echo "Missing environment variable: EVENT_TYPE"
    return 1

  elif [[ "$EVENT_TYPE" == "push" && "$CHANGED_FILES" == "" ]]
  then
    echo "Missing environment variable: CHANGED_FILES"
    return 1

  elif [[ "$EVENT_TYPE" == "release" ]]
  then
      if ! CHANGED_FILES="$(get_changed_files_in_release)"
      then
        echo "Failed to get changed files in release"
        echo "$CHANGED_FILES"
        return 1
      fi
  fi

  read -A FILES <<< $CHANGED_FILES
  for file in $FILES
  do
    echo "$file"
  done
}

function get_changed_service_files {
  while IFS= read -r FILE; do
    if [[ "$FILE" == "services/*" ]]
    then
      echo "$FILE"
    fi
  done <<< "$(get_changed_files)"
}

function get_changed_services_in_release {
  local SERVICES=""
  while IFS= read -r FILE; do
    if [[ -f "$FILE" ]]
    then
      SERVICES="$SERVICES ${FILE%%"/serverless.yml"}"
    fi
  done <<< "$(get_changed_files_in_release | grep "serverless.yml")"

  if [[ "$SERVICES" != "" ]]
  then
    echo "$SERVICES"
  fi
}
