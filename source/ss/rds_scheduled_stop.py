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
        connection=db_connection(database[0])
        cursor = connection.cursor()
        query = " select {0} FROM {1} where {2} = '{3}' and enable_schedules='true';".format(col,database[1],wanted_columns[3],sys_time[0])   #getting  only data which is equal to current time
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        if data_from_database.empty:
            print('No rds_db is ready to stop')
        else:
            print("Some rds_db are ready to stop.")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns")  
#rds db ec2 instance if current time equals to database time using aws  stop_db_instance method
def stop_db(i,connection,data_from_database):  
            db_id=list(data_from_database['db_identifier'])
            account_id=list(data_from_database["account_id"])
            regions=list(data_from_database["region"])
            db_id=db_id[i]
            acc_id=account_id[i]
            region=regions[i]
            reg_keys=get_awsaccount_details(acc_id,connection)
            assume_role=reg_keys['assume_role'][0]
            
            rds=create_client(acc_id, region, assume_role, 'rds')
            state = rds.describe_db_instances(DBInstanceIdentifier=db_id,)
            db_status=state['DBInstances'][0]['DBInstanceStatus']
            
            try:
                response = rds.stop_db_instance(DBInstanceIdentifier=db_id)
                # print(response,'----------------------------------------------------------------------------------------------')
                return(db_id+'is'+response['DBInstance']['DBInstanceStatus'])
            except ClientError as e:
                print('Error', e)        
my_date = date.today()
#todays day
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
wanted_columns=["account_id","region",'db_identifier']
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
    data_from_database=get_dbdata_with_columns("ss.rds_databases_schedules",wanted_columns,sys_time) 
    t1=list(data_from_database[time_column])
    for i in range(len(t1)):
        #passing data to aws console to update
        p=stop_db(i,connection,data_from_database)   
        print(p)
# getting time column based on script running time to pass aws console for update
get_time_count_list(time_column)   
print("%s seconds ====>" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")

