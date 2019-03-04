#!/usr/bin/python
# -*- coding: utf-8 -*-
"""lambda-generate-student-test-score The lambda handles
test results review, creating scores and students notification

Version: 0.1
Author: jakub.marciniak@makemycloud.eu

Usage:
    Script will be executed over CloudWatch Rule
"""

import boto3
import logging
from time import sleep, time
from json import dump as jdump, loads as jloads
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import remove, environ as env

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(process)s] [%(levelname)s] \
[%(funcName)s] %(message)s')

# STATIC VALUES
sleepTime = 30
maxScore = 5
s3delimiter = '/'

# Suppress boto3 INFO logging
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)


def get_mail_body(toStudent=False, score=None, list=[]):
    body = """\
<!DOCTYPE html>
<html>
<head>
<style>
body, table {
    font-family: Calibri, sans-serif;
    border-collapse: collapse;
    font-size: 14px;
}
table.footprint {
    font-family: Arial, sans-serif;
    font-size: 12px;
    border: 0px
}
table.footprint td, table.footprint tr {
    border: 0px
}
p {
    color: #686B73
}
table.footprint a {
    color: #13A3F7
}
td, th {
    border: 1px solid #dddddd;
    text-align: left;
    padding: 6px;
}
tr:nth-child(even) {
    background-color: #f5f5f5;
}
</style>
</head>
<body>
"""
    if toStudent:
        body += """\
Your score is: {score}
""".format(score)

    else:

        if [student for student in list if student['score']!='no' ]:
            body += """\
<table>
  <tr>
    <th colspan="4">Students with grades</th>
  </tr>
  <tr>
    <th>Subject name</th>
    <th>Test ID</th>
    <th>Student ID</th>
    <th>Score</th>
  </tr>
"""
            for student in list:
                if student['score'] != 'no':
                    body += """\
<tr>
<td>{subjectName}</td>
<td>{testId}</td>
<td>{studentId}</td>
<td>{score}</td>
</tr>
""".format(subjectName=student['subjectName'], testId=student['testId'], \
           studentId=student['studentId'], score=student['score'])

            body += """\
</table>
<br>
"""

        if [student for student in list if student['score']=='no' ]:
            body += """\
<table>
  <tr>
    <th colspan="3">Missing tests</th>
  </tr>
  <tr>
    <th>Subject name</th>
    <th>Test ID</th>
    <th>Student ID</th>
  </tr>
"""
            for student in list:
                if student['score'] != 'no':
                    body += """\
<tr>
<td>{subjectName}</td>
<td>{testId}</td>
<td>{studentId}</td>
</tr>
""".format(subjectName=student['subjectName'], testId=student['testId'], \
           studentId=student['studentId'])

            body + """\
</table>
"""

    body += """\

<br><br>
<table class='footprint'>
<tr>
<td>Student Trainingss - Cloud Notification System</td>
</tr>
</table>
<br>
"""

    return body


def mime_email(subject, fromAddress, toAddress, htmlMessage):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = fromAddress
    msg['To'] = toAddress
    msg.attach(MIMEText(htmlMessage, 'html'))
    return msg.as_string()


def send_mail(region, fromAddress, toAddress, message):
    global logger
    counter = 0
    logger.info(f'Sending report to: {toAddress}')
    # Counter helps to work with API RequestLimitExceed errors
    while (counter < 5):
        sesClient = boto3.client('ses', region_name=region)
        try:
            response = sesClient.send_raw_email(
                Source=fromAddress,
                Destinations=toAddress,
                RawMessage={
                    'Data': message
                }
            )
            if response:
                logger.info('Report has been sent')
            del response
            counter = 5
        except Exception as e:
            logger.error(f'{e}')
            counter += 1
            logger.error(f'Get API limit - waiting {sleepTime}s...')
            sleep(sleepTime)
        del sesClient
    del counter


def create_tmp_file(data):
    tmpFile='/tmp/{epoch}.json'.format(epoch=time())
    with open(tmpFile, 'w') as outfile:
        jdump(data, outfile, indent=4)
    return tmpFile


def delete_tmp_file(file):
    remove(file)


