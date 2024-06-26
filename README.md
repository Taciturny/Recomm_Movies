# Movie Recommendation System

## Overview
The Movie Recommendation System project aims to develop a robust recommendation system to suggest movies to users based on their preferences. By analyzing user ratings and movie metadata, the system generates personalized recommendations, enhancing the user experience on movie streaming platforms.

### Dataset
The dataset used for this project contains user ratings for various movies. Each record includes information such as userId, movieId, rating, and timestamp. The dataset is sourced from Kaggle, and you can find it [here](https://www.kaggle.com/code/rounakbanik/movie-recommender-systems/data).

## Methodology
#### Data Preparation
The data is preprocessed to create the target variable 'liked', indicating whether the user liked a movie (rating >= 4). Categorical variables like userId and movieId are one-hot encoded using sklearn's OneHotEncoder.

## Model Building
The recommendation system utilizes machine learning algorithms to predict user preferences. Techniques such as collaborative filtering, content-based  filtering and matrix factorization are employed to generate accurate recommendations.

## Objective
The primary objective of this project is to develop an efficient and accurate movie recommendation system that enhances user satisfaction and engagement on movie platforms.

## Key Outcomes
- Development of a user-friendly recommendation system.
- Improved user experience and engagement on movie streaming platforms.
- Promotion of content discovery and increased user retention.

## Beneficiaries
The project benefits movie enthusiasts, streaming platforms, and content creators by providing personalized movie recommendations tailored to individual preferences.

## Installation
```bash
# Clone the repository
git clone https://github.com/Taciturny/Recomm_Movies.git

# Change to the project directory
cd Recomm_Movies
```
![Prefect Architecture](docs/project_arch.png)

# Project Structure
```bash
Recomm_Movies/
│
├── data/
│   └── ratings_small.csv            # Sample movie ratings data
│    
├── terraform/
│   ├── modules/
│   │   ├── main.tf                   # Terraform configuration for SageMaker, Lambda, Cloudwatch (Monitoring), Stepfunctions
│   │   └── variables.tf              # Variables for SageMaker, Lambda, Cloudwatch (Monitoring), Stepfunctions
│   ├── main.tf                       # Main Terraform configuration
│   ├── provider.tf                   # Provider configuration
│   └── variables.tf                  # Terraform variables
│
├── src/
│   ├── deploy.sh                    # Script to deploy the terraform
│   ├── train.py                     # Script for training models and preprocessing data
│   ├── evaluate.py                  # Script for evaluating models
│   ├── __init__.py                  # Initialization file for the src package
│   ├── cb.py                        # Content-Based recommendation script
│   ├── preprocess.py                # Script for data preprocessing for Content-Based recommendation
│   ├── config/                      # Configuration files
│   │   └── cf_config.py             # Configuration file for Collaborative Filtering
│   └── cf.py                        # Collaborative Filtering recommendation script
│
├── tests/
│   ├── infrastructure/
│   │   └── test_integration.py      # Integration tests for Terraform configurations
│   └── Lambda/
│       └── unit_test.py             # Unit tests for Lambda function
│
├── cicd/
│   └── .github/
│       └── workflows/
│           └── ci.yml               # GitHub Actions configuration
│
├── docs/
│   └── architecture_diagram.png     # Architecture diagram
│
├── README.md                        # Project documentation
└── requirements.txt                 # Python dependencies
```

## Reproducibility Steps

### Step 0: Set Up Python Environment

1. **Create Virtual Environment** (Optional but Recommended):
   - It's recommended to work within a virtual environment to isolate your project's dependencies. If you're using `venv`, run the following command:
     ```bash
     python -m venv myenv --python=3.8
     ```
   - If you're using `conda`, create a new environment:
     ```bash
     conda create --name myenv python=3.8
     ```

2. **Activate the Environment**:
   - For `venv`:
     ```bash
     source myenv/bin/activate
     ```
   - For `conda`:
     ```bash
     conda activate myenv
     ```

### Step 1: Install Dependencies

1. **Install pip (if not already installed)**:
   - If you haven't installed `pip` yet, you can do so by following [these instructions](https://pip.pypa.io/en/stable/installation/).

2. **Install Requirements**:
   - Navigate to the root directory of your project where `requirements.txt` is located.
   - Run the following command to install the required packages:
     ```bash
     pip install -r requirements.txt
     ```

### Step 2: Configure AWS Environment

1. **Create AWS Account and IAM User**:
   - After installing AWS CLI, create an account in AWS and navigate to the [IAM service](https://console.aws.amazon.com/iam/) under Roles. Create a user and access keys.

2. **Assign AdministratorFullAccess Permission**:
   - Assign the `AdministratorFullAccess` permission to the IAM user for this project. Note: This permission is typically not advisable but is used for this project.

3. **Download and Install AWS CLI**:
   - Download AWS CLI locally by following the [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

4. **Configure AWS CLI**:
   - Configure AWS CLI and provide the access keys obtained in step 2.

5. **Create S3 Bucket**:
   - Create an S3 bucket for Terraform and save the data for model training:
     ```bash
     aws s3 mb s3://[bucket_name]
     ```

### Step 3: Run Train Script

1. **Navigate to `src` folder**:
   - Before running the `train.py` script, users can customize the following inputs:

2. **S3 Bucket Name and Key**:
   - Users can specify the name of the S3 bucket where the dataset is stored (`s3_bucket`) and the key (path) to the CSV file (`s3_key`) to save the protobuf data suitable for matrix factorization modeling.

3. **Hyperparameters**:
   - `num_factors`: Number of factors to use in the factorization model.
   - `epochs`: Number of training epochs.
   - `mini_batch_size`: Mini batch size for training.

4. **SageMaker Instance Type (Optional)**:
   - Users can optionally specify the SageMaker instance type (`instance_type`) for training the model. Default value is `ml.c4.xlarge`.

5. **Factorization-Machine Image**:
   - Users should print the image URI which will be used in the step function in step 3.

6. **Run the Command**:
    ```bash
    python train.py
    ```


### Step 4: Configure Terraform

1. **Download and Configure Terraform**: 
   - [Download Terraform](https://www.terraform.io/downloads) and set it up locally on your machine.

2. **Navigate to Terraform Directory**: 
   - Using your command line interface, navigate to the directory containing your Terraform configuration files `terraform`.

3. **Modify Terraform Code**: 
   - Open the Terraform configuration files (typically with a `.tf` extension) in a text editor. Customize the following aspects:
   
      - **Bucket Name**: Update the `bucket` attribute in the Terraform code with your desired bucket name.
      - **IAM Role Names**: Update the `name` attribute in relevant resource blocks for IAM roles.
      - **IAM Policy Permissions**: Adjust permissions in IAM policy documents as needed.
      - **Lambda Function Configuration**: Modify parameters such as function name, handler, runtime, etc., in `variables.tf`.
      - **CloudWatch Event Rule**: Customize event pattern in CloudWatch event rule.
      - **CloudWatch Log Groups and Streams**: Update names and retention periods.
      - **CloudWatch Alarms**: Configure alarms for monitoring Lambda errors and Step Function execution errors.
      - **Step Function Definition**: Adjust Step Function definition to define the workflow of your state machine.

4. **Deploy Terraform Infrastructure**: 
   - After making necessary modifications, save your changes and deploy the Terraform infrastructure:
     ```bash
     ../src/deploy.sh
     ```

### Step 5: Execute the State Machine

Refer to the screenshot below to locate the `Arn`, which should be placed in the designated area: `<state-machine-arn>`
![State Machine Screenshot](docs/state_arn.png)

**Execution**: 
   - After deploying the Terraform infrastructure, follow these steps to execute the Step Function:
     - In the root directory, execute the Step Function using the following command, replacing `<state-machine-arn>` with the ARN of your state machine:
       ```bash
       aws stepfunctions start-execution --state-machine-arn <state-machine-arn>
       ```
     - Monitor the execution of the state machine using the AWS Step Functions console or CLI.

**Step Function Success Notification Screenshot**:
![Step Function Success Notification](docs/step_function_success.png)

### Step 6: Test the Deployed Endpoint

Navigate to the `src` folder and provide the following:

1. **Obtain Endpoint for Prediction**:
   - Go to the AWS SageMaker console and navigate to Endpoints.
   - Copy the endpoint name or URL for prediction.
     Below is a screenshot of the endpoint:
   ![Endpoint Screenshot](docs/endpoint.png)


2. **Open the test.py Script**:
   - Open the `test.py` script in a text editor.


3. **Update Script Parameters**:
   - Modify the following parameters in the script:
     - `endpoint_name`: Replace `'your-endpoint-name'` with the copied endpoint name or URL.
     - `s3_bucket` and `s3_key`: Replace `'your-s3-bucket'` with the name of your S3 bucket where `test.protobuf` is located.

4. **Run the Test Script**:
   - After updating the script, execute the following command in the terminal or command prompt:

     ```bash
     python test.py
     ```

   This will fetch the `test.protobuf` file from your S3 bucket, invoke the SageMaker endpoint with this data, and print the prediction result.


### Step 7: Tests (Unit and Integration Tests)

1. **Navigate to the `Tests` Folder**:
   - Open your command line interface and navigate to the `Tests` folder in your project directory.

2. **Run Unit Test**:
   - Navigate to the `Lambda` folder and execute the following command to run the unit test:
     ```bash
     python unit_test.py
     ```

3. **Run Integration Test**:
   - Additionally, navigate to the `infrastructure` folder for the integration test and execute the following command:
     ```bash
     pytest -v test_integration.py
     ```

The screenshot below indicates that all 14 tests were successful:
![Integration Tests Success Notification](docs/integration_tests_success.png)

### Step 8: Clean Up

Execute the following command to clean up resources:

```bash
terraform destroy --auto-approve   
```

The screenshot below shows that all 22 resources created with Terraform have been successfully destroyed:
![Terraform Destroyed Notification](docs/terraform_destroyed.png)



## Continuous Integration (CI)

This project utilizes GitHub Actions for Continuous Integration (CI) to automate testing and ensure code quality. The CI/CD pipeline is defined in the `.github/workflows/ci.yml` file.

### CI/CD Pipeline Overview

The CI/CD pipeline consists of the following steps:

1. **Trigger**: The pipeline is triggered on every push to the `stage` or `main` branches.

2. **Environment Setup**: AWS credentials and region are configured using GitHub Secrets to enable interaction with AWS services.

3. **Build Job**: 
    - **Checkout code**: The latest code changes are fetched from the repository.
    - **Install Python Dependencies**: Required Python dependencies are installed using `pip`.
    - **Set up Terraform**: Terraform is configured with version 1.0.0.
    - **Execute Deploy Script**: The deployment script located in the `src` directory is executed to deploy the infrastructure.

4. **Testing**: 
    - **Run Unit Tests**: Unit tests located in the `Tests/Lambda` directory are executed to ensure individual components function correctly.
    - **Run Integration Tests**: Integration tests located in the `Tests/infrastructure` directory are executed to verify interactions between different modules.

5. **Infrastructure Cleanup**: After all tests are executed, the infrastructure is automatically destroyed using Terraform to avoid incurring unnecessary costs.

### Viewing CI/CD Status

You can view the status of the CI/CD pipeline runs in the "Actions" tab of this GitHub repository. Detailed logs and reports for each pipeline run are available to help diagnose issues and track progress.

Integrating CI/CD into the project workflow helps maintain code quality, streamline development processes, and ensure the reliability of the software.



### Additional Scripts

In addition to the main functionality provided by the project, there are additional scripts available for content-based filtering and collaborative filtering.

#### Content-Based Filtering Script (`src/cb.py`)

The `cb.py` script, located in the `src` directory, provides functionality for content-based movie recommendations. It analyzes the characteristics of movies and recommends similar movies based on user preferences. Before running the script, ensure preprocessing of the data:

Usage:
```bash
cd src
python preprocess.py  # Preprocesses the data
python cb.py          # Executes the content-based filtering script
```
#### Collaborative Filtering Script (src/cf.py)
The cf.py script, also located in the src directory, implements collaborative filtering techniques for movie recommendations. It analyzes user interactions and preferences to suggest movies similar to those liked by the user.
Execute the command below
```bash
cd src
python cf.py     # Executes the collaborative filtering script
```
