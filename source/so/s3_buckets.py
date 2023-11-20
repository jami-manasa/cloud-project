from api.pdbc_api  import *
from api.aws_api import *
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))
def get_price():
    pass
def get_lifecycle(s3_client,bucket_name):
    try:
        lifecycle = s3_client.get_bucket_lifecycle(Bucket=bucket_name)
        rules = lifecycle['Rules']
        for i in rules['Rules']:
            return(i['Status'])   
    except:
        rules = 'No Policy' 
        return(rules)
def get_object(s3_client,bucket_name):
    response = s3_client.list_objects( Bucket=bucket_name,    )
    return response

def get_size(cloudwatch_client,bucket_name,pe,st,en,v):    
    u = datetime.utcnow()
    u = u.replace(tzinfo=pytz.utc)
    response = cloudwatch_client.get_metric_statistics(
    Namespace = 'AWS/S3',
    MetricName = 'BucketSizeBytes',
    Period=pe,
    Dimensions= [
                {   "Name": "StorageType",
                    "Value": "StandardStorage"
                },
                {  "Name": "BucketName",
                    "Value": bucket_name
                }],
        StartTime=u-timedelta(hours=st),
            EndTime=u-timedelta(hours=en),Statistics=['Average']
            )
    result  = jmespath.search("Datapoints[*].Average",response)
    if v == 'T':
        if len(result)>0:
            return(result[0],result[-1])
        else:
            return (0,0)

    else:
        if len(result)>0:
            return(sum(result))
        else:
            return(0)

def get_object_count(cloudwatch_client,bucket_name,pe,st,en,v):
    
    u = datetime.utcnow()
    u = u.replace(tzinfo=pytz.utc)
    response = cloudwatch_client.get_metric_statistics(
    Namespace = 'AWS/S3',
    MetricName = 'NumberOfObjects',
    Period=pe,
    Dimensions= [
                {
                    "Name": "StorageType",
                    "Value": "AllStorageTypes"
                },
                {
                    "Name": "BucketName",
                    "Value": bucket_name
                }  ],
        StartTime=u-timedelta(hours=st),
            EndTime=u-timedelta(hours=en),Statistics=['Average']
            )
    result  = jmespath.search("Datapoints[*].Average",response)
 
    if v == 'T':
        if len(result)>0:
            return(result[0],result[-1])
        else:
            return (0,0)

    else:
        if len(result)>0:
            return(sum(result))
        else:
            return(0)

def get_value(acc_id,connection):
    query = "SELECT assume_role,regions,account_name,tag_key_1,tag_key_2,tag_key_3,tag_key_4 FROM ad.aws_accounts WHERE account_id = '{}' ".format(acc_id)
    data = pd.read_sql(query,connection)
    return(data)

connection = db_connection("so")
account_id = []
regions=[]
region='us-east-1'
try:
    cursor = connection.cursor()
    query_acc_id  = "SELECT account_id FROM ad.aws_accounts"
    cursor.execute(query_acc_id)
    records = cursor.fetchall()
    for i in records:
        account_id.append(i[0])
    cursor.close()
except Exception as e:
    print(e)
    print("Account_Id Can't Be Fetched")
diff_price = {'STANDARD':0.023,'GLACIER':0.004,'STANDARD_IA':0.00099 ,'ONEZONE_IA':0.0125,'INTELLIGENT_TIERING':0.0025,'DEEP_ARCHIVE':0.0036,'GLACIER_IR':0.01 }
columns = get_columns("so.s3_buckets")
ignore_columns = ['standard_storage_size','standardia_storage_size','glacier_storage_size','ignore']

