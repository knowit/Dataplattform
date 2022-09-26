#!/usr/bin/env bats

setup() {
  source .workflow-scripts/utils/git_utils.sh
  source .workflow-scripts/utils/test/setup/setup_git.sh
  setup_git
}

@test "get_previous_release" {
  run get_previous_release
  [ "$status" -eq 0 ]
  [ "$output" == "test-release" ]
}

@test "get_tag_sha" {
  run get_tag_sha
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Failed to get tag SHA" ]
  [ "${lines[1]}" == "Missing argument: TAG_NAME" ]

  run get_tag_sha "Some_name"
  echo "$output"
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "abseafeawmawlwaef" ]
  [ "${lines[1]}" == "" ]
}

@test "get_previous_release_sha" {
  run get_previous_release_sha
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "abseafeawmawlwaef" ]
  [ "${lines[1]}" == "" ]
}

@test "get_diff_by_sha" {
  run get_diff_by_sha
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Failed to fetch changed files" ]
  [ "${lines[1]}" == "Missing argument: TARGET_SHA" ]

  run get_diff_by_sha "Some_name"
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "some/path/file_1" ]
  [ "${lines[1]}" == "some/path/file_2" ]
  [ "${lines[2]}" == "some/path/file_3" ]
}

@test "get_changed_files_in_release" {
  run get_changed_files_in_release
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == " some/path/file_1 some/path/file_2 some/path/file_3" ]
}
