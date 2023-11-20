# import sys,os
# sys.path.insert(1,os.path.abspath(__file__).split('source')[0]+'source/api')
# from imports import *
from api.pdbc_api  import *
from api.aws_api import *
import time
from threading import Thread
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))

connection = db_connection("ss")
cursor = connection.cursor()
def stop_rds(rds,id): 
    try:
        print("DBInstance Id :",id)
        # rds stop 
        response = rds.stop_db_instance(DBInstanceIdentifier=id) 
        print('RDS instance Stopping  Successfully .')
        print(id+" is "+ "Stopped" +".")    
    except ClientError as e:
        print(e,"-------")
  

def get_db_data(database_with_schema,wanted_columns):
    col = ','.join([str(elem) for elem in wanted_columns])
    try:
        database=database_with_schema.split('.')
        cursor = connection.cursor()
        # sql query for getting  only data which is equal to current time
        query = " select {0} FROM {1} WHERE auto_stop_enable='{2}' AND db_state= '{3}' ;".format(col,database[1],str('true'),str('available')) 
        try:
            cursor.execute(query)
        except Exception as e:
            print(e)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        if data_from_database.empty:
            print('No db data avaliable')
        else:
            print("Some db data is there.")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns")  





def get_ec2_info(ins_id,account_id,region):
    reg_keys=get_awsaccount_details(account_id,connection)
    assume_role=reg_keys['assume_role'][0]
    ec2 = create_client(account_id, region, assume_role, 'ec2')
    response = ec2.describe_instances(InstanceIds=[ins_id,],)
    status=response["Reservations"][0]['Instances'][0]['State']['Name']
    return status
def get_statefull_ins_data(database_with_schema,statefull_set_arn): 
    wanted_columns=["account_id","region","instance_id","instance_tag_name","account_name","is_statefull_set","statefull_set_name","statefull_set_arn"]
    col = ','.join([str(elem) for elem in wanted_columns])
    try:
        database=database_with_schema.split('.')
        connection=db_connection(database[0])
        cursor = connection.cursor()
        try:
            query = " select {0} FROM {1} where statefull_set_arn = '{2}';".format(col,database[1],statefull_set_arn)   
        except Exception as e:
            print(e)
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        if data_from_database.empty:
            print("empty rds dataframe")
        else:
            print("")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns")
def get_metrideatails(data_from_database):
    records=data_from_database
    c=0
    for i in range(len(records)):
        db_id=list(records['db_identifier'])[i]
        acc_id=list(records['account_id'])[i]
        region=list(records['region'])[i]
        reg_keys=get_awsaccount_details(acc_id,connection)
        assume_role=reg_keys['assume_role'][0]
        
        try:
            cloudwatch_client = create_client(acc_id,region,assume_role,'cloudwatch')
            start_time = datetime.utcnow() - timedelta(hours=2,minutes=5)
            endtime = datetime.utcnow() - timedelta(minutes=5)
            response = cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=60,
                                        Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime=start_time,EndTime=endtime, Statistics=['Sum'])

            maximum  = jmespath.search("Datapoints[*].[Sum]",response)     
            if len(maximum)==120:
                print(max(maximum)[0])
                if (max(maximum)[0]) < 6:  
                    c=c+1
                else:
                    print("Not Required for Stopping")
            else:
                print("Already Stopped/ db not available")
            
        except Exception as e:
            print(e)
            print("Failed to Execute")
    if c==len(records):
        return True
    else:
        return False
def statefull_auto_stop(statefull):
    print("____________________________________statefull_______________________")
    if not statefull.empty:
        statefull_set_arn=statefull['statefull_set_arn'].unique()
        for j in range(len(statefull_set_arn)):
            each_statefull_sets=statefull[statefull["statefull_set_arn"] == statefull_set_arn[j]]
            data_from_ec2=get_statefull_ins_data("ss.ec2_instances_schedules",statefull_set_arn[j]) 
            count=0
            for i in range(len(data_from_ec2)):
                ins_id=list(data_from_ec2['instance_id'])[i]
                account_id=list(data_from_ec2["account_id"])[i]
                region=list(data_from_ec2["region"])[i]
                ec2_status=get_ec2_info(ins_id,account_id,region)
                if ec2_status=="stopped" or ec2_status=="stopping":
                    count=count+1
            print(count,"==",data_from_ec2.shape[0])
            if get_metrideatails(each_statefull_sets):
                if count==data_from_ec2.shape[0]:
               
                    for i in each_statefull_sets.index:
                        reg_keys=get_awsaccount_details(str(each_statefull_sets['account_id'][i]),connection)
                        assume_role=reg_keys['assume_role'][0]
                        rds = create_client(each_statefull_sets['account_id'][i],each_statefull_sets['region'][i],assume_role, 'rds')
                        stop_rds(rds,each_statefull_sets["db_identifier"][i])
                

                else:
                    print("for rds autostop each and every instance belongs this statefulls sets  must be in stopped state. ")

            else:
                print("autostop for rds Not required")
    else:
        print("No statefull sets required rds autostop.")




def non_statefull_auto_stop(non_statefull):
    records=non_statefull
    for i in range(len(records)):
        db_id=list(records['db_identifier'])[i]
        acc_id=list(records['account_id'])[i]
        region=list(records['region'])[i]
        reg_keys=get_awsaccount_details(acc_id,connection)
        assume_role=reg_keys['assume_role'][0]
        try:
            cloudwatch_client = create_client(acc_id,region,assume_role,'cloudwatch')
            start_time = datetime.utcnow() - timedelta(hours=2,minutes=5)
            endtime = datetime.utcnow() - timedelta(minutes=5)
            response = cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=60,
                                        Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime=start_time,EndTime=endtime, Statistics=['Sum'])
            maximum  = jmespath.search("Datapoints[*].[Sum]",response)    
            if len(maximum)==120:
                print(max(maximum)[0])
                if (max(maximum)[0]) < 6:  
                    rds = create_client(records['account_id'][i],records['region'][i],assume_role, 'rds')
                    stop_rds(rds,records["db_identifier"][i])
                    print("here it is")
                else:
                    print("Not Required for Stopping")
            else:
                print("Already Stopped/ db not available")
            
        except Exception as e:
            print(e)
            print("Failed to Execute")

wanted_columns=["account_id","region",'db_identifier',"is_statefull_set","statefull_set_name","statefull_set_arn"]
data_from_database=get_db_data("ss.rds_databases_schedules",wanted_columns) 
if data_from_database.empty:
        print("auto_stop state is false for aws rds's")
else:
    statefull = data_from_database[data_from_database['is_statefull_set'] == 'true'] 
    non_statefull = data_from_database[data_from_database['is_statefull_set'] != 'true'] 
    if not statefull.empty:
        t1=Thread(target = statefull_auto_stop(statefull))
        t1.start()
    if not non_statefull.empty:
        t2=Thread(target = non_statefull_auto_stop(non_statefull))
        t2.start()































print("%s seconds ====>" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")




    