def put_object(bucket, key, data):
    global sleepTime, logger
    # Counter helps to work with API RequestLimitExceed errors
    counter = 0
    response = False
    file = create_tmp_file(data=data)
    while (counter < 5):
        s3Resource = boto3.resource('s3')
        try:
            s3Resource.Bucket(bucket).upload_file(Filename=file, Key=key)
            response = True
            break
        except Exception as e:
            logger.warning(e)
            counter += 1
            logger.warning('API limit - waiting {}s...'.format(sleepTime))
            sleep(sleepTime)
        del s3Resource
    delete_tmp_file(file)
    del counter
    return response


def get_object_content(bucket, objectKey):
    global sleepTime, logger
    objectBody = ''
    # Counter helps to work with API RequestLimitExceed errors
    counter = 0
    while (counter < 5):
        s3Resource = boto3.resource('s3')
        try:
            objectBody = jloads(s3Resource.Object(bucket,
                           objectKey).get()['Body'].read().decode('utf-8'))
            break
        except Exception as e:
            logger.warning(e)
            counter += 1
            logger.warning('API limit - waiting {}s...'.format(sleepTime))
            sleep(sleepTime)
        del s3Resource
    del counter
    return objectBody


def check_if_key_exists(bucket, key):
    global sleepTime, s3delimiter
    keyExists = False
    logger.info(f'Checking if key {key} exists...')
    # Counter helps to work with API RequestLimitExceed errors
    counter = 0
    while (counter < 5):
        s3Resource = boto3.resource('s3')
        try:
            # List all directories available under S3 bucket
            response = s3Resource.meta.client.list_objects(Bucket=bucket,
            Delimiter=s3delimiter, Prefix=key)
            if response.get('Contents', []):
                keyExists = True
            break
            del response
        except Exception as e:
            logger.warning(e)
            counter += 1
            logger.warning('API limit - waiting {}s...'.format(sleepTime))
            sleep(sleepTime)
        del s3Resource
    del counter
    return keyExists


def get_list_of_tests(bucket, questionsKey):
    global sleepTime, s3delimiter
    subjectsList = []
    allTests = []
    testList = []
    logger.info('Looking for student list of subjects...')
    # Counter helps to work with API RequestLimitExceed errors
    counter = 0
    while (counter < 5):
        s3Resource = boto3.resource('s3')
        try:
            # List all directories available under S3 bucket
            response = s3Resource.meta.client.list_objects(Bucket=bucket,
            Delimiter=s3delimiter, Prefix=questionsKey)
            if subjectsList == []:
                response = s3Resource.meta.client.list_objects(Bucket=bucket,
                Delimiter=s3delimiter)
                subjectsList = [prefix['Prefix'] \
                                for prefix in response.get('CommonPrefixes', [])]
                logger.info('subjectsList {list}'.format(list=subjectsList))
                counter = 0
            elif allTests == []:
                for subject in subjectsList:
                    response = s3Resource.meta.client.list_objects(
                    Bucket=bucket, Delimiter=s3delimiter, Prefix=subject)
                    allTests += [prefix['Prefix'] \
                                for prefix in response.get('CommonPrefixes', [])]
                logger.info('allTests {list}'.format(list=allTests))
                if allTests == []:
                    break
                else:
                    counter = 0
            else:
                for test in allTests:
                    response = s3Resource.meta.client.list_objects(
                    Bucket=bucket, Delimiter=s3delimiter, Prefix=test)
                    if f'{test}{questionsKey}' in [content['Key'] \
                        for content in response.get('Contents', [])]:
                        testList.append(test)
                break
            del response
        except Exception as e:
            logger.warning(e)
            counter += 1
            logger.warning('API limit - waiting {}s...'.format(sleepTime))
            sleep(sleepTime)
        del s3Resource
    del counter

    return testList


def calculate_score(answerKey, studentTestResult):
    global sleepTime, s3delimiter, maxScore

    numberOfQuestions = len(answerKey)
    correctAnswers = 0.0
    for key in answerKey:
        if key['answer'] == [question['answer'] for question in studentTestResult \
                            if question['questionId']==key['questionId']][0]:
            correctAnswers += 1

    return int(round(correctAnswers / numberOfQuestions * maxScore))



