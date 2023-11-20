import datetime as dt
from api.aws_api import  *
from api.pdbc_api import *
from api.aws_api import platform as pt
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))
account_ids=[]
connection = db_connection("so")
cursor = connection.cursor()
query_account_id ='select instance_id from so.ec2_instances'
cursor.execute(query_account_id)
list_ins_ids = cursor.fetchall()
list_ins_ids = [x[0] for x in list_ins_ids]
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
columns=get_columns("so.ec2_instances")
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
            response = ec2.describe_instances()
            data=json.dumps(response,default = myconverter)
            data= json.loads(data) 
            tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region
            ssm_response = ssm_client.get_parameter(Name = tmp)
            region_name = ssm_response['Parameter']['Value']
            for i in data["Reservations"]:
                print("-ok-")
        
                lt=i['Instances'][0]['LaunchTime']
                ins_id=i['Instances'][0]['InstanceId']
                cloudwatch_client = create_client(account_id,region,assume_role,'cloudwatch')
                m = get_idle_hours_ec2_instance(cloudwatch_client,ec2,ins_id,list_ins_ids)
                if m==None:
                        pass
                else:
                    if m[0]== 0:
                        pass
                    else:
                        ins_type=i['Instances'][0]['InstanceType']
                        instance_state=i['Instances'][0]['State']['Name']
                        try:
                            ins_name=[key['Value'] for key in i['Instances'][0]['Tags'] if key['Key'] == 'Name'][0]
                        except Exception as e:
                            ins_name=None
                        try:
                            tag_value_1=str(tag_keys[0])+":"+[key['Value'] for key in i['Instances'][0]['Tags'] if key['Key'] == tag_keys[0]][0]
                        except Exception as e:
                            tag_value_1=None
                        try:
                            tag_value_2=str(tag_keys[1])+":"+[key['Value'] for key in i['Instances'][0]['Tags'] if key['Key'] == tag_keys[1]][0]
                        except Exception as e:
                            tag_value_2=None
                        try:
                            tag_value_3=str(tag_keys[2])+":"+[key['Value'] for key in i['Instances'][0]['Tags'] if key['Key'] == tag_keys[2]][0]
                        except Exception as e:
                            tag_value_3=None
                        try:
                            tag_value_4=str(tag_keys[3])+":"+[key['Value'] for key in i['Instances'][0]['Tags'] if key['Key'] == tag_keys[3]][0]
                        except Exception as e:
                            tag_value_4=None
                        ins_region=region
                        ins_image_id=i['Instances'][0]['ImageId']
                        os=platform(ec2,ins_image_id)
                        hourly_price=price(pricng,ins_type,region_name,os,'AmazonEC2')
                        df_new_rows = pd.DataFrame({
                                            'instance_id' : [ins_id],
                                            'instance_name' : [ins_name],
                                            'instance_type' : [ins_type],
                                            'account_id': [account_id],
                                            'account_name': [account_name],
                                            'instance_recent_launch_time' :[lt],
                                            'region': [ins_region],
                                            'instance_state_name'  : [instance_state],
                                            'tag_value_1' : [tag_value_1],
                                            'tag_value_2' : [tag_value_2],
                                            'tag_value_3' : [tag_value_3],
                                            'tag_value_4' : [tag_value_4],
                                            'not_being_used_from':[m[2]],
                                            'recent_scan_time' :  [datetime.now()],
                                            'platform': [os],
                                            'hourly_price': [hourly_price],
                                            'total_waste_spent':[ float(hourly_price)*m[0]],
                                            'unused_hours': [m[0]]
                                            })
                        data_from_aws = pd.concat([data_from_aws, df_new_rows])
                        data_from_aws= data_from_aws.astype({"unused_hours": int})
        except Exception as e:
            print(region)
            print("----")
            print(e)      
    if data_from_aws.empty:
        remove_records("so.ec2_instances","account_name",account_name)
    else:
        output=pass_to_db("so.ec2_instances",data_from_aws,"account_name",ignore_columns)  
        print("finally")
print("----------------------- %s seconds ----------------------" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")
