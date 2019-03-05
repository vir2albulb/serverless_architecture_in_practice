#!/bin/bash
##==============================================================================
#title           :test-time.sh
#description     :This script is a simple client to work with student tests
#author          :jakub.marciniak@makemycloud.eu
#date            :02182019
#version         :0.1
#usage           :bash test-time.sh
#notes           :
##==============================================================================

echo '
 _______       _     _   _
|__   __|     | |   | | (_)
  | | ___  ___| |_  | |_ _ _ __ ___   ___
  | |/ _ \/ __| __| | __| | `_ ` _ \ / _ \
  | |  __/\__ \ |_  | |_| | | | | | |  __/
  |_|\___||___/\__|  \__|_|_| |_| |_|\___| v0.1

author: jakub.marciniak@makemycloud.eu
'

configDir="${HOME}/.trainings";
configFile="${configDir}/config";

if [ ! -f $configFile ]; then
  mkdir -p $configDir;
  while [ -z ${apiUrl} ]; do
    read -p 'Register API URL: ' apiUrl;
    echo;
  done
  while [ -z ${apiKey} ]; do
    read -s -p 'Register API key: ' apiKey;
    echo;
  done
  echo;
  while [ -z ${studentId} ]; do
     read -p 'Type your student ID: ' studentId;
     echo;
  done
  echo -e "apiUrl=${apiUrl}\napiKey=${apiKey}\nstudentId=${studentId}" > $configFile;
fi

source $configFile;
apiUrl="${apiUrl}/api/v1"

# Get list of tests
response=$(curl -s -XPOST -d '{"studentId": "'${studentId}'"}' \
              -H "x-api-key: ${apiKey}" ${apiUrl}/tests);

# Exit if student not exists
if (( $(echo ${response} | jq -r '.code') != 200 )); then
  echo ${response} | jq -r '.body' | tr -d '"' | xargs -ifoo echo -e "foo. Please verify config ${configFile}";
  exit 0;
fi

testsList=$(echo ${response} | jq -r '.body' | jq -r '.[]');

unset response

if [ -n "${testsList}" ]; then

  # List of available subjects
  subjects=$(echo ${testsList} | jq -r '.subject');
  userSubject=0;
  if (( $(echo ${subjects} | wc -l) > 1 )); then
    echo -e "There are available subjects:\n";
    index=0;
    for subject in $(echo $subjects); do
      (( index++ ));
      echo "[${index}]: ${subject}";
    done
    while [ -z ${userIndex} ] || (( ${userIndex} < 1 )) || (( ${userIndex} > ${index} )); do
      read -p "Please choose subject index (between 1 and ${index}): " userIndex;
      echo;
    done
    (( index-- ));
    userSubject=$index;
    unset index
  else
    :
  fi
  unset subjects;

  # List of available tests for specific subject
  subjectData=$(echo "[${testsList}]" | jq -r '.['${userSubject}']');
  subjectTestsList=$(echo ${subjectData} | jq -r '.testIds' | jq -r '.[]');

  userTest=0;
  if (( $(echo ${subjectTestsList} | wc -l) > 1 )); then
    echo -e "There are available tests:\n";
    index=0;
    for test in $(echo $subjectTestsList); do
      (( index++ ));
      echo "[${index}]: ${test}";
    done
    while [ -z ${userIndex} ] || (( ${userIndex} < 1 )) || (( ${userIndex} > ${index} )); do
      read -p "Please choose test index (between 1 and ${index}): " userIndex;
      echo;
    done
    (( index-- ));
    userTest=$index;
    unset index;
  else
    :
  fi
  unset subjectTestsList;

  # Variables required to fetch test
  subjectName=$(echo ${subjectData} | jq -r '.subject');
  userTestId=$(echo ${subjectData} | jq -r '.testIds' | jq -r '.['${userTest}']');

  # Get test to fill
  response=$(curl -s -H "x-api-key: ${apiKey}" \
             ${apiUrl}/test?subjectName=${subjectName}\&testId=${userTestId});

  echo "---------------------------- [TEST] ------------------------------------"
  echo "Subject: ${subjectName}"
  echo "Test ID: ${userTestId}"
  echo "---------------------------- [TEST] ------------------------------------"

  testQuestions=$(echo ${response} | jq -r '.body');
  numberOfQuestions=$(echo ${testQuestions} | jq -r '.[].questionId' | wc -l);
  (( numberOfQuestions-- ));
  userAnswers=()
  for questionIndex in $(seq 0 $numberOfQuestions); do
    questionData=$(echo ${testQuestions} | jq -r '.['$questionIndex']');
    questionId=$(echo ${questionData} | jq -r '.questionId');
    questionBody=$(echo ${questionData} | jq -r '.question');
    echo "[${questionId}] ${questionBody}"
    answers=$(echo ${questionData} | jq -r '.answers');
    numberOfAnswers=$(echo ${answers} | jq -r '.[].answerId' | wc -l);
    (( numberOfAnswers-- ));
    allowedAnswers=()
    for answerIndex in $(seq 0 $numberOfAnswers); do
      answerData=$(echo ${answers} | jq -r '.['$answerIndex']');
      answerId=$(echo ${answerData} | jq -r '.answerId');
      answerBody=$(echo ${answerData} | jq -r '.answerBody')
      echo "${answerId}: $answerBody"
      allowedAnswers+=($answerId)
    done
    userAnswer=''
    while [ -z ${userAnswer} ] || [[ ! "${allowedAnswers[@]}" =~ "${userAnswer}" ]]; do
      read -p "Your answer: " userAnswer;
      userAnswer=$(echo $userAnswer | tr '[:upper:]' '[:lower:]')
    done

    # Store user answer
    sep=','
    if (( $questionIndex == $numberOfQuestions )); then
      sep=''
    fi
    userAnswers+=('{"questionId":"'$questionId'","answer":"'$userAnswer'"}'$sep)

  done

  unset testQuestions
  unset numberOfQuestions

  userAnswers="[$(echo ${userAnswers[@]} | tr -d '\ ')]"

  # Upload student answers
  response=$(curl -s -XPOST \
            -d '{"subjectName":"'${subjectName}'","testId":"'${userTestId}'","studentId":"'${studentId}'","testResult":'${userAnswers}'}' \
            -H "x-api-key: ${apiKey}" ${apiUrl}/test);

  echo "-------------------- [TEST UPLOAD] ---------------------";
  if (( $(echo ${response} | jq -r '.code') == 200 )); then
    echo "Test ${userTestId} uploaded with success";
  else
    echo "Test ${userTestId} upload issue. Please contact with trainer";
  fi
  echo "-------------------- [TEST UPLOAD] ---------------------";

else
  echo "No missing tests found!";
fi
