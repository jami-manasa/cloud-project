# import sys,os
# sys.path.insert(1,os.path.abspath(__file__).split('source')[0]+'source/api')
# from imports import *
from api.pdbc_api  import *
from api.aws_api import *
import time
from datetime import date
import calendar
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))
connection = db_connection("ss")
#getting requried data from database if and only if current time matches database time
def get_dbdata_with_columns(database_with_schema,wanted_columns,sys_time):  
    col = ','.join([str(elem) for elem in wanted_columns])
    sys_time=[sys_time]
    try:
        database=database_with_schema.split('.')
        #database connection
        connection=db_connection(database[0]) 
        cursor = connection.cursor()
         #getting  only data which is equal to current time
        query = " select {0} FROM {1} where {2} = '{3}'   and enable_schedules='true';".format(col,database[1],wanted_columns[4],sys_time[0])   
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        # print(data_from_database)
        if data_from_database.empty:
            # print(sys_time)
            print('No instance is ready to stop')

        else:
            print("Some intances are ready to stop.")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns")  
#stoping ec2 instance if current time equals to database time using aws  stop_instances method        
def stop_ec2(i,connection,data_from_database):  
            ins_id=list(data_from_database['instance_id'])
            account_id=list(data_from_database["account_id"])
            regions=list(data_from_database["region"])
            instance_tag_name=list(data_from_database["instance_tag_name"])
            id=ins_id[i]
            acc_id=account_id[i]
            region=regions[i]
            instance_tag_name=instance_tag_name[i]
            reg_keys=get_awsaccount_details(acc_id,connection)
            assume_role=reg_keys['assume_role'][0]
             # creation ec2 client 
            ec2 = create_client(acc_id, region, assume_role, 'ec2') 
            try:
                response = ec2.stop_instances(InstanceIds=[id], DryRun=False)
                return(instance_tag_name+" is "+response['StoppingInstances'][0]['CurrentState']['Name']+".")
            except ClientError as e:
                print('Error', e)        


my_date = date.today()
#present day
day=calendar.day_name[my_date.weekday()] 
now = datetime.now()
h=str(now.hour)
m=str(now.minute)
if len(m)==1:
    m="0"+m
if len(h)==1:
    h="0"+h
 #current sys time
sys_time= h+":"+m  
wanted_columns=["account_id","region","instance_id","instance_tag_name"]
#getting column name based on which day script running  
days_count = {
    'Monday':{'time':'mon_stp_time'},
    'Tuesday':{'time':'tue_stp_time'},
    'Wednesday':{'time':'wed_stp_time'},   
    'Thursday': {'time':'thu_stp_time'},
    'Friday':{'time':'fri_stp_time'},
    'Saturday':{'time':'sat_stp_time'},
    'Sunday':{'time':'sun_stp_time'}
}
for key in list(days_count.keys()):
    if(key == day):
        columns = days_count[key]
time_column = columns['time']
def get_time_count_list(time_column):
    wanted_columns.append(time_column)
    #data from database
    data_from_database=get_dbdata_with_columns("ss.ec2_instances_schedules",wanted_columns,sys_time) 
    t1=list(data_from_database[time_column])
    for i in range(len(t1)):
         #passing data to aws console to update
        p=stop_ec2(i,connection,data_from_database) 
        print(p)
# getting time column based on script running time to pass aws console fpr update
get_time_count_list(time_column)  

print("%s seconds ====>" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")
