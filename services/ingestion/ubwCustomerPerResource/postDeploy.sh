#!/bin/sh

PROD_STAGE="prod"
if [ "$SERVERLESS_STAGE" = $PROD_STAGE ]
then
  echo "Invoking ingest"
  sls invoke -f ingest $SERVERLESS_STAGE_FLAG $SERVERLESS_AWS_PROFILE_FLAG
else
  echo "Invoking mock-ingest"
  sls invoke -f mock $SERVERLESS_STAGE_FLAG $SERVERLESS_AWS_PROFILE_FLAG
fi
