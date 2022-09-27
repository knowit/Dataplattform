#!/bin/bash
source .workflow-scripts/utils/utils.sh
source .workflow-scripts/utils/get_changed_files.sh

# Printer en liste av alle endrede filer som befinner seg i services-mappen
function get_changed_service_files {
  local CHANGED_FILES_ARRAY
  if ! CHANGED_FILES_ARRAY="$(get_changed_files)"
  then
    echo "Failed to get changed files"
    echo "$CHANGED_FILES_ARRAY"
    return 1
  fi
  while IFS= read -r FILE; do
    if [[ "$FILE" == services/* ]]
    then
      echo "$FILE"
    fi
  done <<< "${CHANGED_FILES_ARRAY[@]}"
}

# Finner en serverless.yml fil i pathen til en gitt fil
function get_related_serverless_file {
  local SERVICE_FILE="$1"
  if [[ "$SERVICE_FILE" == "" ]]
  then
    echo "Missing argument: SERVICE_FILE"
    return 1
  fi
  local SERVICE_PATH=""
  IFS="/"
  read -a FILES <<< "$SERVICE_FILE"
  for i in "${FILES[@]}"
  do
    SERVICE_PATH="$SERVICE_PATH$i/"
    SERVERLESS_PATH="${SERVICE_PATH}serverless.yml"
    if [[ -f "$SERVERLESS_PATH" ]]
    then
      echo "$SERVERLESS_PATH"
      return
    fi
  done
}

# Printer en liste av alle mapper som inneholder både en serverless.yml fil og endrede filer
function get_changed_services {
  local SERVICES=()
  local CHANGED_SERVICE_FILES
  if ! CHANGED_SERVICE_FILES="$(get_changed_service_files)"
  then
    echo "Failed to get changed service files"
    echo "$CHANGED_SERVICE_FILES"
    return 1
  fi

  if [[ "$CHANGED_SERVICE_FILES" == "" ]]
  then
    return
  fi

  while IFS= read -r FILE; do
    if ! SERVERLESS_FILE="$(get_related_serverless_file "$FILE")"
    then
      echo "Failed to find related serverless file: $FILE"
      echo "$SERVERLESS_FILE"
      return 1
    fi
    SERVICE="${SERVERLESS_FILE%%"/serverless.yml"}"
    if ! [[ " ${SERVICES[*]} " =~ ${SERVICE} ]]
    then
      SERVICES+=("$SERVICE")
    fi
  done <<< "${CHANGED_SERVICE_FILES[@]}"
  echo "${SERVICES[*]}"
}

# Printer en liste med alle endrede filer
# Printer deretter en liste med alle mapper med serverless.yml fil som også inneholder endrede filer
# Til slutt settes nødvendige outputs for å kunne kjøre dataplattform deploy i neste steg i workflowen
function look_for_changed_services {
  local CHANGED_FILES_ARRAY
  if ! CHANGED_FILES_ARRAY="$(get_changed_files)"
  then
    echo "Failed to get changed files"
    echo "${CHANGED_FILES_ARRAY[@]}"
    return 1
  fi
  print_header "Changed files:"
  echo "${CHANGED_FILES_ARRAY[@]}"
  local DEPLOY_ALL="false"
  while IFS= read -r FILE; do
    if [[ "$FILE" == packages/query/* ]] || [[ "$FILE" == packages/api/* ]] || [[ "$FILE" == packages/common/* ]]
    then
      DEPLOY_ALL="true"
    fi
  done <<< "${CHANGED_FILES_ARRAY[@]}"

  print_header "Services to be deployed:"
  local SERVICES
  if [[ "$DEPLOY_ALL" == "true" ]]
  then
    echo "All"
    echo "::set-output name=should_deploy::true"
    echo "SERVICES=." >> $GITHUB_ENV

  elif ! SERVICES="$(get_changed_services)"
  then
    echo "Failed to get changed services"
    echo "${SERVICES}"
    exit 1

  elif [[ "${SERVICES}" == "" ]]
  then
    echo "None"

  else
    split_string_by_space "$SERVICES"
    echo "::set-output name=should_deploy::true"
    echo "SERVICES=${SERVICES}" >> $GITHUB_ENV
  fi
}
