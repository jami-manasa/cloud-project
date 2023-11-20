# import sys,os
# sys.path.insert(1,os.path.abspath(__file__).split('source')[0]+'source/api')
# from imports import *
from api.pdbc_api  import *
from api.aws_api import *
import time
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))
account_ids=[]
connection = db_connection("ss")
try:
    cursor = connection.cursor()
    Query = "SELECT account_id from ad.aws_accounts;"
    cursor.execute(Query)
    print("fetching account_ids")
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

 #getting requried data from database if and only if current time matches database time
def get_hourly_price(region_code, pricing_client, db_instance_type, db_engine):  
        db_engine_edition =[
                {"scanned_db_engine":'aurora-mysql','actual_db_engine':'Aurora MySQL','db_edition':None},
                {"scanned_db_engine":'aurora-postgresql','actual_db_engine':'Aurora PostgreSQL','db_edition':None},
                {"scanned_db_engine":'mariadb','actual_db_engine':'MariaDB','db_edition':None},
                {"scanned_db_engine":'mysql','actual_db_engine':'MySQL','db_edition':None},
                {"scanned_db_engine":'oracle-ee','actual_db_engine':'Oracle','db_edition':'Enterprise'},
                {"scanned_db_engine":'oracle-se2','actual_db_engine':'Oracle','db_edition':'Standard Two'},
                {"scanned_db_engine":'postgres','actual_db_engine':'PostgreSQL','db_edition':None},
                {"scanned_db_engine":'sqlserver-ee','actual_db_engine':'SQL Server','db_edition':'Enterprise'},
                {"scanned_db_engine":'sqlserver-ex','actual_db_engine':'SQL Server','db_edition':'Express'},
                {"scanned_db_engine":'sqlserver-se','actual_db_engine':'SQL Server','db_edition':'Standard'},
                {"scanned_db_engine":'sqlserver-web','actual_db_engine':'SQL Server','db_edition':'Web'},
        ]
        for dic in db_engine_edition:
                if dic['scanned_db_engine'] == db_engine:
                       
                        engine = dic['actual_db_engine']
                        edition = dic['db_edition']
                        break
                else:
                        engine = None
                        edition = None
        if edition and engine is not None:
                try:
                        pricing_response = pricing_client.get_products(
                                ServiceCode='AmazonRDS',
                                Filters=[
                                {
                                        'Type': 'TERM_MATCH',
                                        'Field': 'instanceType',
                                        'Value': db_instance_type
                                },
                                {
                                        'Type': 'TERM_MATCH',
                                        'Field': 'databaseEngine',
                                        'Value': engine
                                },
                                {
                                        'Type': 'TERM_MATCH',
                                        'Field': 'databaseEdition',
                                        'Value': edition
                                },
                                
                                {
                                        'Type': 'TERM_MATCH',
                                        'Field': 'location',
                                        'Value': region_code
                                },
                                ],
                                FormatVersion='aws_v1',
                                MaxResults=1
                        )
                        od = json.loads(pricing_response['PriceList'][0])['terms']['OnDemand']
                        
                        id1 = list(od)[0]
                        id2 = list(od[id1]['priceDimensions'])[0]
                        hourly_price = od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']
                        # print(hourly_price,"-------------------------------",od)
                except Exception as e:
                        print(e)
                        hourly_price = None
        elif edition is None:
                try:
                        pricing_response = pricing_client.get_products(
                                ServiceCode='AmazonRDS',
                                Filters=[
                                {
                                        'Type': 'TERM_MATCH',
                                        'Field': 'instanceType',
                                        'Value': db_instance_type
                                },
                                {
                                        'Type': 'TERM_MATCH',
                                        'Field': 'databaseEngine',
                                        'Value': engine
                                },
                                
                                {
                                        'Type': 'TERM_MATCH',
                                        'Field': 'location',
                                        'Value': region_code
                                },
                                ],
                                FormatVersion='aws_v1',
                                MaxResults=1)
                        od = json.loads(pricing_response['PriceList'][0])['terms']['OnDemand']
                        
                        id1 = list(od)[0]
                        id2 = list(od[id1]['priceDimensions'])[0]
                        hourly_price = od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']
                        # print(hourly_price,"-------------------------------",od)
                except Exception as e:
                        print(e)
                        hourly_price = None
        else:
                hourly_price = None
        return hourly_price
