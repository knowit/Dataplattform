#!/bin/bash
source .workflow-scripts/utils/git_utils.sh
source .workflow-scripts/utils/utils.sh

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
