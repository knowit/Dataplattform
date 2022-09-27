#!/usr/bin/env bats

setup(){
  source .workflow-scripts/deploy/get_changed_services.sh
  source .workflow-scripts/utils/test/setup/setup_git.sh
  setup_git
  mkdir -p "services/some"
  touch "services/some/serverless.yml"
}

teardown() {
  rm -r "services/some"
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

@test "look_for_changed_services" {

  run look_for_changed_services
  [ "$status" -eq 1 ]
  [ "${lines[0]}" == "Failed to get changed files" ]
  [ "${lines[1]}" == "Missing environment variable: EVENT_TYPE" ]

  export EVENT_TYPE="release"
  run look_for_changed_services
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "------------------------------" ]
  [ "${lines[1]}" == "| Changed files:" ]
  [ "${lines[2]}" == "------------------------------" ]
  [ "${lines[3]}" == "some/path/file_1" ]
  [ "${lines[4]}" == "some/path/file_2" ]
  [ "${lines[5]}" == "some/path/file_3" ]
  [ "${lines[6]}" == "------------------------------" ]
  [ "${lines[7]}" == "| Services to be deployed:" ]
  [ "${lines[8]}" == "------------------------------" ]
  [ "${lines[9]}" == "None" ]
  [ "${lines[10]}" == "" ]

  export EVENT_TYPE="push"
  export CHANGED_FILES="some/path/file_1 services/some/path/file_2 services/some/path/file_3 services/some/file_4"
  export GITHUB_ENV="services/some/output"
  run look_for_changed_services
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "------------------------------" ]
  [ "${lines[1]}" == "| Changed files:" ]
  [ "${lines[2]}" == "------------------------------" ]
  [ "${lines[3]}" == "some/path/file_1" ]
  [ "${lines[4]}" == "services/some/path/file_2" ]
  [ "${lines[5]}" == "services/some/path/file_3" ]
  [ "${lines[6]}" == "services/some/file_4" ]
  [ "${lines[7]}" == "------------------------------" ]
  [ "${lines[8]}" == "| Services to be deployed:" ]
  [ "${lines[9]}" == "------------------------------" ]
  [ "${lines[10]}" == "services/some" ]
  [ "${lines[11]}" == "::set-output name=should_deploy::true" ]
  [ "${lines[12]}" == "" ]
}
