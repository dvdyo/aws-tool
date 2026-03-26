import boto3

def get_client(service_name, region_name="eu-north-1"):
    """Shortcut to get a boto3 client for any AWS service"""
    return boto3.client(service_name, region_name=region_name)
