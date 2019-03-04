#!/bin/bash
##==============================================================================
#title           :remove-api-gateway.sh
#description     :This script will execute Ansible playbook to remove API Gateway
#author          :jakub.marciniak@makemycloud.eu
#date            :02272019
#version         :0.1
#usage           :bash remove-api-gateway.sh
#notes           :Install Ansible v2.7 (at least) to use this script
##==============================================================================

#-------------------------------------------------------------------------------
# Main flow
#-------------------------------------------------------------------------------
echo "[INFO] ------------------------------------------------------------------"
echo "[INFO] Playbook to remove AWS API Gateway started"
echo "[INFO] ------------------------------------------------------------------"

ansible-playbook ./base-playbook.yml --tags "remove-api-gateway"

echo "[INFO] ------------------------------------------------------------------"
echo "[INFO] Playbook to remove AWS API Gateway finished"
echo "[INFO] ------------------------------------------------------------------"
