
# import sys,os
# sys.path.insert(1,os.path.abspath(__file__).split('source')[0]+'source/api')
# from imports import *
from api.pdbc_api  import *
from api.aws_api import *
from datetime import date
import calendar
import time
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
        #getting  only data which is equal to current time and day
        query = " select {0} FROM {1} where {2} = '{3}';".format(col,database[1],wanted_columns[5],sys_time[0])
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        if data_from_database.empty:
            print('No work ..')
        else:
            print("Some work is there...")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns")  

# using scale out time and count update Min size
def scale_out(i,connection,c1,data_from_database): 
            auto_scaling_group_name=list(data_from_database['auto_scaling_group_name'])
            account_id=list(data_from_database["account_id"])
            c=c1[i]
            acc_id=account_id[i]
            asg_name=auto_scaling_group_name[i]
            #getting account detials  from database
            reg_keys=get_awsaccount_details(acc_id,connection)
            r=reg_keys['regions']
            for region in r:
                assume_role=reg_keys['assume_role'][0]
                # autoscaling client 
                auto = create_client(acc_id, region, assume_role, 'autoscaling')
                try:
                    #to update min size $ desire capacity in aws console based on user's requriement
                    response=auto.update_auto_scaling_group(AutoScalingGroupName=asg_name,MinSize=c,
                    DesiredCapacity =c,)
                    return("Succesfully changed minimum capacity..")
                except ClientError as e:
                    print('Error', e) 
#todays day  
my_date = date.today()
day=calendar.day_name[my_date.weekday()]
now = datetime.now()
h=str(now.hour)
m=str(now.minute)
if len(m)==1:
    m="0"+m
if len(h)==1:
    h="0"+h
# present time
sys_time= h+":"+m
#wanted columns :required columns in update operation  in data base and aws console 
wanted_columns=["auto_scaling_group_name","minimum_capacity","desired_capacity","account_name","account_id"]
 #getting column name based on which day script running  
days_count = {
    'Monday':{'time':'mon_scaleout_time', 'count':'mon_scaleout_count'},
    'Tuesday':{'time':'tue_scaleout_time', 'count':'tue_scaleout_count'},
    'Wednesday':{'time':'wed_scaleout_time', 'count':'wed_scaleout_count'},
    'Thursday': {'time':'thu_scaleout_time', 'count':'thu_scaleout_count'},
    'Friday':{'time':'fri_scaleout_time', 'count':'fri_scaleout_count'},
    'Saturday':{'time':'sat_scaleout_time', 'count':'sat_scaleout_count'},
    'Sunday':{'time':'sun_scaleout_time', 'count':'sun_scaleout_count'}
}
for key in list(days_count.keys()):
    if(key == day):
        columns = days_count[key]
#time  data in list formart 
time_column = columns['time'] 
#count data in list formart
count_column = columns['count']
#function for getting list of time and count details 
def get_time_count_list(time_column,count_column):
    wanted_columns.append(time_column)
    wanted_columns.append(count_column)
    data_from_database=get_dbdata_with_columns("ss.auto_scaling_groups",wanted_columns,sys_time)
    t1=list(data_from_database[time_column])
    c1=list(data_from_database[count_column])
    for i in range(len(t1)):
        p=scale_out(i,connection,c1,data_from_database)
        print(p)

#1st step : getting todays day and time for further operation
get_time_count_list(time_column,count_column)
print("%s seconds ====>" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")
