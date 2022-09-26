#!/usr/bin/env bats

setup() {
  source .workflow-scripts/utils/get_changed_files.sh
  source .workflow-scripts/utils/test/setup/setup_git.sh
  setup_git
}

@test "get_changed_files" {
  run get_changed_files
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Missing environment variable: EVENT_TYPE" ]

  export EVENT_TYPE="release"
  run get_changed_files
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "some/path/file_1" ]
  [ "${lines[1]}" == "some/path/file_2" ]
  [ "${lines[2]}" == "some/path/file_3" ]

  export EVENT_TYPE="push"
  run get_changed_files
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Missing environment variable: CHANGED_FILES" ]

  export CHANGED_FILES="file_1 file_2 file_3"
  run get_changed_files
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "file_1" ]
  [ "${lines[1]}" == "file_2" ]
  [ "${lines[2]}" == "file_3" ]
}
