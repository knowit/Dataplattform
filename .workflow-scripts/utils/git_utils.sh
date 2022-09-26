#!/bin/bash

function get_previous_release {
  local LATEST_TAG
  local LATEST_TAG_BRANCH
  LATEST_TAG="$(gh api repos/knowit/dataplattform/releases/latest --jq .tag_name)"
  LATEST_TAG_BRANCH="$(gh api repos/knowit/dataplattform/releases/latest --jq .target_commitish)"
  gh api repos/knowit/dataplattform/releases | jq -r -c ".[] | select( .target_commitish == \"$LATEST_TAG_BRANCH\" ) | select( .tag_name != \"$LATEST_TAG\" ) | .tag_name"
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
