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
        query = " select {0} FROM {1} where {2} = '{3}';".format(col,database[1],wanted_columns[5],sys_time[0]) #getting  only data which is equal to current time
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        if data_from_database.empty:
            print('No work .')
        else:
            print("Some work is there ..")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns") 
 # using scale out time and count update Max size 
def scale_in(i,connection,c1,data_from_database):                                     
            auto_scaling_group_name=list(data_from_database['auto_scaling_group_name'])
            account_id=list(data_from_database["account_id"])
            c=c1[i]
            acc_id=account_id[i]
            asg_name=auto_scaling_group_name[i]
            reg_keys=get_awsaccount_details(acc_id,connection)
            r=reg_keys['regions']
            for region in r:
                assume_role=reg_keys['assume_role'][0]
                auto = create_client(acc_id, region, assume_role, 'autoscaling')
                try:
                    response=auto.update_auto_scaling_group(AutoScalingGroupName=asg_name,MinSize=c,
                    DesiredCapacity =c,)
                    return("Succesfully changed minimum capacity..")
                except ClientError as e:
                    print('Error', e)  
#today      
my_date = date.today()
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
wanted_columns=["auto_scaling_group_name","minimum_capacity","desired_capacity","account_name","account_id"]
 #getting column name based on which day script running  
days_count = {
    'Monday':{'time':'mon_scalein_time', 'count':'mon_scalein_count'},
    'Tuesday':{'time':'tue_scalein_time', 'count':'tue_scalein_count'},    
    'Wednesday':{'time':'wed_scalein_time', 'count':'wed_scalein_count'},
    'Thursday': {'time':'thu_scalein_time', 'count':'thu_scalein_count'},
    'Friday':{'time':'fri_scalein_time', 'count':'fri_scalein_count'},
    'Saturday':{'time':'sat_scalein_time', 'count':'sat_scalein_count'},
    'Sunday':{'time':'sun_scalein_time', 'count':'sun_scalein_count'}
}
for key in list(days_count.keys()):
    if(key == day):
        columns = days_count[key]
time_column = columns['time']
count_column = columns['count']
def get_time_count_list(time_column,count_column):
    wanted_columns.append(time_column)
    wanted_columns.append(count_column)
     #data from database
    data_from_database=get_dbdata_with_columns("ss.auto_scaling_groups",wanted_columns,sys_time) 
    t1=list(data_from_database[time_column])
    c1=list(data_from_database[count_column])
    for i in range(len(t1)):
        #passing data to aws console to update
        p=scale_in(i,connection,c1,data_from_database)  
        print(p)

 # getting count column and time column based on script running time to pass aws console fpr update
get_time_count_list(time_column,count_column)  
print("%s seconds ====>" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")
