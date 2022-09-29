#!/bin/bash

# Finn taggen til forrige release, altså den som kom før "latest"
function get_previous_release {
  local LATEST_TAG
  local LATEST_TAG_BRANCH
  LATEST_TAG="$(gh api repos/knowit/dataplattform/releases/latest --jq .tag_name)"
  LATEST_TAG_BRANCH="$(gh api repos/knowit/dataplattform/releases/latest --jq .target_commitish)"
  gh api repos/knowit/dataplattform/releases | jq -r -c ".[] | select( .target_commitish == \"$LATEST_TAG_BRANCH\" ) | select( .tag_name != \"$LATEST_TAG\" ) | .tag_name"
}

# Printer SHA til en gitt tag
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

# Printer SHA til forrige release
function get_previous_release_sha {
  local TAG_NAME
  if ! TAG_NAME="$(get_previous_release)"
  then
    echo "Failed to get previous release name"
    echo "$TAG_NAME"
    return 1
  elif [[ "$TAG_NAME" == "" ]]
  then
    return 0
  fi

  local TAG_SHA
  if ! TAG_SHA="$(get_tag_sha "$TAG_NAME")"
  then
    echo "Failed to get SHA for tag $TAG_NAME"
    echo "$TAG_SHA"
    return 1
  fi

  echo "$TAG_SHA"
}

# Printer diffen mellom nåværende branch og en gitt SHA
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

function list_all_files_in_branch {
  if [[ "$CURRENT_BRANCH_NAME" == "" ]]
  then
    echo "Missing environment variable: CURRENT_BRANCH_NAME"
    return 1
  fi
  git ls-tree -r "$CURRENT_BRANCH_NAME" --name-only
}

# Printer en liste med alle filer som er endret i nåværende release
function get_changed_files_in_release {
  local PREV_SHA
  local DIFF
  if ! PREV_SHA="$(get_previous_release_sha)"
  then
    echo "Failed to fetch list of changed files in release"
    echo "$PREV_SHA"
    return 1

  # Dersom det ikke finnes noen release fra før, print alle filer
  elif [[ "$PREV_SHA" == "" ]]
  then
    if ! DIFF="$(list_all_files_in_branch)"
    then
      echo "$DIFF"
      return 1
    fi

  # Dersom det finnes en tidligere release, print diff mellom denne og forrige release
  else
    if ! DIFF="$(get_diff_by_sha "$PREV_SHA")"
    then
      echo "$DIFF"
      return 1
    fi

    # Print liste med filer på samme linje separert med mellomrom
    local FILES=""
    while IFS= read -r FILE; do
      FILES="$FILES $FILE"
    done <<< "$DIFF"
    if [[ "$FILES" != "" ]]
    then
      echo "$FILES"
    fi
  fi
}
