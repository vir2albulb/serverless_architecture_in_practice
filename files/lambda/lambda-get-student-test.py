#!/usr/bin/python
# -*- coding: utf-8 -*-
"""lambda-get-student-test The lambda handles
fetching test to fill by student

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

def get_student_test(bucket, subjectName, testId, questionsKey):
    global sleepTime, s3delimiter
    response = ''
    questionsKeyPath = f'{subjectName}{s3delimiter}{testId}{s3delimiter}' \
                       f'{questionsKey}'
    # Counter helps to work with API RequestLimitExceed errors
    counter = 0
    while (counter < 5):
        s3Resource = boto3.resource('s3')
        try:
            response = jloads(s3Resource.Object(bucket,
                       questionsKeyPath).get()['Body'].read().decode('utf-8'))
            break
        except Exception as e:
            logger.warning(e)
            counter += 1
            logger.warning('API limit - waiting {}s...'.format(sleepTime))
            sleep(sleepTime)
        del s3Resource
    del questionsKeyPath, counter
    return response


def lambda_handler(event, context):

    global logger

    # environment variables
    questionsKey = env.get('questionsKeyPath', '')
    bucketName = env.get('targetBucketName', '')

    # event variables
    subjectName = event.get('subjectName', '')
    testId = event.get('testId', '')

    logger.info(f'Request to get questions - subject: {subjectName}, ' \
    f'testId: {testId}')

    lambdaResponse = get_student_test(bucket=bucketName, subjectName=subjectName,
                                testId=testId, questionsKey=questionsKey)
    errorCode = 400
    if lambdaResponse:
        logger.info('Questions successfully pulled')
        errorCode = 200
    else:
        lambdaResponse = 'Error while trying to pull questions. Please contact with '\
        'teacher!'
        logger.info(response)

    return {
        "body": lambdaResponse,
        "code": errorCode
    }
