#!/bin/bash

function setup_git {
  function git {
    local ARG_1="$1"
    local ARG_2="$2"
    if [[ "$ARG_1" == "show-ref" ]]
    then
      echo "abseafeawmawlwaef $ARG_2"
    elif [[ "$ARG_1" == "diff" || "$ARG_1" == "ls-tree" ]]
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
}
