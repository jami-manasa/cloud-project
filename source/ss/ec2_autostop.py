# import sys,os
# sys.path.insert(1,os.path.abspath(__file__).split('source')[0]+'source/api')
# from imports import *
from datetime import datetime
from api.pdbc_api  import *
from api.aws_api import *
import datetime as dt
from threading import Thread
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))

connection = db_connection("ss")
cursor = connection.cursor()
def stop_instances(ec2,id,connection):
    try:
        print("instance id :",id)
        response = ec2.stop_instances(InstanceIds=[id], DryRun=False)
        # print('Instance Stopping  Successfully .')
        query = "select instance_tag_name from  ss.ec2_instances_schedules WHERE instance_id = '{}' ".format(id)
        id_name=pd.read_sql(query,connection)
        print(id_name['instance_tag_name'][0]+" is "+response['StoppingInstances'][0]['CurrentState']['Name']+".")

    except ClientError as e:
        print('Error', e)

       
def get_dbdata_with_columns(database_with_schema,wanted_columns):
    col = ','.join([str(elem) for elem in wanted_columns])
    try:
        database=database_with_schema.split('.')
        cursor = connection.cursor()
        query = " select {0} FROM {1} WHERE auto_stop_enable='{2}' AND instance_state= '{3}' ;".format(col,database[1],str('true'),str('running')) 
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        if data_from_database.empty:
            print('No instance is ready for auto auto stop')
        else:
            print("Some intances  are ready for auto auto stop.")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns") 

def  get_max_cpu_utlz(data_from_database):
    try:
        records=data_from_database
        print(data_from_database)
        max_cpu_utlz_fr_each_in=[]
        for i in range(len(records)):
            acc_id=list(records['account_id'])[i]
            region=list(records['region'])[i]
            reg_keys=get_awsaccount_details(acc_id,connection)
            acc_name=list(records['account_name'])[i]
            ins_id=list(records["instance_id"])[i]
            assume_role=reg_keys['assume_role'][0]
            launch_time=list(records['recent_launch_time'])[i]
            k=launch_time.replace("+00:00","")
            date_time_obj = dt.datetime.strptime(k, '%Y-%m-%d %H:%M:%S')
            diff= (datetime.utcnow() - timedelta(minutes=10))-date_time_obj
            sec = diff.total_seconds()
            ins_id=list(records["instance_id"])[i]
            cloudwatch_client = create_client(acc_id,region,assume_role,'cloudwatch')
            start_time = datetime.utcnow() - timedelta(hours=2,minutes=5)
            endTime = datetime.utcnow() - timedelta(minutes=5)
            response = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=7200,
                                                        Dimensions=[{
                                                            'Name': 'InstanceId','Value':ins_id},],
                                                        StartTime=start_time,
                                                        EndTime=endTime,
                                                        Statistics=['Maximum'])                                      
            maximum  = jmespath.search("Datapoints[*].[Maximum]",response)
            if sec > 7200:
                if (max(maximum)[0]) < 6: 
                    ec2 = create_client(acc_id,region,assume_role, 'ec2')
                    print("Needs To Stop In account, region:",acc_name, region,ins_id)
                    stop_instances(ec2,ins_id,connection)
                else:
                    print("No Need To autoStop ,bcz cpu utilization is more than 6.") 
            else:
                print("Instance started recently, so no need to auto stop.")
            
    except Exception as e:
        print(e)
    if len(max_cpu_utlz_fr_each_in) != data_from_database.shape[0]:
        return False
    else:
        return True


def statefull_auto_stop(statefull):
    if get_max_cpu_utlz(statefull):
        for i in statefull.index:
            acc_id=list(statefull['account_id'])[i]
            region=list(statefull['region'])[i]
            reg_keys=get_awsaccount_details(acc_id,connection)
            ins_id=list(statefull["instance_id"])[i]
            assume_role=reg_keys['assume_role'][0]
            ec2 = create_client(acc_id,region,assume_role, 'ec2')
            print(stop_instances(ec2,ins_id,connection))
    else:
        print("no need of autosotp for this  statefull set ")

       
def non_statefull_auto_stop(non_statefull):
    records=non_statefull
    try:
        for i in range(len(records)):
            acc_id=list(records['account_id'])[i]
            acc_name=list(records['account_name'])[i]
            region=list(records['region'])[i]
            reg_keys=get_awsaccount_details(acc_id,connection)
            assume_role=reg_keys['assume_role'][0]
            launch_time=list(records['recent_launch_time'])[i]
            k=launch_time.replace("+00:00","")
            date_time_obj = dt.datetime.strptime(k, '%Y-%m-%d %H:%M:%S')
            diff= (datetime.utcnow() - timedelta(minutes=10))-date_time_obj
            sec = diff.total_seconds()
            ins_id=list(records["instance_id"])[i]
            cloudwatch_client = create_client(acc_id,region,assume_role,'cloudwatch')
            start_time = datetime.utcnow() - timedelta(hours=2,minutes=5)
            endTime = datetime.utcnow() - timedelta(minutes=5)
            response = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=7200,
                                                        Dimensions=[{
                                                            'Name': 'InstanceId','Value':ins_id},],
                                                        StartTime=start_time,
                                                        EndTime=endTime,
                                                        Statistics=['Maximum'])                                      
            maximum  = jmespath.search("Datapoints[*].[Maximum]",response)
            # print(max(maximum)[0],"---",ins_id,sec)
            if sec > 7200:
                if (max(maximum)[0]) < 6: 
                    ec2 = create_client(acc_id,region,assume_role, 'ec2')
                    print("Needs To Stop In account, region:",acc_name, region,ins_id)
                    stop_instances(ec2,ins_id,connection)
                else:
                    print("No Need To autoStop ,bcz cpu utilization is more than 6.") 
            else:
                print("Instance started recently, so no need to auto stop.")
            
    except Exception as e:
        print(e)
    
wanted_columns=["account_id","region","instance_id","instance_tag_name","account_name","instance_state","auto_stop_enable","recent_launch_time" ]
print("hhihihi manasa dont worry")
try:
    print("om...............................................>")
    data_from_database=get_dbdata_with_columns("ss.ec2_instances_schedules",wanted_columns) 
except Exception as e:
        print(e,"hihihihhihihihh")
print(data_from_database)
print("--------------------------------------------------------------------------.>")
if data_from_database:
    statefull=data_from_database[data_from_database.is_statefull_set == 'true']
    non_statefull =data_from_database[data_from_database.is_statefull_set != 'true']
    if not statefull.empty:
        t1=Thread(target = statefull_auto_stop(statefull))
        t1.start()
    if not non_statefull.empty:
        t2=Thread(target = non_statefull_auto_stop(non_statefull))
        t2.start() 
        
else:
    print("auto_stop state is false for aws instances's")
    



print("%s seconds ====>" % (time.time() - start_time),"time taken by script")

print("-----------------------------------------------END---------------------------------------------------")
print("script_end")