columns=get_columns("ss.rds_databases_schedules")
ignore_columns=['rds_group_name','is_statefull_set','statefull_set_name','statefull_set_arn', 'auto_stop_enable','mon_str_time','mon_stp_time','tue_str_time','tue_stp_time','wed_str_time','wed_stp_time','thu_str_time','thu_stp_time','fri_str_time','fri_stp_time','sat_str_time','sat_stp_time','sun_str_time','sun_stp_time','stack_arn']
for account_id in account_ids:
    data_from_aws = pd.DataFrame(columns=columns)
    account_details=get_awsaccount_details(account_id,connection)
    regions=account_details['regions']
    account_name=account_details['account_name'][0]
    tag_keys=account_details['tag_keys']
    assume_role=account_details['assume_role'][0]
    rds_response = {}
    for region in regions:
        try:
                # creating ssm client
                ssm_client = create_client(account_id, region, assume_role, "ssm")
                tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region
                ssm_response = ssm_client.get_parameter(Name = tmp)
                region_name = ssm_response['Parameter']['Value'] 
                #creating price client
                pricing_client = create_client(account_id, 'us-east-1', assume_role, "pricing") 
                rds = create_client(account_id, region, assume_role, "rds")
                #rds details
                response = rds.describe_db_instances() 
                #rds db details
                data=json.dumps(response,default = myconverter) 
                data= json.loads(data)
                #required data from json  
                for db_instance in data['DBInstances']:
                        db_resource_id = db_instance['DbiResourceId']  
                        db_identifier = db_instance['DBInstanceIdentifier']
                        date_created_on = db_instance['InstanceCreateTime']
                        db_instance_type = db_instance['DBInstanceClass']
                        db_engine = db_instance['Engine']
                        db_state = db_instance['DBInstanceStatus']
                        db_storage_type = db_instance['StorageType']
                        db_storage_size = db_instance['AllocatedStorage']
                        tags_list = db_instance['TagList']
                        try:
                                db_tag_name=[key['Value'] for key in tags_list if key['Key'] == 'Name'][0]
                        except Exception as e:
                                db_tag_name=None
                        try:
                                tag_value_1=str(tag_keys[0])+":"+[key['Value'] for key in tags_list if key['Key'] == tag_keys[0]][0]
                        except Exception as e:
                                tag_value_1=None
                        try:
                                tag_value_2=str(tag_keys[1])+":"+[key['Value'] for key in tags_list if key['Key'] == tag_keys[1]][0]
                        except Exception as e:
                                tag_value_2=None
                        try:
                                tag_value_3=str(tag_keys[2])+":"+[key['Value'] for key in tags_list if key['Key'] == tag_keys[2]][0]
                        except Exception as e:
                                tag_value_3=None
                        try:
                                tag_value_4=str(tag_keys[3])+":"+[key['Value'] for key in tags_list if key['Key'] == tag_keys[3]][0]
                        except Exception as e:
                                tag_value_4=None
                        hourly_price = get_hourly_price(region_name, pricing_client, db_instance_type, db_engine)
                        #dataframe : passing data into  database from aws console
                        df_new_rows = pd.DataFrame({
                                'db_resource_id' : [db_resource_id],
                                'db_identifier' : [db_identifier],            
                                "db_tag_name":[db_tag_name],
                                'date_created_on' : [date_created_on],
                                'db_instance_type':[db_instance_type],
                                "db_engine":[db_engine],
                                "db_state":[db_state],
                                "db_storage_type":[db_storage_type] ,
                                "db_storage_size":[db_storage_size],
                                'account_id' : [account_id],
                                'account_name' : [account_name],
                                'region':[region],
                                'tag_value_1' : [tag_value_1],
                                'tag_value_2' : [tag_value_2],
                                'tag_value_3' : [tag_value_3],
                                'tag_value_4' : [tag_value_4],
                                'hourly_price':[hourly_price]
                                })
                        data_from_aws = pd.concat([data_from_aws, df_new_rows])
        except Exception as e:
            print(region)
            print("----")
            print(e)
    if data_from_aws.empty:
        #if cureent  dataframe empty it will delete previous data from database(only based on account name)
        remove_records("ss.rds_databases_schedules","account_name",account_name) 
    else:
            #pass_to_db function for curd operation
        output=pass_to_db("ss.rds_databases_schedules",data_from_aws,"account_name",ignore_columns)    
        print(output + " for " + str(account_name))
print("%s seconds ====>" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")
