#!/bin/bash

function split_string_by_space {
  local STRING="$1"
  if [[ "$STRING" == "" ]]
  then
    echo "Missing argument: STRING"
    return 1
  fi
  IFS=' '
  read -a WORDS <<< "$STRING"
  for word in "${WORDS[@]}"
  do
    echo "$word"
  done
}

function print_header {
  local MSG="$1"
  if [[ "$MSG" == "" ]]
  then
    echo "Missing argument: MSG"
    return 1
  fi
  echo -e "\n------------------------------"
  echo "| $MSG"
  echo "------------------------------"
}
