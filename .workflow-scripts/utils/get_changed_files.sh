#!/bin/bash
source .workflow-scripts/utils/git_utils.sh
source .workflow-scripts/utils/utils.sh

# Printer en liste med endrede filer, enten siden forrige push, endrede filer i en PR, eller i en release.

# EVENT_TYPE må settes til å være lik ${{ github.event_name }} i github workflow

# Hvis EVENT_TYPE er noe annet enn "release", så må CHANGED_FILES settes til å være en liste med endrede filer, i samme
# streng, delt med mellomrom. For "push" og "pull_request" kan CHANGED_FILES settes ved å bruke
# jitterbit/get-changed-files@v1

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
