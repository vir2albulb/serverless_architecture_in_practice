#!/bin/bash
##==============================================================================
#title           :update-subjects-or-students.sh
#description     :This script will execute Ansible playbook to create or update
#                 subjects, tests, questions, students list under S3 buceket
#author          :jakub.marciniak@makemycloud.eu
#date            :02172019
#version         :0.1
#usage           :bash create-subjects-or-update-students.sh
#notes           :Install Ansible v2.7 (at least) to use this script
##==============================================================================

#-------------------------------------------------------------------------------
# Main flow
#-------------------------------------------------------------------------------
echo "[INFO] ------------------------------------------------------------------"
echo "[INFO] Playbook to create/update list of subjects/students list started"
echo "[INFO] ------------------------------------------------------------------"

ansible-playbook ./base-playbook.yml --tags "update-subjects-or-students"

echo "[INFO] ------------------------------------------------------------------"
echo "[INFO] Playbook to create/update list of subjects/students list finished"
echo "[INFO] ------------------------------------------------------------------"
