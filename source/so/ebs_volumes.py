from api.pdbc_api  import *
from api.aws_api import *
import re
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))
assume_role="role_admin"
account_ids=[]
connection = db_connection("so")
try:
    cursor = connection.cursor()
    query = "SELECT account_id from ad.aws_accounts;"
    cursor.execute(query)
    records = cursor.fetchall()
    for i in records:
        account_ids.append(i[0])  
    cursor.close()
except:
    print("check whether the database exits or not")

columns=get_columns("so.ebs_volumes")
ignore_columns=['ignore']
for account_id in account_ids:
    data_from_aws = pd.DataFrame(columns=columns)
    account_details=get_awsaccount_details(account_id,connection) 
    regions=account_details['regions']
    account_name=account_details['account_name'][0]
    tag_keys=account_details['tag_keys']
    assume_role=account_details['assume_role'][0]

    for region in regions: 
        try:
            ebs = create_client(account_id, region, assume_role, 'ec2')
            ec2 = create_client(account_id, region, assume_role, 'ec2')
            ssm_client =create_client(account_id, region, assume_role, 'ssm')
            response1 = ec2.describe_instances()
            data1=json.dumps(response1,default = myconverter)
            data1= json.loads(data1)
            response=ebs.describe_volumes()
            data=json.dumps(response,default = myconverter)
            data= json.loads(data)
            tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region
            ssm_response = ssm_client.get_parameter(Name = tmp)
            region_name = ssm_response['Parameter']['Value']
            for j in data["Volumes"]:
                for i in data1["Reservations"]:
                    instance_state=i['Instances'][0]['State']['Name']
                    ins_id=i['Instances'][0]['InstanceId']
                    status = i['Instances'][0]
                    if j["Attachments"]!=[]:
                        attached_ec2_instance_id=j["Attachments"][0]["InstanceId"]
                    else:
                        attached_ec2_instance_id=None
                    if status['State']['Name']=="stopped" and attached_ec2_instance_id ==ins_id:
                        volume_id=j["Attachments"][0]["VolumeId"]
                        attached_ec2_instance_status = j["State"]
                        volume_size   =j["Size"]
                        volumes_type   = j["VolumeType"]
                        stopped_reason = status['StateTransitionReason']
                        now = datetime.now()
                        latest_scan_time = response1['ResponseMetadata']['HTTPHeaders']['date']
                        latest_scan_time =  now
                        try:
                            instance_stopped_time = re.findall('.*\((.*)\)', stopped_reason)[0]
                        except IndexError:
                            instance_stopped_time=None
                        ebs_name_map = {'standard': 'Magnetic','gp2': 'General Purpose','io1': 'Provisioned IOPS','st1': 'Throughput Optimized HDD','sc1': 'Cold HDD'}
                        pricing_client = create_client(account_id, "us-east-1",assume_role,"pricing")
                        for ebs_code in ebs_name_map:
                            response = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=[
                                        {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': ebs_name_map[ebs_code]}, 
                                        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value':region_name}])
                            for result in response['PriceList']:
                                json_result = json.loads(result)
                                for json_result_level_1 in json_result['terms']['OnDemand'].values():
                                    for json_result_level_2 in json_result_level_1['priceDimensions'].values():
                                        for price_value in json_result_level_2['pricePerUnit'].values():
                                            continue
                            ebs_name_map[ebs_code] = float(price_value)
                        if volumes_type =="gp2":
                            p=ebs_name_map["gp2"]
                        elif volumes_type =="standard":
                            p=ebs_name_map["standard"]
                        elif volumes_type =="st1":
                            p=ebs_name_map["st1"]
                        elif volumes_type =="sc1":
                            p=ebs_name_map["sc1"]
                        elif volumes_type =="io1":
                            p=ebs_name_map["io1"] ## P is hourly price 
                        else:
                            p=None
                        hourly_price= p      
                        d=instance_stopped_time   ## Calculation for unused time
                        if d==None:
                            break
                        else:
                            d=d.replace(" GMT", "")
                        d=datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
                        m=now-d ## unused time in days 
                        h=m.total_seconds() ## unused time in sec
                        h=divmod(h, 3600)[0] ##unused time in hours
                        k= 'Tags'
                        if k in j.keys():
                                try:
                                    volume_tag_name=[key['Value'] for key in j['Tags'] if key['Key'] == 'Name'][0]
                                except Exception as e:
                                    volume_tag_name=None
                                
                                try:
                                    tag_value_1 =str(tag_keys[0])+":"+[key['Value'] for key in j['Tags'] if key['Key'] == tag_keys[0]][0]
                                except Exception as e:
                                    tag_value_1=None
                                try:
                                    tag_value_2 =str(tag_keys[1])+":"+[key['Value'] for key in j['Tags'] if key['Key'] == tag_keys[1]][0]
                                except Exception as e:
                                    tag_value_2=None 
                                try:
                                    tag_value_3 =str(tag_keys[2])+":"+[key['Value'] for key in j['Tags'] if key['Key'] == tag_keys[2]][0]
                                except Exception as e:
                                        tag_value_3=None 
                                try:
                                    tag_value_4  = str(tag_keys[3])+":"+[key['Value'] for key in j['Tags'] if key['Key'] == tag_keys[3]][0]        
                                except Exception as e:
                                    tag_value_4=None  
                        else:
                                volume_tag_name=None
                                tag_value_1=None
                                tag_value_2=None
                                tag_value_3=None
                                tag_value_4=None
                        unused_hours= int(h)
                        total_waste_spent = unused_hours*hourly_price
                        volume_state=j["State"]
                        df_new_rows = pd.DataFrame({
                                        'volume_id' : [volume_id],
                                        'volume_tag_name':[volume_tag_name],                        
                                        'attached_ec2_instance_id' : [attached_ec2_instance_id],
                                        'attached_ec2_instance_status':[instance_state],
                                        'volume_size':[volume_size],
                                        'volumes_type':[volumes_type],
                                        'hourly_price':[hourly_price],
                                        'tag_value_1' : [tag_value_1],
                                        'tag_value_2' : [tag_value_2],
                                        'tag_value_3' : [tag_value_3],
                                        'tag_value_4' : [tag_value_4],
                                        'account_id' : [account_id],
                                        'account_name' : [account_name],
                                        'region':[region],
                                        'instance_stopped_time':[instance_stopped_time]   ,
                                        'unused_hours':[unused_hours]  ,
                                        'total_waste_spent':[total_waste_spent] ,
                                        'recent_scan_time':[latest_scan_time] ,
                                        'volume_state':[volume_state],
                                        })
                        data_from_aws = pd.concat([data_from_aws, df_new_rows])
        except Exception as e:
            print(region)
            print("----")
            print(e)
    if data_from_aws.empty:
        remove_records("so.ebs_volumes","account_name",account_name)
    else:
        output=pass_to_db("so.ebs_volumes",data_from_aws,"account_name",ignore_columns)
        print(output + " for " + str(account_name))
print("----------------------- %s seconds ----------------------" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")    
