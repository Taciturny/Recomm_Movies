# // region
variable "region" {
  description = "AWS region to create resources in"
  type  = string
  default = "us-east-1"
}

variable training_instance_type {
  type = string
  description = "Instance type for training the ML model"
  default = "ml.c4.xlarge"
}

variable project_name {
  type = string
  description = "Name of the project"
  default = "movie-recomm"
}


variable endpoint_instance_type {
  type = string
  description = "The instance type used when deploying the model endpoint."
  default = "ml.c4.xlarge"
}


variable lambda_function_name {
  type = string
  description = "Name of the lambda function creating a unique ID"
  default     = "movie-recomm-function"
}


variable handler {
  type = string
  description = "Name of the lambda function handler"
  default = "lambda_function.lambda_handler"
}

variable "runtime" {
  type = string
  default = "python3.8"
}

variable "memory_size" {
  type = string
  description = "Memory Lambda in MB"
  default = "128"
}

variable "timeout" {
  type = string
  description = "Timeout Lambda in Seconds"
  default = "200"
}


variable lambda_zip_filename {
  type = string
  description = "The filename of the zip function from the lambda function"
  default     = "lambda_function.zip"
}
