#!/bin/sh

PROD_STAGE="prod"
if [ "$SERVERLESS_STAGE" = $PROD_STAGE ]
then
  echo "Invoking ingest"
  sls invoke -f ingest --stage prod "$SERVERLESS_AWS_PROFILE_FLAG"
else
  echo "Invoking mock-ingest"
  sls invoke -f mock --stage dev "$SERVERLESS_AWS_PROFILE_FLAG"
fi
