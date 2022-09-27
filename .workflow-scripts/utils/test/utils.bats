#!/usr/bin/env bats

setup() {
  source .workflow-scripts/utils/utils.sh
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

@test "print_header" {
  run print_header
  [ "$status" -eq 1 ]
  [ "$output" == "Missing argument: MSG" ]

  run print_header "one two three"
  echo "$output"
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "------------------------------" ]
  [ "${lines[1]}" == "| one two three" ]
  [ "${lines[2]}" == "------------------------------" ]
}
