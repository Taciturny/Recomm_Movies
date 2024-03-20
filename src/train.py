# import os
import io
from io import BytesIO
import boto3
import sagemaker
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sagemaker import image_uris
from sagemaker.session import s3_input
from sagemaker.estimator import Estimator
import sagemaker.amazon.common as smac
import time


class MovieRecommendationFlowSageMaker:
    @staticmethod
    def load_rating_data(s3_bucket, s3_key, max_retries=3):
        for attempt in range(max_retries):
            try:
                print(f"Loading data from S3 bucket: {s3_bucket}, key: {s3_key}")

                s3_client = boto3.client('s3')
                response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
                data = pd.read_csv(BytesIO(response['Body'].read()))

                # Print the column names and first few rows
                print("Column names in the loaded DataFrame:", data.columns)
                print("First few rows of the loaded DataFrame:", data.head())

                return data
            except Exception as e:
                print(f"An error occurred: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(5)  # Sleep for a few seconds before retrying
                else:
                    raise e
    

    @staticmethod
    def prepare_features(data):
        data['liked'] = (data['rating'] >= 4).astype('float32')

        # Convert numerical columns to float32
        numerical_columns = data.select_dtypes(include=['float64']).columns
        data[numerical_columns] = data[numerical_columns].astype('float32')

        # One-hot encode categorical variables in X before splitting
        categorical_columns = ['userId', 'movieId']

        # Use OneHotEncoder with sparse output
        encoder = OneHotEncoder(handle_unknown='ignore', sparse=True)
        X_sparse = encoder.fit_transform(data[categorical_columns])

        # Convert the sparse matrix to float32
        X_sparse = X_sparse.astype('float32')

        y = data['liked']
        return X_sparse, y



    @staticmethod
    def split_data(X, y):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        return X_train, X_test, y_train, y_test
       

    @staticmethod
    def write_data_to_protobuf(X, Y, bucket, key, folder_name="data", encoding="utf-8"):
        try:
            buf = io.BytesIO()

            # Reset the index of Y to ensure alignment with X
            Y_reset_index = Y.reset_index(drop=True)

            # Print or log intermediate values for debugging
            print("Sample Y_train:", Y_reset_index.head())
            print("Sample X_train:", X[:5])  # Print the first 5 rows

            smac.write_spmatrix_to_sparse_tensor(buf, X, Y_reset_index)
            buf.seek(0)
            
            # Update the object key to include the "data/" prefix
            obj = f'{folder_name}/{key}'
            
            boto3.resource('s3').Bucket(bucket).Object(obj).upload_fileobj(buf)
            return f's3://{bucket}/{obj}'
        except Exception as e:
            print(f"An error occurred: {e}")
            raise e


    @staticmethod
    def train_sagemaker_model(train_data_path, output_path, hyperparameters, X_train):
        role = "arn:aws:iam::690744128016:role/sagemaker-aws"

        container = image_uris.retrieve("factorization-machines", boto3.Session().region_name)
        train_records = s3_input(train_data_path, content_type='application/x-recordio-protobuf')

        estimator = Estimator(
            image_uri=container,
            role=role,
            instance_count=1,
            instance_type="ml.c4.xlarge",
            hyperparameters={
                "feature_dim": str(X_train.shape[1]),
                "num_factors": str(hyperparameters.get("num_factors", 25)),
                "mini_batch_size": str(hyperparameters.get("mini_batch_size", 1000)),
                "epochs": str(hyperparameters.get("epochs", 5)),
                "predictor_type":'binary_classifier',
            },
            output_path=output_path
        )

        # Fit the estimator
        estimator.fit({'train': train_records})



    @classmethod
    def main_flow(cls):
        s3_bucket = "datarecomm1.0"
        s3_key = "data/ratings_small.csv"
        
        # Load rating data
        data_task = MovieRecommendationFlowSageMaker.load_rating_data(s3_bucket, s3_key)
        
        # Prepare features
        train_data, train_labels = MovieRecommendationFlowSageMaker.prepare_features(data_task)
        
        # Split data
        X_train, X_test, y_train, y_test = MovieRecommendationFlowSageMaker.split_data(train_data, train_labels)
        # Save training data to protobuf format and upload to S3
        train_data_path = MovieRecommendationFlowSageMaker.write_data_to_protobuf(X_train, y_train, s3_bucket, "train.protobuf", folder_name="data", encoding="utf-8")

        # Save testing data to protobuf format and upload to S3
        test_data_path = MovieRecommendationFlowSageMaker.write_data_to_protobuf(X_test, y_test, s3_bucket, "test.protobuf", folder_name="data", encoding="utf-8")
        
        hyperparameters = {
            "num_factors": 25,
            "epochs": 25,
            "learning_rate": 0.007,
            "regularization": 0.2
        }

        train_data_path = "s3://datarecomm1.0/data/train.protobuf"
        output_path = "s3://datarecomm1.0/model"

        # Train SageMaker model
        model_artifact_task = MovieRecommendationFlowSageMaker.train_sagemaker_model(
            train_data_path=train_data_path,
            output_path=output_path,
            hyperparameters=hyperparameters,
            X_train=train_data
        )
        # Load the SageMaker Predictor
        predictor = sagemaker.predictor.Predictor(
        endpoint_name="movie-recommender-endpoint-config",
        sagemaker_session=sagemaker.Session()
        )


if __name__ == '__main__':
    MovieRecommendationFlowSageMaker.main_flow()

