data "aws_s3_bucket" "ml_data_bucket" {
  bucket = "datarecomm1.0"
}


data "aws_iam_policy_document" "sf_assume_role" {
  version = "2012-10-17"

  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sf_exec_role" {
  name               = "${var.project_name}-sfn-exec"
  assume_role_policy = data.aws_iam_policy_document.sf_assume_role.json
}

// policy to invoke sagemaker training job, creating endpoints etc.
resource "aws_iam_policy" "sagemaker_policy" {
  name   = "${var.project_name}-sagemaker"
  policy = <<-EOF
      {
          "Version": "2012-10-17",
          "Statement": [
              {
                  "Effect": "Allow",
                  "Action": [
                      "sagemaker:CreateTrainingJob",
                      "sagemaker:DescribeTrainingJob",
                      "sagemaker:StopTrainingJob",
                      "sagemaker:createModel",
                      "sagemaker:createEndpointConfig",
                      "sagemaker:createEndpoint",
                      "sagemaker:addTags"
                  ],
                  "Resource": [
                   "*"
                  ]
              },
              {
                  "Effect": "Allow",
                  "Action": [
                      "sagemaker:ListTags"
                  ],
                  "Resource": [
                   "*"
                  ]
              },
              {
                  "Effect": "Allow",
                  "Action": [
                      "iam:PassRole"
                  ],
                  "Resource": [
                   "*"
                  ],
                  "Condition": {
                      "StringEquals": {
                          "iam:PassedToService": "sagemaker.amazonaws.com"
                      }
                  }
              },
              {
                  "Effect": "Allow",
                  "Action": [
                      "events:PutTargets",
                      "events:PutRule",
                      "events:DescribeRule"
                  ],
                  "Resource": [
                  "*"
                  ]
              }
          ]
      }
EOF
}

resource "aws_iam_role_policy_attachment" "sm_invoke" {
  role       = aws_iam_role.sf_exec_role.name
  policy_arn = aws_iam_policy.sagemaker_policy.arn
}

// IAM role for SageMaker training job //
data "aws_iam_policy_document" "sagemaker_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "cloud_watch_full_access" {
  role       = aws_iam_role.sf_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}


// Policies for sagemaker execution training job
resource "aws_iam_policy" "sagemaker_s3_policy" {
  name   = "${var.project_name}-sagemaker-s3-policy"
  policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:*"
        ],
        "Resource": [
          "${data.aws_s3_bucket.ml_data_bucket.arn}",
          "${data.aws_s3_bucket.ml_data_bucket.arn}/data/*",
          "${data.aws_s3_bucket.ml_data_bucket.arn}/model/*"
        ]
      }
    ]
  }
  EOF
}

resource "aws_iam_role" "sagemaker_exec_role" {
  name               = "${var.project_name}-sagemaker-exec"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
}

resource "aws_iam_role_policy_attachment" "s3_restricted_access" {
  role       = aws_iam_role.sagemaker_exec_role.name
  policy_arn = aws_iam_policy.sagemaker_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

// policy to invoke lambda
data "aws_iam_policy_document" "lambda_invoke" {
  statement {
    actions = [
      "lambda:InvokeFunction",
      "sagemaker:CreateTrainingJob", 
      "sagemaker:DescribeTrainingJob", 
      "sagemaker:StopTrainingJob", 
    ]
    resources = [
      aws_lambda_function.lambda_function.arn,
      "*"
    ]
  }
}

resource "aws_iam_policy" "lambda_invoke" {
  name   = "${var.project_name}-lambda-invoke"
  policy = data.aws_iam_policy_document.lambda_invoke.json
}

resource "aws_iam_role_policy_attachment" "lambda_invoke" {
  role       = aws_iam_role.sf_exec_role.name
  policy_arn = aws_iam_policy.lambda_invoke.arn
}

// Lambda //

resource "aws_iam_role" "lambda-role" {
  name        = "${var.lambda_function_name}-role"
  description = "${var.lambda_function_name}-permissions"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": ["lambda.amazonaws.com"]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

}

resource "aws_lambda_function" "lambda_function" {
  filename         = "${path.module}/../src/lambda_function.zip" 
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda-role.arn
  handler          = var.handler
  runtime          = var.runtime
  memory_size      = var.memory_size
  timeout          = var.timeout
  source_code_hash = filebase64sha256("${path.module}/../src/lambda_function.zip")
}


resource "aws_cloudwatch_event_rule" "sagemaker_model_created" {
  name        = "sagemaker-model-created"
  description = "Trigger Lambda function when a SageMaker model is created"

  event_pattern = <<EOF
{
  "source": ["aws.sagemaker"],
  "detail-type": ["SageMaker Model Created"]
}
EOF
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.sagemaker_model_created.name
  target_id = "RegisterModelLambda"
  arn       = "arn:aws:lambda:us-east-1:690744128016:function:${var.lambda_function_name}"
}


resource "aws_iam_role_policy_attachment" "lambda_invoke_target" {
  role       = aws_iam_role.lambda-role.name
  policy_arn = aws_iam_policy.lambda_invoke.arn
}


// CloudWatch Logs Group for Lambda function
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = 14  // Adjust retention as needed
}

