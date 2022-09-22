#!/bin/bash

function get_changed_files {
  local TARGET_SHA="$1"
  if [[ "$TARGET_SHA" == "" ]]
  then
    echo "Failed to fetch changed files"
    echo "Missing argument: TARGET_SHA"
    return 1
  fi

  git diff --name-only "$TARGET_SHA"
}

function get_changed_services {
  local SERVICES=""
  while IFS= read -r FILE; do
    if [[ -f "$FILE" ]]
    then
      SERVICES="$SERVICES ${FILE%%"/serverless.yml"}"
    fi
  done <<< "$(echo "$GIT_DIFF" | grep "serverless.yml")"
  echo "$SERVICES"
}

