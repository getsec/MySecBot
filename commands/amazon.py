import boto3
import json
from requests import get
from uuid import uuid4
from boto3 import resource
from boto3.dynamodb.conditions import Key
dynamodb_resource = resource('dynamodb')
TABLE_NAME="ShittyResources"

def log_resources(resource_id, resource, resource_type):
    dynamo = boto3.client('dynamodb')
    dynamo.put_item(
        TableName=TABLE_NAME,
        Item={
            'id': {"S": str(resource_id) },
            'resource': {"S": resource},
            'resource_type': {"S": resource_type}
        }
    )
    
def delete_s3_bucket(resource):

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(resource)
    bucket.objects.all().delete()

    s3_buck = boto3.client('s3')
    s3_buck.delete_bucket(
        Bucket=resource
    )

def scan_table_allpages(table_name, filter_key=None, filter_value=None):
    """
    Perform a scan operation on table. Can specify filter_key (col name) and its value to be filtered. This gets all pages of results.
    Returns list of items.
    """
    table = dynamodb_resource.Table(table_name)

    if filter_key and filter_value:
        filtering_exp = Key(filter_key).eq(filter_value)
        response = table.scan(FilterExpression=filtering_exp)
    else:
        response = table.scan()

    items = response['Items']
    while True:
        if response.get('LastEvaluatedKey'):
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items += response['Items']
        else:
            break

    return items

def delete_db_item(TABLE_NAME, pk_name, pk_value):
    """
    Delete an item (row) in table from its primary key.
    """
    table = dynamodb_resource.Table(TABLE_NAME)
    response = table.delete_item(Key={pk_name: pk_value})

    return

def teardown():
    s3_buckets = scan_table_allpages(TABLE_NAME, filter_key="resource_type", filter_value="s3")
    print(s3_buckets)
    for items in s3_buckets:
        delete_s3_bucket(items['resource'])
        pk_name = "id"
        pk_value = items['id']
        print(f"Deleted: {items['resource']}")
        delete_db_item(TABLE_NAME, pk_name, pk_value)

def create_bucket():
    name = f"shitty-employee-bucket-{str(uuid4()).split('-')[0]}"
    resource_id = uuid4()
    resource_type = "s3"
    resource = name
    s3 = boto3.client(resource_type)
    
    resp = s3.create_bucket(
        Bucket=name,
        ACL='public-read',
        CreateBucketConfiguration={'LocationConstraint': 'ca-central-1'},

    )
    s3.put_bucket_policy(
        Bucket=name,
        Policy=json.dumps({
            "Version": "2012-10-17",
            "Id": "S3PolicyId1",

            "Statement": [

                {
                "Sid": "IPAllow",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{name}/*"
           
                }
            ]
            })
    )
    pic = get("https://image.shutterstock.com/image-vector/wrench-hammer-tools-icon-isolated-260nw-181305683.jpg")
    item = boto3.client('s3')
    key_name = "pic-of-you.png"
    item.put_object(
         Bucket=name,
         Key=key_name,
         Body=pic.content

    )
    
    log_resources(resource_id, resource, resource_type)
    return resp['Location'] + key_name
