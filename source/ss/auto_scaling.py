# import sys,os
# sys.path.insert(1,os.path.abspath(__file__).split('source')[0]+'source/api')
# from imports import *
from api.pdbc_api  import *
from api.aws_api import *
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))

def LaunchConfigurationDetails(lc,LaunchConfigurationName):
    ImageId=None
    lc_response = lc.describe_launch_configurations(
            LaunchConfigurationNames=[
            LaunchConfigurationName,
            ], )
    lc_response=json.dumps(lc_response,default = myconverter)
    lc_response=json.loads(lc_response)
    for j in lc_response['LaunchConfigurations']:
        ImageId=j['ImageId']
        instance_type=j['InstanceType']
    return ImageId,instance_type
account_ids=[]
connection = db_connection("ss")
try:
    cursor = connection.cursor()
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
columns=get_columns("ss.auto_scaling_groups")
ignore_columns=['user_maximum_capacity','mon_scaleout_time', 'mon_scaleout_count', 'mon_scalein_time', 'mon_scalein_count','tue_scaleout_time', 'tue_scaleout_count', 'tue_scalein_time', 'tue_scalein_count', 'wed_scaleout_time', 'wed_scaleout_count', 'wed_scalein_time', 'wed_scalein_count', 'thu_scaleout_time', 'thu_scaleout_count', 'thu_scalein_time', 'thu_scalein_count', 'fri_scaleout_time', 'fri_scaleout_count', 'fri_scalein_time', 'fri_scalein_count', 'sat_scaleout_time', 'sat_scaleout_count', 'sat_scalein_time', 'sat_scalein_count', 'sun_scaleout_time', 'sun_scaleout_count', 'sun_scalein_time', 'sun_scalein_count']
for account_id in account_ids:
    data_from_aws = pd.DataFrame(columns=columns)
    account_details=get_awsaccount_details(account_id,connection)
    account_name=account_details['account_name'][0]
    acc_id=account_id
    regions=account_details['regions']
    account_name=account_details['account_name'][0]
    tag_keys=account_details['tag_keys']
    assume_role=account_details['assume_role'][0]
    for region in regions:
        try:
            ec2 = create_client(account_id, region, assume_role, 'ec2')
            auto_client=create_client(account_id, region, assume_role, 'autoscaling')
            ssm_client =create_client(account_id, region, assume_role, 'ssm')
            response = auto_client.describe_auto_scaling_groups()
            data=json.dumps(response,default = myconverter)
            data= json.loads(data)
            tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region
            ssm_response = ssm_client.get_parameter(Name = tmp)
            region_name = ssm_response['Parameter']['Value']
            response1 = auto_client.describe_policies()
            data1=json.dumps(response1,default = myconverter)
            data1=json.loads(data1)
            res = auto_client.describe_tags()
            tag=json.dumps(res,default = myconverter)
            tag=json.loads(tag)
            lc=create_client(account_id, region, assume_role, 'autoscaling')
            pricng = create_client(account_id, 'us-east-1', assume_role, 'pricing') 
            # print(data)
            for i in data['AutoScalingGroups']:
                # print(i)
                AutoScalingGroupName=i["AutoScalingGroupName"]
                AutoScalingGroupARN=i['AutoScalingGroupARN']
                MinSize=int(i['MinSize'])
                MaxSize=int(i['MaxSize'])
                DesiredCapacity=int(i['DesiredCapacity'])
                HealthCheckGracePeriod=i['HealthCheckGracePeriod']
                LoadBalancerNames=i['LoadBalancerNames']
                HealthCheckType=i['HealthCheckType']
                try:
                    LaunchConfigurationName=i[ 'LaunchConfigurationName']
                except:
                    LaunchConfigurationName=None   
                try:
                    LaunchTemplateName=i['LaunchTemplate']['LaunchTemplateName']
                except:
                    LaunchTemplateName=None
                print(LaunchConfigurationName,"---------",LaunchTemplateName)
                InstanceId=[]
                HealthStatus=[]
                for ins in i['Instances']: 
                    Id=ins['InstanceId']
                    InstanceId.append(Id)
                    Status=ins['HealthStatus']
                    HealthStatus.append(Status) 
                if LaunchConfigurationName !=None:
                    lcd = LaunchConfigurationDetails(lc,LaunchConfigurationName)
                    ImageId = lcd[0]
                    instance_type = lcd[1]
                if LaunchTemplateName !=None:
                    ImageId = None
                    if i['Instances'] == []:
                        instance_type = None
                    else:
                        instance_type = i['Instances'][0]['InstanceType']
                # print(i)
                    
                if ImageId!=None:
                    os=platform(ec2,ImageId)
                    hourly_price=price(pricng,instance_type,region_name,os,'AmazonEC2')
                else:
                    os=None
                    hourly_price=None
                if hourly_price != None:
                    hourly_price = str(float(hourly_price))
                
                # print(os,"-----",hourly_price,"-------",instance_type,"---",AutoScalingGroupName)
                for ttp in data1['ScalingPolicies']:
                    tag_value_1,tag_value_2,tag_value_3,tag_value_4=None,None,None,None
                    if AutoScalingGroupName==ttp['AutoScalingGroupName']:
                            if ttp['Enabled']==True:
                                Enabled="True"
                                try:
                                    PolicyName=ttp['PolicyName']
                                except:
                                    PolicyName=None
                                try:
                                    PolicyType=ttp['PolicyType']
                                except:
                                    PolicyType=None
                            
                                try:
                                    PredefinedMetricType=ttp['TargetTrackingConfiguration']['PredefinedMetricSpecification']['PredefinedMetricType']
                                except:
                                    PredefinedMetricType=None
                                try:
                                    TargetValue=ttp['TargetTrackingConfiguration']['TargetValue']

                                except:
                                    TargetValue=None
                                try:
                                    EstimatedInstanceWarmup=ttp['EstimatedInstanceWarmup']
                                except:
                                    EstimatedInstanceWarmup=None
                            else:
                                Enabled="Flase"
                            try:
                                tag_value_1=None
                            except Exception as e:
                                tag_value_1=None
                            try:
                                tag_value_2=None
                            except Exception as e:
                                tag_value_2=None
                            try:
                                tag_value_3=None
                            except Exception as e:
                                tag_value_3=None
                            try:
                                tag_value_4=None
                            except Exception as e:
                                tag_value_4=None
            
                m=[]
                for tags in tag['Tags']:
                    if  AutoScalingGroupName==tags['ResourceId']:
                        m.append(tags)
                        try:
                            tag_value_1=str(tag_keys[0])+":"+[key['Value'] for key in m if key['Key'] == tag_keys[0]][0] 
                        except Exception as e:
                            tag_value_1=None
                        try: 
                            tag_value_2=str(tag_keys[1])+":"+[key['Value'] for key in m if key['Key'] == tag_keys[1]][0] 
                        except Exception as e:
                            tag_value_2=None
                        try:
                            tag_value_3=str(tag_keys[2])+":"+[key['Value'] for key in m if key['Key'] == tag_keys[2]][0] 
                        except Exception as e:
                            tag_value_3=None
                        try:
                            tag_value_4=str(tag_keys[3])+":"+[key['Value'] for key in m if key['Key'] == tag_keys[3]][0]
                        except Exception as e:
                            tag_value_4=None
                print(tag_value_1,tag_value_2,tag_value_3,tag_value_4,AutoScalingGroupName)
                str1 = "    " 
                #converting list to string before inserting into database
                InstanceId=str1.join(InstanceId)  
                HealthStatus=str1.join(HealthStatus)
                df_new_rows = pd.DataFrame({
                            'auto_scaling_group_arn':[AutoScalingGroupARN],
                                        'auto_scaling_group_name' : [AutoScalingGroupName],
                                        'desired_capacity' : [DesiredCapacity],
                                        'minimum_capacity' : [MinSize],
                                        'maximum_capacity' : [MaxSize],
                                        'launch_configuration' : [LaunchConfigurationName],
                                        'launch_template':[LaunchTemplateName],
                                        'instance_ids' : [str(InstanceId)],
                                        'health_status':[str(HealthStatus)],
                                        'policy_name':[PolicyName],
                                        'policy_type':[PolicyType],
                                        'policy_enabled':[Enabled],
                                        'policy_metrics_type':[PredefinedMetricType],
                                        'policy_metrics_target_value':[TargetValue],
                                        'health_check_grace_period' : [HealthCheckGracePeriod],
                                        # # 'HealthCheckType' : HealthCheckType,
                                        # # 'EstimatedInstanceWarmup':EstimatedInstanceWarmup,
                                        "instance_type":[instance_type],
                                        'os':[os],
                                        'hourly_price':[str(float(0.023))],
                                        'tag_value_1' : [tag_value_1],
                                        'tag_value_2' : [tag_value_2],
                                        'tag_value_3' : [tag_value_3],
                                        'tag_value_4' : [tag_value_4],
                                        'loadbalancer_name':[LoadBalancerNames],
                                        'account_name':[account_name],
                                        "account_id":[acc_id],
                                        "region":[region],
                            })
                data_from_aws = pd.concat([data_from_aws, df_new_rows])
                data_from_aws['minimum_capacity'] = data_from_aws['minimum_capacity'].astype('int')
                data_from_aws['maximum_capacity'] = data_from_aws['maximum_capacity'].astype('int')
                data_from_aws['desired_capacity'] = data_from_aws['desired_capacity'].astype('int')
                data_from_aws['health_check_grace_period'] = data_from_aws['health_check_grace_period'].astype('int')
                data_from_aws['policy_metrics_target_value'] = data_from_aws['policy_metrics_target_value'].astype('int')
        except Exception as e:
            print(region)
            print("----")
            print(e)

    # print(data_from_aws)
    if data_from_aws.empty:
        remove_records("ss.auto_scaling_groups","account_name",account_name)
    else:
        output=pass_to_db("ss.auto_scaling_groups",data_from_aws,"account_name",ignore_columns)
        print(output + " for " + str(account_name)) 
print("%s seconds ====>" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")
