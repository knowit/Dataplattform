#!/bin/bash

echo "Prepare services for deploy"
for full_path in $(find ./services/ingestion -name "serverless.yml")
do
    echo "Get serverless plugins $(dirname $full_path)"
    (cd $(dirname $full_path) && npm install)
    
    if [ $1 ] && [ $1 = "clean" ]
    then
        echo "Clean $(dirname $full_path)"
        (cd $(dirname $full_path) && sls requirements clean)
        (cd $(dirname $full_path) && sls requirements cleanCache)
    fi  
done

echo "Deploy all services"
for full_path in $(find ./services/ingestion -name "serverless.yml")
do
    echo "Begin deploy of $(dirname $full_path)"
    (cd $(dirname $full_path) && sls deploy &)    
done

wait
echo "Deploy done"
