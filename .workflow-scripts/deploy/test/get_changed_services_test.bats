#!/usr/bin/env bats

setup(){
  source .workflow-scripts/deploy/get_changed_services.sh
  function git {
    local ARG_1="$1"
    local ARG_2="$2"
    if [[ "$ARG_1" == "show-ref" ]]
    then
      echo "abseafeawmawlwaef $ARG_2"
    elif [[ "$ARG_1" == "diff" ]]
    then
      echo -e "some/path/file_1\nsome/path/file_2\nsome/path/file_3"
    fi
  }
  function gh {
    if [[ "$1" == "api" ]]
    then
      local RESULT
      if [[ "$2" == "repos/knowit/dataplattform/releases/latest" ]]
      then
        RESULT='{"tag_name": "1.2.3", "target_commitish": "feature/main-cicd", "name": "1.2.3"}'
      elif [[ "$2" == "repos/knowit/dataplattform/releases" ]]
      then
        RESULT='[{"tag_name": "1.2.3", "target_commitish": "feature/main-cicd", "name": "1.2.3"}, {"tag_name": "test-release", "target_commitish": "feature/main-cicd","name": "Test release"}]'
      fi

      if [[ "$3" == "--jq" ]]
      then
        echo "$RESULT" | jq -r "$4"
      else
        echo "$RESULT"
      fi
    fi
  }
  mkdir -p "services/some"
  touch "services/some/serverless.yml"
}

teardown() {
  rm -r "services/some"
}

@test "split_string_by_space" {
  run split_string_by_space
  [ "$status" -eq 1 ]
  [ "$output" == "Missing argument: STRING" ]

  run split_string_by_space "one"
  [ "$status" -eq 0 ]
  [ "$output" == "one" ]

  run split_string_by_space "one two three"
  [ "$status" -eq 0 ]
  [ "$output" != "one two three" ]
  [ "${lines[0]}" == "one" ]
  [ "${lines[1]}" == "two" ]
  [ "${lines[2]}" == "three" ]
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

@test "get_changed_service_files" {
  function get_changed_files {
    echo "some/path/file_1"
    echo "services/some/path/file_2"
    echo "some/path/file_3"
    echo "services/some/path/file_4"
    echo "services"
  }

  run get_changed_service_files
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "services/some/path/file_2" ]
  [ "${lines[1]}" == "services/some/path/file_4" ]
}

@test "get_related_serverless_file" {
  run get_related_serverless_file
  [ "$status" -eq 1 ]
  [ "$output" == "Missing argument: SERVICE_FILE" ]

  run get_related_serverless_file "services/some/path/file_2"
  [ "$status" -eq 0 ]
  [ "$output" == "services/some/serverless.yml" ]
}

@test "get_changed_services" {

  function get_changed_files_in_release {
    echo "some/path/file_1 services/some/path/file_2 services/some/path/file_3 services/some/path/file_4"
  }

  run get_changed_services
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Failed to get changed service files" ]
  [ "${lines[1]}" == "Failed to get changed files" ]
  [ "${lines[2]}" == "Missing environment variable: EVENT_TYPE" ]

  export EVENT_TYPE="push"
  run get_changed_services
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Failed to get changed service files" ]
  [ "${lines[1]}" == "Failed to get changed files" ]
  [ "${lines[2]}" == "Missing environment variable: CHANGED_FILES" ]

  export CHANGED_FILES="some/path/file_1 services/some/path/file_2"
  run get_changed_services
  [ "$status" -eq 0 ]
  [ "$output" == "services/some" ]

  export EVENT_TYPE="release"
  export CHANGED_FILES=""
  run get_changed_services
  [ "$status" -eq 0 ]
  [ "$output" == "services/some" ]
}
