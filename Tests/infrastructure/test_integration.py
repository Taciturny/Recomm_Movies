# pylint: disable=line-too-long

"""Integration tests for Terraform configuration."""

import unittest
import boto3

class TestIntegration(unittest.TestCase):
    """
    Integration tests for Terraform configuration.

    This module contains integration tests for validating the Terraform configuration deployed in AWS.

    Classes:
        TestIAMAndS3Integration: A TestCase class for IAM and S3 integration tests.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up AWS clients and variables for testing.
        """
        cls.iam_client = boto3.client('iam')
        cls.s3_client = boto3.client('s3')
        cls.cloudwatch_client = boto3.client('cloudwatch')
        cls.logs_client = boto3.client('logs')
        cls.lambda_client = boto3.client('lambda')
        cls.sfn_client = boto3.client('stepfunctions')
        cls.role_name_stf  = "movie-recomm-sfn-exec"
        cls.role_name_sagemaker  = "movie-recomm-sagemaker-exec"
        cls.bucket_name = "datarecomm1.0"
        cls.project_name = "movie-recomm"
        cls.policy_name = "movie-recomm-sagemaker-s3-policy"
        cls.lambda_function_name = "movie-recomm-function"
        cls.lambda_log_group_name = f"/aws/lambda/{cls.lambda_function_name}"
        cls.sfn_log_group_name = "/aws/states/movie-recomm-state-machine"
        cls.training_job_name = "movie-recomm-20240320143637"
        cls.lambda_role_name = "movie-recomm-function-role"
        cls.lambda_policy_arn ="arn:aws:iam::690744128016:policy/movie-recomm-lambda-invoke"
        cls.sfn_state_machine_arn = "arn:aws:states:us-east-1:690744128016:stateMachine:movie-recomm-state-machine"
        cls.ml_data_bucket_name = "datarecomm1.0"

    def test_iam_role_exists(self):
        """
        Test whether IAM role exists.
        """
        response = self.iam_client.get_role(RoleName=self.role_name_stf)
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

    def test_iam_role_policy_attachment_exists(self):
        """
        Tests if the specified IAM role has the required policy attached.
        """
        response = self.iam_client.list_attached_role_policies(RoleName=self.role_name_stf)
        policies = [p['PolicyArn'] for p in response['AttachedPolicies']]
        # Check if CloudWatchFullAccess policy is attached to the state machine role
        self.assertIn("arn:aws:iam::aws:policy/CloudWatchFullAccess", policies)

    def test_s3_bucket_exists(self):
        """
        Tests if the specified S3 bucket exists.
        """
        response = self.s3_client.head_bucket(Bucket=self.bucket_name)
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

    def test_sagemaker_training_job_policy_exists(self):
        response = self.iam_client.list_attached_role_policies(RoleName=self.role_name_sagemaker)
        policies = [p['PolicyArn'] for p in response['AttachedPolicies']]
        self.assertIn("arn:aws:iam::690744128016:policy/movie-recomm-sagemaker-s3-policy", policies)


    def test_lambda_role_exists(self):
        """
        Tests if the specified Lambda function role exists.
        """
        response = self.iam_client.get_role(RoleName=self.lambda_role_name)
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

    def test_lambda_function_exists(self):
        """
        Tests if the specified Lambda function exists.
        """
        response = self.lambda_client.get_function(FunctionName=self.lambda_function_name)
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

    def test_lambda_function_permissions(self):
        """
        Tests if the specified Lambda function has the required permissions.
        """
        # Validate Lambda function permissions
        function_policy = self.iam_client.get_policy(PolicyArn=self.lambda_policy_arn)
        policy_version = self.iam_client.get_policy_version(PolicyArn=function_policy['Policy']['Arn'], VersionId=function_policy['Policy']['DefaultVersionId'])
        policy_document = policy_version['PolicyVersion']['Document']
        self.assertIn("lambda:InvokeFunction", policy_document['Statement'][0]['Action'])

    def test_lambda_log_group_exists(self):
        """
        Tests if the specified CloudWatch log group for Lambda exists.
        """
        response = self.logs_client.describe_log_groups(logGroupNamePrefix=self.lambda_log_group_name)
        self.assertTrue(len(response['logGroups']) > 0)

    def test_sfn_log_group_exists(self):
        """
        Tests if the specified CloudWatch log group for Step Function exists.
        """
        response = self.logs_client.describe_log_groups(logGroupNamePrefix=self.sfn_log_group_name)
        self.assertTrue('logGroups' in response and len(response['logGroups']) > 0)

    def test_lambda_log_stream_exists(self):
        """
        Tests if the specified CloudWatch log stream for Lambda exists.
        """
        response = self.logs_client.describe_log_streams(logGroupName=self.lambda_log_group_name, logStreamNamePrefix=self.lambda_function_name)
        self.assertTrue(len(response['logStreams']) > 0)

    def test_sfn_log_stream_exists(self):
        """
        Tests if the specified CloudWatch log stream for Step Function exists.
        """
        response = self.logs_client.describe_log_streams(logGroupName=self.sfn_log_group_name)
        self.assertTrue('logStreams' in response and len(response['logStreams']) > 0)

    def test_lambda_error_alarm_exists(self):
        """
        Tests if the specified CloudWatch alarm for Lambda errors exists.
        """
        alarm_name = "LambdaFunctionErrors"
        response = self.cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
        self.assertTrue(len(response['MetricAlarms']) > 0)

    def test_sfn_execution_error_alarm_exists(self):
        """
        Tests if the specified CloudWatch alarm for Step Function execution errors exists.
        """
        alarm_name = "StepFunctionExecutionErrors"
        response = self.cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
        self.assertTrue(len(response['MetricAlarms']) > 0)

    def test_state_machine_exists(self):
        """
        Tests if the specified Step Function state machine exists.
        """
        response = self.sfn_client.describe_state_machine(stateMachineArn=self.sfn_state_machine_arn)
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

if __name__ == '__main__':
    unittest.main()


# The tests primarily focus on verifying the existence of IAM roles, S3 buckets, Lambda functions, CloudWatch log groups and streams, CloudWatch alarms, and AWS Step Functions state machine. They also include a test for executing the state machine.
