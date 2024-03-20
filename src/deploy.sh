#!/bin/bash

# Ensure Terraform is installed
terraform --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Terraform is not installed. Please install Terraform and try again."
  exit 1
fi

# Initialize Terraform
terraform init

# Validate Terraform configuration
terraform validate

# Plan Terraform changes
terraform plan -out=tfplan

# Apply Terraform changes
terraform apply tfplan

# Clean up temporary files
rm -f tfplan
