"""Unit tests for Lambda configuration."""

import os
import sys
import datetime
import unittest


# Add the parent directory of the terraform module to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Correct the import statement to match the actual structure
from terraform.src.lambda_function import lambda_handler


class TestLambdaHandler(unittest.TestCase):
    """
    A unittest class to test the Lambda handler function.

    This class contains a single test method to ensure that the Lambda handler
    generates the expected training job name based on the event data provided.
    """
    def test_lambda_handler(self):
        """
        Tests the Lambda handler function.

        Verifies that the Lambda handler generates the expected training job name
        based on the event data provided.
        """
        event = {'PrefixName': 'prefix'}
        expected_training_job_name = 'prefix-' + datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')

        result = lambda_handler(event, None)

        self.assertEqual(result, expected_training_job_name)

if __name__ == '__main__':
    unittest.main()
