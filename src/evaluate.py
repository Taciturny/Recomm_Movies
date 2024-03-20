import io
import boto3
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sagemaker import Predictor
from sagemaker.serializers import IdentitySerializer
from sagemaker.deserializers import NumpyDeserializer
import sagemaker.amazon.common as smac

# Define a lambda function for loading protobuf data from S3
load_protobuf_data = lambda s3_bucket, s3_key: boto3.client('s3').get_object(Bucket=s3_bucket, Key=s3_key)['Body'].read()

# Define a lambda function for evaluating the model
evaluate_model = lambda predictor, X_test, y_test: (
    (
        accuracy_score(y_test, (predictor.predict(X_test) > 0.5).astype('float32')),
        confusion_matrix(y_test, (predictor.predict(X_test) > 0.5).astype('float32')),
        classification_report(y_test, (predictor.predict(X_test) > 0.5).astype('float32'))
    )
)

# Define the main lambda handler function
def lambda_handler(event, context):
    # Define S3 bucket and key for test data
    s3_bucket = "your-s3-bucket"
    s3_key = "test.protobuf"
    
    # Load test data
    data_buffer = load_protobuf_data(s3_bucket, s3_key)
    
    # Deserialize protobuf data
    data = smac.read_records(data_buffer)
    features = np.array([r.features.values for r in data])
    labels = np.array([r.label['values'][0] for r in data])
    
    # Load the SageMaker Predictor
    predictor = Predictor(
        endpoint_name="your-endpoint-name",
        serializer=IdentitySerializer(content_type="application/x-recordio-protobuf"),
        deserializer=NumpyDeserializer()
    )
    
    # Evaluate the model
    accuracy, confusion, classification_report_str = evaluate_model(predictor, features, labels)
    
    # Log the evaluation metrics
    print(f"Accuracy: {accuracy}")
    print("Confusion Matrix:")
    print(confusion)
    print("Classification Report:")
    print(classification_report_str)
    
    # Return the evaluation metrics if needed
    return {
        "Accuracy": accuracy,
        "Confusion Matrix": confusion,
        "Classification Report": classification_report_str
    }
