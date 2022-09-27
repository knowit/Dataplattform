#!/usr/bin/env bats

setup(){
  source .workflow-scripts/test-python/get_tox_changes.sh
  source .workflow-scripts/utils/test/setup/setup_git.sh
  setup_git
  mkdir -p "services/some"
  touch "services/some/tox.ini"
  mkdir -p "services/some_other"
  touch "services/some_other/tox.ini"
}

teardown() {
  rm -r "services/some"
  rm -r "services/some_other"
}

@test "get_related_tox_file" {
  run get_related_tox_file
  [ "$status" -eq 1 ]
  [ "$output" == "Missing argument: FILE_ARG" ]
}

@test "get_changed_tox_directories" {
  run get_changed_tox_directories
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Failed to get changed files" ]
  [ "${lines[1]}" == "Missing environment variable: EVENT_TYPE" ]

  export EVENT_TYPE="pull_request"
  run get_changed_tox_directories
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Failed to get changed files" ]
  [ "${lines[1]}" == "Missing environment variable: CHANGED_FILES" ]

  export CHANGED_FILES="some/path/file_1 services/some/path/file_2.py services/some/path/file_3 services/some_other/file_4"
  run get_changed_tox_directories
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "services/some services/some_other" ]
  [ "${lines[1]}" == "" ]
}

@test "look_for_changed_tox_directories" {
  run look_for_changed_tox_directories
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Failed to get changed files" ]
  [ "${lines[1]}" == "Missing environment variable: EVENT_TYPE" ]

  export EVENT_TYPE="pull_request"
  run look_for_changed_tox_directories
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Failed to get changed files" ]
  [ "${lines[1]}" == "Missing environment variable: CHANGED_FILES" ]

  export CHANGED_FILES="some/path/file_1 services/some/path/file_2.py services/some/path/file_3 services/some_other/file_4"
  export GITHUB_ENV="services/some/output"
  run look_for_changed_tox_directories
  echo "$output"
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "------------------------------" ]
  [ "${lines[1]}" == "| Changed files:" ]
  [ "${lines[2]}" == "------------------------------" ]
  [ "${lines[3]}" == "some/path/file_1" ]
  [ "${lines[4]}" == "services/some/path/file_2.py" ]
  [ "${lines[5]}" == "services/some/path/file_3" ]
  [ "${lines[6]}" == "services/some_other/file_4" ]
  [ "${lines[7]}" == "------------------------------" ]
  [ "${lines[8]}" == "| Folders to test with tox:" ]
  [ "${lines[9]}" == "------------------------------" ]
  [ "${lines[10]}" == "services/some" ]
  [ "${lines[11]}" == "services/some_other" ]
  [ "${lines[12]}" == "::set-output name=should_test::true" ]
  [ "${lines[13]}" == "" ]
}