def generate_scores(bucket, testsList, questionsKey, studentsList, studentAnswersKey, scoreKey):
    global sleepTime, s3delimiter
    trainerListToSend = []
    studentsListToSend = []
    logger.info('Calculating scores...')

    for test in testsList:
        answerKey = get_object_content(bucket=bucket, objectKey=f'{test}{questionsKey}')
        subjectName = test.split(f'{s3delimiter}')[0]
        testId = test.split(f'{s3delimiter}')[1]
        for student in studentsList:

            score = "no"
            studentId = student['student_id']
            studentEmail = student['email']
            studentResultExists = check_if_key_exists(bucket=bucket, \
            key=f'{test}{studentId}{s3delimiter}{studentAnswersKey}')

            if studentResultExists:
                scoreExists = check_if_key_exists(bucket=bucket, \
                key=f'{test}{studentId}{s3delimiter}{scoreKey}')

                if not scoreExists:
                    studentTestResult = get_object_content(bucket=bucket, \
                    objectKey=f'{test}{studentId}{s3delimiter}{studentAnswersKey}')
                    score = calculate_score(answerKey, studentTestResult)
                    studentsListToSend.append({"studentEmail": studentEmail, \
                    "subjectName": subjectName, "testId": testId, "score": score})
                    if put_object(bucket=bucket, \
                                key=f'{test}{studentId}{s3delimiter}{scoreKey}', \
                                data={"score": score}):
                        logger.info(f'Subject: {subjectName}, test: {testId}, '\
                                    f'student: {studentId} - score saved')
            else:
                None
            trainerListToSend.append({"studentId": studentId, \
            "subjectName": subjectName, "testId": testId, "score": score})

    return trainerListToSend, studentsListToSend


def lambda_handler(event, context):
    global logger

    logger.info('====== lambda-generate-student-test-score is running ======')

    bucketName = env.get('targetBucketName', '')
    sesRegion = env.get('sesRegion', '')
    senderEmail = env.get('emailSender', '')
    trainerEmail = env.get('trainerEmail', '')
    mainSubject = 'Test score'
    studentsListKey = env.get('studentsListKeyPath', '')
    questionsKey = env.get('questionsKeyPath', '')
    studentAnswersKey = env.get('testResult', '')
    scoreKey = env.get('scoreKey', '')

    if (bucketName != '' and sesRegion != '' and senderEmail != ''):
        # Get list of students
        studentsList = get_object_content(bucket=bucketName, \
                                            objectKey=studentsListKey)
        testsList = get_list_of_tests(bucket=bucketName, \
                                      questionsKey=questionsKey)
        if testsList:
            trainerEmail, studentsNotification = generate_scores(\
            bucket=bucketName, testsList=testsList, \
            questionsKey=questionsKey, studentsList=studentsList, \
            studentAnswersKey=studentAnswersKey, scoreKey=scoreKey)

            for student in studentsNotification:
                mailBody = get_mail_body(toStudent=True, score=student['score'])
                subject = '[{subjectName}] [{testId}] {main}'.format(\
                subjectName=student['subjectName'], testId=student['testId'], \
                main=mainSubject)
                message = mime_email(subject=subject, fromAddress=senderEmail, \
                toAddress=student['studentEmail'], htmlMessage=mailBody)
                send_mail(region=sesRegion, fromAddress=senderEmail, \
                toAddress=student['studentEmail'], message=message)
                del mailBody, subject, message

            # Mail to trainer
            mailBody = get_mail_body(list=trainerEmail)
            subject = f'[bucketName] {mainSubject}'
            message = mime_email(subject=subject, fromAddress=senderEmail, \
                toAddress=trainerEmail, htmlMessage=mailBody)
            send_mail(region=sesRegion, fromAddress=senderEmail, \
                toAddress=trainerEmail, message=message)
            del mailBody, subject, message
        else:
            logger.info('Test lists if empty')    
    else:
        logger.info('Please provide environment variables for bucket name, ' \
                    'SES region and email sender')
    del report, bucketName, sesRegion, senderEmail, trainerEmail, mainSubject

    logger.info('====== lambda-generate-student-test-score completed ======')
