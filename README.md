# Serverless architecture with Ansible and AWS

Repository contains Ansible playbook to deploy real example of AWS API Gateway
and AWS Lambda. Playbook deploys application to manage students subjects
and tests. After each session trainer creates test questions. Next each student should fill test before next lesson. Playbook deploys
AWS Lambda triggered by CloudWatch rule to generate score for each student upload. Notification about scores and missing uploads are send to students and
to trainer (both grades and missing tests per student).

## Prerequisites:

Install all below tools/packages to work with playbook.

* AWS CLI v1.16.60
* AWS access key pair configured with AWS CLI
* boto v2.49.0
* Ansible v2.7.1

## Environment variables

Playbook requires to initialize tools or environment variables to work with:

* AWS credentials - admin access manadatory (or admin access to AWS IAM, CloudWatch,
  API Gateway, Lambda, Simple Email Service)

```bash
# Run awscli to setup default AWS credentials
$ aws configure
```

## Plabyook variables

Playbook uses a set of predefined variables to deploy AWS serverless app:

* [all.yml](group_vars/all.yml) - properties used by plabyook to deploy API
Gateway and AWS Lambda functions, some properties are used as environment variables in AWS Lambda setup.

## Usage

Once all variables have been verified playbook can be executed.

```bash
# Run deploy-api-gateway.sh script to deploy Serverless app
$ ./deploy-api-gateway.sh
```

To deploy/update list of students and or subjects with questions execute below
command.

```bash
# Run update-subjects-or-students.sh script to deploy/update subjects/questions/studentsList
$ ./update-subjects-or-students.sh
```

To remove stacks and AWS S3 buckets use below command.

```bash
# Run remove-api-gateway.sh script to remove deployment
$ ./remove-api-gateway.sh
```

## Simple Bash clients

Once you will setup Serverless app you can pull config for AWS API Gateway.

```bash
# Run pull-api-config.sh to pull AWS API Gateway endpoint URL and API key
$ ./bin/pull-api-config.sh
```

Use above output to setup trainings client (client config stored under ~/.trainings/config)
and work with Serverless app.

```bash
# Run test-time.sh to work with Serverless app
$ ./bin/test-time.sh
```
