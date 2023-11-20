import json
import boto3
from datetime import datetime,timedelta
import pytz
import jmespath
from api.pdbc_api  import *
from api.aws_api import *
def myconverter(o):
    if isinstance(o, datetime):
        return o.__str__()

def create_client(account_id, region, assume_role, service):
    sts_client = boto3.client('sts')
    assumed_role_object=sts_client.assume_role(
        RoleArn="arn:aws:iam::"+str(account_id)+":role/"+assume_role,
        RoleSessionName="AssumeRoleSession1"
    )
    credentials=assumed_role_object['Credentials']
    client=boto3.client(
        service,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name=region
    )
    return client



def price(pricing_client,intype,region_name,platform,service_code):
    try:
        if service_code == 'AmazonRDS':
            field_value= 'databaseEngine'
        elif service_code == 'AmazonEC2':
            field_value = 'operatingSystem'
        else:
            field_value = None
        response = pricing_client.get_products(
        ServiceCode='{}'.format(service_code),
        Filters=[
                    {
                        'Type': 'TERM_MATCH',
                        'Field': 'ServiceCode',
                        'Value': '{}'.format(service_code)
                    },
              {
                        "Type": "TERM_MATCH",
                        "Field": field_value,
                        "Value": "{}".format(platform)
                    },
            
             {
                        "Type": "TERM_MATCH",
                        "Field": "location",
                        "Value": "{}".format(region_name)
                    },
             
              {
                        "Type": "TERM_MATCH",
                        "Field": "instanceType",
                        "Value":  "{}".format(intype)
                    },
                    {    'Type' :'TERM_MATCH', 'Field':'tenancy','Value':'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'},
                    {'Type' :'TERM_MATCH', 'Field':'marketoption','Value':'OnDemand'},
                    {'Type' :'TERM_MATCH', 'Field':'preInstalledSw','Value':'NA'},
                    {"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}
            
                ],
                    FormatVersion='aws_v1',
                    MaxResults=1
        )
        od = json.loads(response['PriceList'][0])['terms']['OnDemand']
        m=json.loads(response['PriceList'][0])
        
        id1 = list(od)[0]
        id2 = list(od[id1]['priceDimensions'])[0]
        # print(od[id1]['priceDimensions'][id2]['description'])
        return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']
            
    except Exception as e:
        print("something went wrong in pricing ")


def get_max_cpu(cloudwatch_client,id):
    try:
        u = datetime.utcnow()
        u = u.replace(tzinfo=pytz.utc)
         
        response = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=3600,
                                               Dimensions=[{
                                                   'Name': 'InstanceId','Value': id},],
                                               StartTime=u- timedelta(hours=336),
                                               EndTime=u,
                                               Statistics=['Maximum'])
        x=jmespath.search("Datapoints[*].[Maximum]",response)
        
        if len(x)>0:
            return (max(x)[0])
    except Exception as e:
       
        print("something went wrong in cloudwatch")

def platform(service_client,img_id):
    img_id=[img_id]
    response1= service_client.describe_images(ImageIds=img_id)
    data=json.dumps(response1,default = myconverter)
    data= json.loads(data)
    try:
        os=data['Images'][0]['PlatformDetails']
    except IndexError:
        os=None
    if os == "Linux/UNIX" or os == None:
        os="Linux"
    elif os == "Red Hat Enterprise Linux":
        os = "RHEL"
    elif os == "Windows" or os == "windows":
        os = "Windows"
    else:
        os =None
    return os

