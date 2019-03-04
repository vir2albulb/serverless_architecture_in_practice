#!/usr/bin/python
# -*- coding: utf-8 -*-
"""lambda-get-student-tests The lambda handles
fetching list of tests to fill by student

Version: 0.1
Author: jakub.marciniak@makemycloud.eu

Usage:
    Script will be executed over API Gateway
"""

import boto3
import logging
from time import sleep
from json import loads as jloads
from os import environ as env

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(process)s] [%(levelname)s] \
[%(funcName)s] %(message)s')

# GLOBAL VALUES
sleepTime = 30
s3delimiter = '/'

# Suppress boto3 INFO logging
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)


def check_if_student_is_valid(bucket, studentId, studentsListKey):
    global sleepTime
    studentsList = ''
    # Counter helps to work with API RequestLimitExceed errors
    counter = 0
    while (counter < 5):
        s3Resource = boto3.resource('s3')
        try:
            studentsList = jloads(s3Resource.Object(bucket,
                           studentsListKey).get()['Body'].read().decode('utf-8'))
            break
        except Exception as e:
            logger.warning(e)
            counter += 1
            logger.warning('API limit - waiting {}s...'.format(sleepTime))
            sleep(sleepTime)
        del s3Resource
    del counter
    return [student for student in studentsList
            if student['student_id']==studentId]


def get_student_tests(bucket, studentId):
    global sleepTime, s3delimiter
    subjectsList = []
    allTests = []
    studentTests = []
    logger.info('Looking for student list of subjects...')
    # Counter helps to work with API RequestLimitExceed errors
    counter = 0
    while (counter < 5):
        s3Resource = boto3.resource('s3')
        try:
            # List all directories available under S3 bucket
            response = ''
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
                    if '{}{}{}'.format(test, studentId, s3delimiter) not in \
                                            [prefix['Prefix'] for prefix in \
                                            response.get('CommonPrefixes', [])]:
                        studentTests.append(test)
                logger.info('studentTests {list}'.format(list=studentTests))
                break
            del response
        except Exception as e:
            logger.warning(e)
            counter += 1
            logger.warning('API limit - waiting {}s...'.format(sleepTime))
            sleep(sleepTime)
        del s3Resource
    del counter

    return studentTests


def lambda_handler(event, context):

    global logger, s3delimiter

    # environment variables
    studentsListKey = env.get('studentsListKeyPath', '')
    bucketName = env.get('targetBucketName', '')

    # event variables
    studentId = event.get('studentId', '')
    testId = event.get('testId', '')

    logger.info('Checking if student exists in list of students: '\
    '{id}'.format(id=studentId))

    errorCode = 400

    studentData = check_if_student_is_valid(bucket=bucketName,
                                            studentId=studentId,
                                            studentsListKey=studentsListKey)

    if studentData == []:
        lambdaResponse = 'Requested student does not exists'
        logger.info(lambdaResponse)
        return {
            "body": lambdaResponse,
            "code": errorCode
        }
    del studentData

    logger.info('Getting student tests - student ID: {id}'.format(id=studentId))
    get_student_tests(bucket=bucketName, studentId=studentId)

    tmpListAll = []
    tmpListSubjects = []
    for test in sorted(get_student_tests(bucket=bucketName, studentId=studentId)):
        testDetails = test.split(s3delimiter)
        tmpListSubjects.append(testDetails[0])
        tmpListAll.append({'subject': testDetails[0], 'testId': testDetails[1]})
        del testDetails

    lambdaResponse = []
    for subject in tmpListSubjects:
        lambdaResponse.append({'subject': subject,
                        'testIds': [test['testId'] for test in tmpListAll
                                    if test['subject']==subject]})
    del tmpListAll, tmpListSubjects

    errorCode = 200

    return {
        "body": lambdaResponse,
        "code": errorCode
    }
