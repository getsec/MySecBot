import boto3
import json
from requests import get
from uuid import uuid4
from boto3 import resource
from boto3.dynamodb.conditions import Key
import watchtower, logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())
dynamodb_resource = resource('dynamodb')
TABLE_NAME="ShittyResources"


def save_state(resource, resource_type):
    dynamo = boto3.client('dynamodb')
    dynamo.put_item(
        TableName=TABLE_NAME,
        Item={
            'id': {"S": str(uuid4()) },
            'resource': {"S": resource},
            'resource_type': {"S": resource_type}
        }
    )
    

def delete_s3_bucket(resource):

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(resource)
    bucket.objects.all().delete()

    s3_buck = boto3.client('s3')
    delete_buck = s3_buck.delete_bucket(
        Bucket=resource
    )
    logger.info(dict(Event="DeleteBucket", Resource=resource, details=delete_buck))


def delete_sg(resource):
    client = boto3.client('ec2')
    delete = client.delete_security_group(
        GroupId=resource
    )
    logger.info(dict(Event="DeleteSecurityGroup", Resource=resource, details=delete))


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


def delete_iam_user(resource):
    client = boto3.client('iam')
    client.detach_user_policy(
        UserName=resource,
        PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
    )

    deleto = client.delete_user(
        UserName=resource
    )
    logger.info(dict(Event="DeleteIamUser", resource=resource, Details=deleto))


def teardown():
    s3_buckets = scan_table_allpages(TABLE_NAME, filter_key="resource_type", filter_value="s3")
    iam_users = scan_table_allpages(TABLE_NAME, filter_key="resource_type", filter_value="iam")
    security_groups = scan_table_allpages(TABLE_NAME, filter_key="resource_type", filter_value="sg")
    for items in s3_buckets:
        delete_s3_bucket(items['resource'])
        pk_name = "id"
        pk_value = items['id']
        print(f"Deleted: {items['resource']}")
        delete_db_item(TABLE_NAME, pk_name, pk_value)
    for items in security_groups:
        delete_sg(items['resource'])
        pk_name = "id"
        pk_value = items['id']
        print(f"Deleted: {items['resource']}")
        delete_db_item(TABLE_NAME, pk_name, pk_value)
    for items in iam_users:
        delete_iam_user(items['resource'])
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
    logger.info(dict(Event="CreateBucket",Resource=name, details=resp))
    save_state( resource, resource_type)
    return resp['Location'] + key_name

def create_shitty_sg():
    client = boto3.client('ec2')
    name = f"shitty-securitygroup-{str(uuid4()).split('-')[-1]}"
    group_id = client.create_security_group(
        Description=name,
        GroupName=name
    )
    resource_id = str(uuid4())
    resource = group_id['GroupId']
    resource_type = "sg"
    save_state(resource, resource_type)
    logger.info(dict(Event="CreateSecurityGroup",Resource=resource, details=group_id))

    sg = client.authorize_security_group_ingress(
        GroupId=resource,
        IpPermissions=[
            {
            'FromPort': 22,
            'ToPort': 22,
            'IpProtocol': 'tcp',
            'IpRanges': [
                {
                    'CidrIp': '0.0.0.0/0',
                    'Description': 'bad-group'
                }
            ]
            }]
    )
    logger.info(dict(Event="AuthorizeSecurityGroupIngress", Resource=resource, details=sg))


def create_bad_iam_user():
    client = boto3.client('iam')
    name = f"ShittyUser-{str(uuid4()).split('-')[-1]}"
    resource = name
    resource_type = "iam"
    resp = client.create_user(
        UserName=name,
        Tags=[
            {
                'Key': 'Usage',
                'Value': 'created by the shitty bot'
            }
        ]
    )
    save_state(resource, resource_type)
    logger.info(dict(Event="CreateIamUser", Resource=resource, details=resp))

    policy = client.attach_user_policy(
        UserName=name,
        PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
    )
    logger.info(dict(Event="AttachUserPolicy", details=resp))
    return resource