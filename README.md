# Project Structure
```bash
Recomm_Movies/
│
├── data/
│   ├── ratings_small.csv        
│   
│  
│
├── terraform/
│   ├── modules/
│   │   ├── main.tf               # Terraform configuration for SageMaker, Lambda, Cloudwatch (Monitoring), Stepfunctions
│   │   └── variables.tf          # Variables for SageMaker, Lambda, Cloudwatch (Monitoring), Stepfunctions
│   ├── main.tf                   # Main Terraform configuration
│   ├── provider.tf               # Provider configuration
│   └── variables.tf   
│
├── src/
│   ├── deploy.sh                 # Script to deploy the terraform
│   ├── train.py                  # Training/Preprocessing script
│   └── evaluate.py               # Evaluating script
│
├── tests/
│   ├── infrastructure/
│   │   ├── test_integration.py     # Integration tests for Terraform configurations
│   └── Lambda /
│       ├── unit_test.py        # Unit tests for Lambda function
│
├── cicd/
│   ├── pipeline/
│   │   ├── pipeline.yaml         # AWS CodePipeline configuration
│   │   └── ...
│   └── scripts/
│       ├── build.sh              # Script for building CI/CD artifacts
│       └── deploy.sh             # Script for deploying CI/CD pipeline
│
├── docs/
│   ├── architecture_diagram.png  # Architecture diagram
│   └── ...
│
├── README.md                     # Project documentation
└── requirements.txt              # Python dependencies
```