// CloudWatch Log Stream for Lambda function
resource "aws_cloudwatch_log_stream" "lambda_log_stream" {
  name           = aws_lambda_function.lambda_function.function_name
  log_group_name = aws_cloudwatch_log_group.lambda_log_group.name
}

// CloudWatch Log Group for Step Function
resource "aws_cloudwatch_log_group" "sfn_log_group" {
  name              = "/aws/states/${var.project_name}-state-machine"
  retention_in_days = 14  // Adjust retention as needed
}

// CloudWatch Log Stream for Step Function
resource "aws_cloudwatch_log_stream" "sfn_log_stream" {
  name           = aws_sfn_state_machine.sfn_state_machine.name
  log_group_name = aws_cloudwatch_log_group.sfn_log_group.name
}

// CloudWatch Alarm for Lambda Errors
resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  alarm_name          = "LambdaFunctionErrors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alarm if Lambda function errors occur"
}

// CloudWatch Alarm for Step Function Execution Errors
resource "aws_cloudwatch_metric_alarm" "sfn_execution_error_alarm" {
  alarm_name          = "StepFunctionExecutionErrors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ExecutionFailed"
  namespace           = "AWS/States"
  period              = "60"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alarm if Step Function execution errors occur"
}


resource "aws_sfn_state_machine" "sfn_state_machine" {
  name     = "${var.project_name}-state-machine"
  role_arn = aws_iam_role.sf_exec_role.arn

  definition = <<-EOF
    {
      "Comment": "An AWS Step Function State Machine to train, build, and deploy an Amazon SageMaker model endpoint",
      "StartAt": "Configuration Lambda",
      "States": {
        "Configuration Lambda": {
          "Type": "Task",
          "Resource": "${aws_lambda_function.lambda_function.arn}",
          "Parameters": {
            "PrefixName": "${var.project_name}",
            "input_training_path": "$.input_training_path"
          },
          "Next": "Create Training Job",
          "ResultPath": "$.training_job_name"
        },
        "Create Training Job": {
          "Type": "Task",
          "Resource": "arn:aws:states:::sagemaker:createTrainingJob.sync",
          "Parameters": {
            "TrainingJobName.$": "$.training_job_name",
            "ResourceConfig": {
              "InstanceCount": 1,
              "InstanceType": "${var.training_instance_type}",
              "VolumeSizeInGB": 5
            },
            "HyperParameters": {
              "feature_dim": "9737",
              "num_factors": "25",
              "epochs": "5",
              "mini_batch_size": "1000",
              "predictor_type": "binary_classifier"
            },
            "AlgorithmSpecification": {
              "TrainingImage": "382416733822.dkr.ecr.us-east-1.amazonaws.com/factorization-machines:1",
              "TrainingInputMode": "File"
            },
            "OutputDataConfig": {
              "S3OutputPath": "s3://${data.aws_s3_bucket.ml_data_bucket.bucket}/model/"
            },
            "StoppingCondition": {
              "MaxRuntimeInSeconds": 3600
            },
            "RoleArn": "${aws_iam_role.sagemaker_exec_role.arn}",
            "InputDataConfig": [
              {
                "ChannelName": "train",
                "ContentType": "application/x-recordio-protobuf",
                "DataSource": {
                  "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": "s3://${data.aws_s3_bucket.ml_data_bucket.bucket}/data/train.protobuf",
                    "S3DataDistributionType": "FullyReplicated"
                  }
                }
              }
            ]
          },
          "Next": "Create Model"
        },
        "Create Model": {
          "Type": "Task",
          "Resource": "arn:aws:states:::sagemaker:createModel",
          "Parameters": {
            "PrimaryContainer": {
              "Image": "382416733822.dkr.ecr.us-east-1.amazonaws.com/factorization-machines:1",
              "Environment": {},
              "ModelDataUrl.$": "$.ModelArtifacts.S3ModelArtifacts"
            },
            "ExecutionRoleArn": "${aws_iam_role.sagemaker_exec_role.arn}",
            "ModelName.$": "$.TrainingJobName"
          },
          "ResultPath": "$.taskresult",
          "Next": "Create Endpoint Config"
        },
        "Create Endpoint Config": {
          "Type": "Task",
          "Resource": "arn:aws:states:::sagemaker:createEndpointConfig",
          "Parameters": {
            "EndpointConfigName.$": "$.TrainingJobName",
            "ProductionVariants": [
              {
                "InitialInstanceCount": 1,
                "ModelName.$": "$.TrainingJobName",
                "VariantName": "AllTraffic",
                "InstanceType": "${var.endpoint_instance_type}"
              }
            ]
          },
          "ResultPath": "$.taskresult",
          "Next": "Create Endpoint"
        },
        "Create Endpoint": {
          "Type": "Task",
          "Resource": "arn:aws:states:::sagemaker:createEndpoint",
          "Parameters": {
            "EndpointConfigName.$": "$.TrainingJobName",
            "EndpointName.$": "$.TrainingJobName"
          },
          "End": true
        }
      }
    }
  EOF
}
