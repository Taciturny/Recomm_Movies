data "aws_caller_identity" "current_identity" {}

module "ml-pipeline" {
  source = "./modules"
  project_name = var.project_name
  training_instance_type = var.training_instance_type
  endpoint_instance_type = var.endpoint_instance_type
  lambda_function_name = var.lambda_function_name
  handler = var.handler
}



