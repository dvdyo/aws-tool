import boto3

def get_client(service_name, region_name="eu-north-1"):
    """Shortcut to get a boto3 client for any AWS service"""
    return boto3.client(service_name, region_name=region_name)

def get_resource(service_name):
    """I doon't know why did i even put this bs here"""
    return boto3,resource(service_name)
