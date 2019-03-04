#!/bin/bash
##==============================================================================
#title           :pull-config.sh
#description     :This script pulls API Gateway deployment URL and API key
#author          :jakub.marciniak@makemycloud.eu
#date            :02232019
#version         :0.1
#usage           :bash pull-config.sh
#notes           :
##==============================================================================

echo '
 _____       _ _            _____ _____                    __ _
|  __ \     | | |     /\   |  __ \_   _|                  / _(_)
| |__) |   _| | |    /  \  | |__) || |     ___ ___  _ __ | |_ _  __ _
|  ___/ | | | | |   / /\ \ |  ___/ | |    / __/ _ \|  _ \|  _| |/ _` |
| |   | |_| | | |  / ____ \| |    _| |_  | (_| (_) | | | | | | | (_| |
|_|    \__,_|_|_| /_/    \_\_|   |_____|  \___\___/|_| |_|_| |_|\__, |
                                                                __/ |
                                                               |___/ v0.1

author: jakub.marciniak@makemycloud.eu
'

# Script uses default AWS CLI region
awsRegion=$(aws configure get region);

apiId=$(aws apigateway get-rest-apis \
        --query 'items[?name==`Upload student test API`]' | jq -r '.[].id');

apiKeyValue=$(aws apigateway get-api-keys --name-query manage-student-test-01 \
              --include-values | jq -r '.items' | jq -r '.[].value');


echo "API Endpoint URL: https://${apiId}.execute-api.${awsRegion}.amazonaws.com";
echo "API Key: ${apiKeyValue}";

unset apiId;
unset apiKeyValue;
