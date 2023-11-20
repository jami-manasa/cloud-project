from api.pdbc_api  import *
from api.aws_api import *
import re
import time
import pytz
from dateutil import parser
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))
def get_ec2_info(ins_id,ec2):
    response = ec2.describe_instances(InstanceIds=[ins_id,],)
    reason=response["Reservations"][0]['Instances'][0]['StateTransitionReason']
    status=response["Reservations"][0]['Instances'][0]['State']['Name']
    return status,reason
account_ids=[]
#db connection
connection = db_connection("ss")
try:
    cursor = connection.cursor()
    #query for getting account details 
    Query = "SELECT account_id from ad.aws_accounts;"
    cursor.execute(Query)
    records = cursor.fetchall()
    for i in records:
        account_ids.append(i[0])  
    cursor.close()
except:
    print("check whether the database exits or not")
regions=[]
def myconverter(o):
    if isinstance(o, datetime):
        return o.__str__()
columns=get_columns("so.eip_addresses")
ignore_columns=['ignore']
for account_id in account_ids:
    data_from_aws = pd.DataFrame(columns=columns)
    #account details from database
    account_details=get_awsaccount_details(account_id,connection) 
    regions=account_details['regions']
    account_name=account_details['account_name'][0]
    tag_keys=account_details['tag_keys']
    assume_role=account_details['assume_role'][0]
    for region in regions:
        try:
            ec2 = create_client(account_id, region, assume_role, 'ec2') 
            ssm_client =create_client(account_id, region, assume_role, 'ssm') 
            pricng = create_client(account_id, 'us-east-1', assume_role, 'pricing') 
            response = ec2.describe_addresses()
            data=json.dumps(response,default = myconverter)
            data= json.loads(data) 
            tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region
            ssm_response = ssm_client.get_parameter(Name = tmp)
            region_name = ssm_response['Parameter']['Value']
            x=jmespath.search("Addresses[*].[Tags]",response)
            for i in data['Addresses']:
                k= 'Tags'
                if k in i.keys():
                        try:
                            tag_value_1 =str(tag_keys[0])+":"+[key['Value'] for key in i['Tags'] if key['Key'] == tag_keys[0]][0]
                        except Exception as e:
                            tag_value_1=None
                        try:
                            tag_value_2 =str(tag_keys[1])+":"+[key['Value'] for key in i['Tags'] if key['Key'] == tag_keys[1]][0]
                        except Exception as e:
                            tag_value_2=None 
                        try:
                            tag_value_3 =str(tag_keys[2])+":"+[key['Value'] for key in i['Tags'] if key['Key'] == tag_keys[2]][0]
                        except Exception as e:
                                tag_value_3=None 
                        try:
                            tag_value_4  = str(tag_keys[3])+":"+[key['Value'] for key in i['Tags'] if key['Key'] == tag_keys[3]][0]        
                        except Exception as e:
                            tag_value_4=None  
                else:
                    volume_tag_name=None
                    tag_value_1=None
                    tag_value_2=None
                    tag_value_3=None
                    tag_value_4=None
                ipv4_address = i['PublicIp']
                allocation_id  = i['AllocationId']
                word = "InstanceId"
                if word in i.keys():
                    try:
                        res = get_ec2_info(i['InstanceId'],ec2)
                        stopped_reason = res[1]
                        status = res[0]
                        if status == "running":
                            pass
                        else:
                            instance_stopped_time = re.findall('.*\((.*)\)', stopped_reason)[0]
                            d = instance_stopped_time
                            d=d.replace(" GMT", "")
                            d=datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
                            m=datetime.now()-d ## unused time in days 
                            h=m.total_seconds() ## unused time in sec
                            h=divmod(h, 3600)[0]
                    except IndexError:
                        instance_stopped_time=None
                    association_id = i['AssociationId']
                else:
                    association_id = None
                    h = 336
                account_id = account_id
                account_name = account_name
                region=  region
                total_wastage = "total_wastage"
                if word in i.keys():
                    pass
                else:
                    df_new_rows = pd.DataFrame({
                                        'ipv4_address' : [ipv4_address],
                                        'allocation_id' : [allocation_id] ,
                                        'association_id' : [association_id] ,
                                        'tag_value_1': [tag_value_1],
                                        'tag_value_2': [tag_value_2],
                                        'tag_value_3': [tag_value_3],
                                        'tag_value_4': [tag_value_4], 
                                        'hourly_price': [0.005],
                                        'unused_hours' : [h], 
                                        'account_id': [account_id],
                                        'account_name': [account_name],
                                        'region': [region],
                                        'total_waste_spent':[h*0.005],
                                        'recent_scan_time' : [datetime.now()],
                                        })
                    data_from_aws = pd.concat([data_from_aws, df_new_rows])
        except Exception as e:
            print(region)
            print("----")
            print(e)
    if data_from_aws.empty:
        remove_records("so.eip_addresses","account_name",account_name)
    else:
        output=pass_to_db("so.eip_addresses",data_from_aws,"account_name",[])
        print("done")
print("----------------------- %s seconds ----------------------" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")
       