#!/bin/bash
##==============================================================================
#title           :deploy-api-gateway.sh
#description     :This script will execute Ansible playbook to deploy API Gateway
#author          :jakub.marciniak@makemycloud.eu
#date            :02172019
#version         :0.1
#usage           :bash deploy-api-gateway.sh
#notes           :Install Ansible v2.7 (at least) to use this script
##==============================================================================

#-------------------------------------------------------------------------------
# Main flow
#-------------------------------------------------------------------------------
echo "[INFO] ------------------------------------------------------------------"
echo "[INFO] Playbook to deploy AWS API Gateway started"
echo "[INFO] ------------------------------------------------------------------"

ansible-playbook ./base-playbook.yml --tags "deploy-api-gateway"

echo "[INFO] ------------------------------------------------------------------"
echo "[INFO] Playbook to deploy AWS API Gateway finished"
echo "[INFO] ------------------------------------------------------------------"
