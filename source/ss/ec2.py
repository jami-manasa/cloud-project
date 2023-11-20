# import sys,os
# sys.path.insert(1,os.path.abspath(__file__).split('source')[0]+'source/api')
# from imports import *
import datetime as dt

from datetime import datetime
# from pwd import struct_passwd
from api.pdbc_api  import *
from api.aws_api import *
import time
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))
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
columns=get_columns("ss.ec2_instances_schedules")
ignore_columns=['enable_schedules','ec2_group_name','is_statefull_set','statefull_set_name','statefull_set_arn', 'auto_stop_enable','mon_str_time','mon_stp_time','tue_str_time','tue_stp_time','wed_str_time','wed_stp_time','thu_str_time','thu_stp_time','fri_str_time','fri_stp_time','sat_str_time','sat_stp_time','sun_str_time','sun_stp_time','stack_arn']
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
            #creating client ec2 
            ec2 = create_client(account_id, region, assume_role, 'ec2') 
            #creating client ssm client
            ssm_client =create_client(account_id, region, assume_role, 'ssm') 
            #creating client pricing
            pricng = create_client(account_id, 'us-east-1', assume_role, 'pricing') 
            #intsances details from aws console
            response = ec2.describe_instances()
            #intsances details from aws console
            data=json.dumps(response,default = myconverter)
            # instace details
            data= json.loads(data) 
            # print(data)
            tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region
            ssm_response = ssm_client.get_parameter(Name = tmp)
            region_name = ssm_response['Parameter']['Value']
            for i in data["Reservations"]:
                lt=i['Instances'][0]['LaunchTime']
                k=lt.replace("+00:00","")
                rlt = dt.datetime.strptime(k, '%Y-%m-%d %H:%M:%S')
                try:
                    tag_list=i['Instances'][0]['Tags']
                except:
                    tag_list=[]
                keys=[]
                # list of  instances tags 
                for k in tag_list: 
                    k=k['Key']
                    keys.append(k)
                for j in range(len(keys)):
                    con=[]
                    #if not in auto scaling  grp list then it will to database
                    if keys[j][0:3]!="aws" and keys[j]=="Name":  
                        con.append("yes")
                    if con:
                        ins_id=i['Instances'][0]['InstanceId']
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
                        #image id of particular instances
                        ins_image_id=i['Instances'][0]['ImageId']
                        os=platform(ec2,ins_image_id)  
                        hourly_price=price(pricng,ins_type,region_name,os,'AmazonEC2')
                        df_new_rows = pd.DataFrame({'instance_id' : [ins_id],   
                                        'instance_tag_name' : [ins_name],
                                        'tag_value_1' : [tag_value_1],
                                        'tag_value_2' : [tag_value_2],
                                        'tag_value_3' : [tag_value_3],
                                        'tag_value_4' : [tag_value_4],
                                        'instance_type':[ins_type],
                                        'account_id' : [account_id],
                                        'account_name' : [account_name],
                                        'region':[region],
                                        'platform':[os],
                                        'recent_launch_time':[rlt],
                                        'instance_state':[instance_state],
                                        'hourly_price':[hourly_price]
                                        }) 
                        data_from_aws = pd.concat([data_from_aws, df_new_rows])
            print(data_from_aws)
        except Exception as e:
            print(region)
            print("----")
            print(e)
    if data_from_aws.empty:
        #if cureent  dataframe empty it will delete previous data from database(only based on account name)
        remove_records("ss.ec2_instances_schedules","account_name",account_name)
    else:
        #pass_to_db function for curd operation
        output=pass_to_db("ss.ec2_instances_schedules",data_from_aws,"account_name",ignore_columns)  
        print(output + " for " + str(account_name))
data=get_dbdata("ss.ec2_instances_schedules")
print("%s seconds ====>" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")


