#!/usr/bin/python
# -*- coding: utf-8 -*-
"""lambda-upload-student-test The lambda handles
upload of student test

Version: 0.1
Author: jakub.marciniak@makemycloud.eu

Usage:
    Script will be executed over API Gateway
"""

import boto3
import logging
from time import sleep, time
from json import dump as jdump, loads as jloads
from os import remove, environ as env

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


def create_tmp_file(data):
    tmpFile='/tmp/{epoch}.json'.format(epoch=time())
    with open(tmpFile, 'w') as outfile:
        jdump(data, outfile, indent=4)
    return tmpFile


def delete_tmp_file(file):
    remove(file)


def put_object(bucket, key, data):

    global sleepTime
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


def lambda_handler(event, context):

    global s3delimiter

    # environment variables
    bucketName = env.get('targetBucketName', '')
    studentAnswersKey = env.get('studentAnswersKeyPath', '')

    # event variables
    subjectName = event.get('subjectName', '')
    testId = event.get('testId', '')
    studentId = event.get('studentId', '')
    testResult = event.get('testResult', '')

    lambdaResponse = ''
    errorCode = 400

    if subjectName and testId and studentId and testResult:
        s3BucketKey = f'{subjectName}{s3delimiter}{testId}{s3delimiter}'\
                      f'{studentId}{s3delimiter}{studentAnswersKey}'
        logger.info(f'Registered request to upload test result: {s3BucketKey}')

        errorCode = 200 if put_object(bucket=bucketName, key=s3BucketKey, \
                            data=testResult) else 400
        lambdaResponse = 'Successfully uploaded test result' if errorCode == 200 \
        else 'Issue occoured while uploading file. Please contact with trainer'

    else:
        lambdaResponse = 'Missing one or more parameters - required '\
        'subject_name, test_id, student_id and test_result'

    return {
        "body": lambdaResponse,
        "code": errorCode
    }
