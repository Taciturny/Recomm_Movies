import boto3

def fetch_protobuf_data_from_s3(bucket, key):
    """
    Fetches protobuf data from the specified S3 bucket and key.
    """
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)
    protobuf_data = response['Body'].read()
    return protobuf_data

def invoke_endpoint(endpoint_name, protobuf_data):
    """
    Invokes the specified SageMaker endpoint with the provided protobuf data.
    """
    sagemaker_client = boto3.client('sagemaker-runtime')
    response = sagemaker_client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/x-recordio-protobuf',
        Body=protobuf_data
    )
    prediction = response['Body'].read().decode()
    return prediction

def main():
    # Specify endpoint details
    endpoint_name = 'your-endpoint-name'
    s3_bucket = 'your-s3-bucket'
    s3_key = 'data/test.protobuf'  # Adjust the key to point to the data folder

    # Fetch protobuf data from S3
    protobuf_data = fetch_protobuf_data_from_s3(s3_bucket, s3_key)

    # Invoke the endpoint and get predictions
    prediction = invoke_endpoint(endpoint_name, protobuf_data)

    # Print the prediction
    print('Prediction:', prediction)

if __name__ == "__main__":
    main()