for acc_id in account_id:
    data_from_aws = pd.DataFrame(columns=columns) 
    details_from_ad = get_value(acc_id,connection)
    account_details=get_awsaccount_details(acc_id,connection)
    account_name=account_details['account_name'][0]
    tag_keys = account_details['tag_keys']
    assume_role=account_details['assume_role'][0]
    s3_client=create_client(acc_id,region,assume_role,'s3')
    cloudwatch_client = create_client(acc_id,region,assume_role,'cloudwatch')
    response = s3_client.list_buckets()
    for bucket in response['Buckets']:
        get_lifecycle_response = get_lifecycle(s3_client,bucket['Name'])
        get_object_response = get_object(s3_client,bucket['Name'])
        get_size_response = get_size(cloudwatch_client,bucket['Name'],3600,336,0,"T")
        get_object_count_response = get_object_count(cloudwatch_client,bucket['Name'],3600,336,0,"T")
        get_object_count_avg1 = get_object_count(cloudwatch_client,bucket['Name'],3600,336,0,"F")
        get_object_count_avg2 = get_object_count(cloudwatch_client,bucket['Name'],3600,48,0,"F")
        get_size_avg3 = get_size(cloudwatch_client,bucket['Name'],86400,336,312,"F")/1024/1024/1024 
        get_size_avg4 = get_size(cloudwatch_client,bucket['Name'],86400,48,24,"F")/1024/1024/1024 
        if get_object_count_avg1 == get_object_count_avg2:
            if get_size_avg3 == get_size_avg4:
                r = s3_client.list_objects(Bucket=bucket['Name'],)
                hourly_price = 0
                for i in r:
                    if i == "Contents":
                        hourly_price = 0
                        for j in r[i]:
                            in_kbs = round(j['Size']/(1024),8)
                            in_gbs = round(j['Size']/(1024 * 1024 * 1024),8)
                            if j['StorageClass'] == "STANDARD" or j['StorageClass']== 'INTELLIGENT_TIERING':
                                if in_kbs > 128 and in_gbs < 50:
                                    # print(in_gbs)
                                    # print(j['StorageClass'])
                                    # print(j['Key'])
                                    price = diff_price[j['StorageClass']]
                                    hourly_price = hourly_price + price
                                    pass
                                else:
                                    price = 0
                                    hourly_price = hourly_price + price 
                                    pass
                            else:
                                hourly_price = diff_price[j['StorageClass']]

                if hourly_price == 0:
                    pass
                else:
                    try:
                        response_tags = s3_client.get_bucket_tagging(Bucket=bucket['Name'])
                        k= 'TagSet'
                        if k in response_tags.keys():
                            try:
                                tag_value_1 =str(tag_keys[0])+":"+[key['Value'] for key in response_tags['TagSet'] if key['Key'] == tag_keys[0]][0]
                            except Exception as e:
                                tag_value_1=None
                            try:
                                tag_value_2 =str(tag_keys[1])+":"+[key['Value'] for key in response_tags['TagSet'] if key['Key'] == tag_keys[1]][0]
                            except Exception as e:
                                tag_value_2=None 
                            try:
                                tag_value_3 =str(tag_keys[2])+":"+[key['Value'] for key in response_tags['TagSet'] if key['Key'] == tag_keys[2]][0]
                            except Exception as e:
                                    tag_value_3=None 
                            try:
                                tag_value_4  = str(tag_keys[3])+":"+[key['Value'] for key in response_tags['TagSet'] if key['Key'] == tag_keys[3]][0]        
                            except Exception as e:
                                tag_value_4=None  
                        else:
                            tag_value_1=None
                            tag_value_2=None
                            tag_value_3=None
                            tag_value_4=None
                    except Exception as e:
                        tag_value_1=None
                        tag_value_2=None
                        tag_value_3=None
                        tag_value_4=None
                        # print(e)
                    billing = get_size_avg4/100*2.18
                    df_new_rows = pd.DataFrame({
                        'bucket_name': [bucket['Name']],
                        'account_id': [acc_id],
                        'account_name': [account_name],
                        'tag_value_1':[tag_value_1],
                        'tag_value_2':[tag_value_2],
                        'tag_value_3':[tag_value_3],
                        'tag_value_4':[tag_value_4],
                        'created_on': [bucket['CreationDate']],
                        'life_cycle_enabled': [get_lifecycle_response],
                        'data_size_2weeksago':[ get_size_response[0]],
                        'data_size_now': [get_size_response[-1]],
                        'objects_count_2weeksago': [int(get_object_count_response[0])],
                        'objects_count_now':[int(get_object_count_response[-1])],
                        'unused_hours':[336],
                        'hourly_price':[hourly_price],
                        'total_waste_spent': [hourly_price*336],
                        'recent_scan_time': [datetime.now()],
                        })
                    data_from_aws = pd.concat([data_from_aws, df_new_rows])
    if data_from_aws.empty:
        remove_records("so.s3_buckets","account_name",account_name)
    else:
        output=pass_to_db("so.s3_buckets",data_from_aws,"account_name",ignore_columns)
        print(output + " for " + str(account_name))   
print("----------------------- %s seconds ----------------------" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")



