#!/usr/bin/env bats

setup(){
  source .workflow-scripts/test-python/run_tox.sh
  mkdir -p "services/some"
  mkdir -p "services/some_other"
  touch "services/some/tox.ini"
  touch "services/some_other/tox.ini"
  export ROOT_DIR="$(pwd)"

  function tox {
    local ARG_1="$1"
    local TOX_DIR
    TOX_DIR="$(pwd)"
    echo "${TOX_DIR##"$ROOT_DIR"}"
  }
}

teardown() {
  rm -r "services/some"
  rm -r "services/some_other"
}

@test "run_tox" {
  run run_tox
  [ "$status" -eq 1 ]
  [ "$output" == "Missing argument: TOX_DIRS" ]

  run run_tox "services/some services/some_other"
  [ "$status" -eq 0 ]
  [ "${lines[0]}" == "/services/some" ]
  [ "${lines[1]}" == "/services/some_other" ]
}
