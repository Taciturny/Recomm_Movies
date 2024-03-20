terraform {
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.region
}
