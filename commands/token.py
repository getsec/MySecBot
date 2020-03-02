import boto3 

def get_token():
    client = boto3.client('ssm')
    resp = client.get_parameter(
        Name='DISCORD_TOKEN',
        WithDecryption=True
    )
    
    return resp['Parameter']['Value']
