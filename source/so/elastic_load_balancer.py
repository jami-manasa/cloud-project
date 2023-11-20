from api.pdbc_api  import *
from api.aws_api import *
from api.aws_api import platform as pt
start_time = time.time()
print("--------------------------------------------- datetime:{} -------------------------------------".format(datetime.now()))
def get_price(pricing_client,region_name):
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[ {"Type": "TERM_MATCH", "Field": "productFamily","Value": "Load Balancer"},
                    {"Type": "TERM_MATCH", "Field": "location","Value": region_name},],FormatVersion='aws_v1',)#MaxResults=1
    pri=[]
    for i in range(2):
        od = json.loads(response['PriceList'][i])['terms']['OnDemand']
        id1 = list(od)[0]
        id2 = list(od[id1]['priceDimensions'])[0] #per gb price 
        pri.append(od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']) #per hour price
    return (pri)
def get_cpu_response(cloudwatch_client,lb_main,tg_main):
    ut = {}
    u = datetime.utcnow()
    u = u.replace(tzinfo=pytz.utc)
    response = cloudwatch_client.get_metric_statistics(Namespace = 'AWS/ApplicationELB',MetricName = 'RequestCount',Period=3600,
    Dimensions= [{"Name": "TargetGroup","Value": "{}".format(tg_main)},
                {"Name": "LoadBalancer","Value": "{}".format(lb_main)}],StartTime=u-timedelta(hours=336),EndTime=u,Statistics=['Sum'] )
    response1 = cloudwatch_client.get_metric_statistics(Namespace = 'AWS/ApplicationELB',MetricName = 'ConsumedLCUs',Period=3600,
    Dimensions= [{"Name": "LoadBalancer","Value": "{}".format(lb_main) }],StartTime=u-timedelta(hours=3),EndTime=u,Statistics=['Sum'])
    result1  = jmespath.search("Datapoints[*].Sum",response1)
    result  = jmespath.search("Datapoints[*].Sum",response)
    if len(result1)>0:
        ut['lcu'] = max(result1)
    else:
        ut['lcu'] = 0
    if len(result)>0:
        ut['responseCount'] = int(max(result))
    else:
        ut['responseCount'] = 0
    return(ut)
def get_value(acc_id,connection):
    query = "SELECT assume_role,regions,account_name,tag_key_1,tag_key_2,tag_key_3,tag_key_4 FROM ad.aws_accounts WHERE account_id = '{}' ".format(acc_id)
    data = pd.read_sql(query,connection)
    return(data)
account_ids=[]
connection = db_connection("so")
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
columns=get_columns("so.elastic_load_balancers")
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
            ssm_client =create_client(account_id, region, assume_role, 'ssm') 
            tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region
            ssm_response = ssm_client.get_parameter(Name = tmp)
            region_name = ssm_response['Parameter']['Value']
            ssm_client = create_client(account_id,region,assume_role,'ssm')
            tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region
            ssm_response = ssm_client.get_parameter(Name = tmp)
            region_name = ssm_response['Parameter']['Value']
            elb_client = create_client(account_id,region,assume_role,'elbv2')
            cloudwatch_client = create_client(account_id,region,assume_role,'cloudwatch')
            response = elb_client.describe_load_balancers()
            for lb in response['LoadBalancers']:
                if len(lb)> 0:
                    lb_name = lb['LoadBalancerName'] 
                    status = lb['State']['Code']
                    elb_type = lb['Type']
                    lb_arn = lb['LoadBalancerArn']
                    lb_main = lb_arn.split('loadbalancer/')
                    response1 = elb_client.describe_target_groups(LoadBalancerArn ='{}'.format(lb_arn))
                    response3 = elb_client.describe_tags(ResourceArns  =['{}'.format(lb_arn)])
                    tag_list =response3['TagDescriptions'][0]['Tags']
                    try:
                        tag_value_1=str(tag_keys[0])+" : "+[key['Value'] for key in tag_list if key['Key'] == tag_keys[0]][0]
                    except Exception as e:
                        tag_value_1=None
                    try:
                        tag_value_2=str(tag_keys[1])+" : "+[key['Value'] for key in tag_list if key['Key'] == tag_keys[1]][0]
                    except Exception as e:
                        tag_value_2=None
                    try:
                        tag_value_3=str(tag_keys[2])+" : "+[key['Value'] for key in tag_list if key['Key'] == tag_keys[2]][0]
                    except Exception as e:
                        tag_value_3=None
                    try:
                        tag_value_4=str(tag_keys[3])+" : "+[key['Value'] for key in tag_list if key['Key'] == tag_keys[3]][0]
                    except Exception as e:
                        tag_value_4=None
                    for tg in response1['TargetGroups']:
                        tg_name = tg['TargetGroupName']
                        tg_arn = tg['TargetGroupArn']
                        tg_main = tg_arn.split(':')
                        cloudwatch_response = get_cpu_response(cloudwatch_client,lb_main[-1],tg_main[-1])
                        response2 = elb_client.describe_target_health(TargetGroupArn='{}'.format(tg_arn))
                        inst_present = jmespath.search("TargetHealthDescriptions[*].Target.Id",response2)
                        inst_present = str(inst_present)[1:-1]
                        inst_present_x = inst_present.replace(",", " ")
                        # response_count_list.append(cloudwatch_response['responseCount']) #13
                        if cloudwatch_response['responseCount'] == 0 :
                            pricing_client = create_client(account_id,region,assume_role,'pricing') # pricing client
                            pricing_response = get_price(pricing_client,region_name)
                            # hourly_price_list.append(pricing_response[1]) #14
                            # lcu_hourly_price_list.append(pricing_response[0])
                            df_new_rows = pd.DataFrame({
                                # 'loadbalancer_name':lb_arn,
                                'loadbalancer_name' : [lb_name],
                                'account_name' : [account_name],
                                'account_id' : [account_id],
                                'region': [region],
                                'elb_type' : [elb_type],
                                'status': [status],
                                'target_group_name': [tg_name],
                                'attached_ec2_instances': [inst_present_x],
                                'tag_value_1': [tag_value_1],
                                'tag_value_2':[tag_value_2],
                                'tag_value_3': [tag_value_3],
                                'tag_value_4':[tag_value_4],
                                'unused_hours':[336],
                                'total_waste_spent':[pricing_response[1]*336],
                                'recent_scan_time' :  [datetime.now()],
                                'hourly_price': [pricing_response[1]]
                                })
                            data_from_aws = pd.concat([data_from_aws, df_new_rows])
        except Exception as e:
            print(region)
            print("----")
            print(e)
    if data_from_aws.empty:
        remove_records("so.elastic_load_balancers","account_name",account_name)
    else:
        output=pass_to_db("so.elastic_load_balancers",data_from_aws,"account_name",ignore_columns)
        print(output + " for " + str(account_name))  
print("----------------------- %s seconds ----------------------" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")    

# expression="TagDescriptions[0].[[Tags[?Key== '{}'].Value] [0][0] ,[Tags[?Key== '{}'].Value] [0][0] ,[Tags[?Key== '{}'].Value] [0][0],[Tags[?Key== '{}'].Value] [0][0]]".format(details_from_ad['tag_key_1'][0],details_from_ad['tag_key_2'][0],details_from_ad['tag_key_3'][0],details_from_ad['tag_key_4'][0])
                # data=jmespath.search(expression,response3)