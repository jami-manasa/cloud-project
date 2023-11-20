from time import time
from threading import Thread
from datetime import date
import calendar
# import sys,os
# sys.path.insert(1,os.path.abspath(__file__).split('source')[0]+'source/api')
from api.pdbc_api  import *
from api.aws_api import *

start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))
connection = db_connection("ss")
my_date = date.today()
#todays's day
day=calendar.day_name[my_date.weekday()]
now = datetime.now()
sys_time = now.strftime("%H:%M")
# print(sys_time)
wanted_columns=["account_id","region","instance_id","instance_tag_name","account_name","is_statefull_set","statefull_set_name","statefull_set_arn"]
wanted_columns1=["account_id","region",'db_identifier',"is_statefull_set","statefull_set_name","statefull_set_arn"]
#getting requried data from database if and only if current time matches database time
def get_dbdata_with_columns(database_with_schema,wanted_columns,sys_time):
    col = ','.join([str(elem) for elem in wanted_columns])
    sys_time=[sys_time]
    try:
        database=database_with_schema.split('.')
        connection=db_connection(database[0])
        cursor = connection.cursor()
        # sql query for getting  only data which is equal to current time
        query = " select {0} FROM {1} where {2} = '{3}' and enable_schedules='true';".format(col,database[1],wanted_columns[8],sys_time[0])
        print(query)
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        print(data_from_database)
        if data_from_database.empty:
            
            print('No instance is ready to Start')
        else:
            print("Some intances are ready to start.")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns")  


def  get_rds_info(db_id,account_id,region):
    reg_keys=get_awsaccount_details(account_id,connection)
    assume_role=reg_keys['assume_role'][0]
    rds=create_client(account_id, region, assume_role, 'rds')
    response = rds.describe_db_instances(DBInstanceIdentifier=db_id,)
    db_status=response['DBInstances'][0]['DBInstanceStatus']
    return db_status
    # =='available' 
def get_dbdata_with_columns1(database_with_schema,wanted_columns1,sys_time): 
    col = ','.join([str(elem) for elem in wanted_columns1])
    try:
        database=database_with_schema.split('.')
        connection=db_connection(database[0])
        cursor = connection.cursor()
        try:
            query = " select {0} FROM {1} where statefull_set_arn = '{3}';".format(col,database[1],wanted_columns1[5],sys_time)   
        except Exception as e:
            print(e)
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns1)
        if data_from_database.empty:
            print("empty rds dataframe")
        else:
            print("")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns")


def start_ec2(connection,data_from_database):
    # print(data_from_database)
    ins_id=list(data_from_database['instance_id'])
    account_id=list(data_from_database["account_id"])
    regions=list(data_from_database["region"])
    print(len(data_from_database))
    if len(data_from_database):
        for i in range(len(data_from_database)):
            id=ins_id[i]
            acc_id=account_id[i]
            region=regions[i]
            reg_keys=get_awsaccount_details(acc_id,connection)
            assume_role=reg_keys['assume_role'][0]
            ec2 = create_client(acc_id, region, assume_role, 'ec2')
            response = ec2.start_instances(InstanceIds=[id], DryRun=False)
            print(id+" is "+response['StartingInstances'][0]['CurrentState']['Name']+".")


def non_statefull_(non_statefull):
    if not non_statefull.empty:
        for i in range(len(non_statefull)):
            p=start_ec2(connection,non_statefull)  
            print(p)
        # print("hello")
    else:
        print("no instance is ready to stop")

def statefull_(statefull):
    if not statefull.empty:
        statefull_set_arn=statefull['statefull_set_arn'].unique()
        for j in range(len(statefull_set_arn)):
            each_statefull_sets=statefull[statefull["statefull_set_arn"] == statefull_set_arn[j]]
            data_from_rds=get_dbdata_with_columns1("ss.rds_databases_schedules",wanted_columns1,statefull_set_arn[j]) 
            c=0
            for i in range(len(data_from_rds)):
                db_id=list(data_from_rds['db_identifier'])[i]
                account_id=list(data_from_rds["account_id"])[i]
                region=list(data_from_rds["region"])[i]
                acc_id=list(data_from_rds["account_id"])[i]
                # print(db_id,account_id,region)
                db_status=get_rds_info(db_id,account_id,region)
                if db_status=="available":
                    c=c+1
            if c==len(data_from_rds.index):
                print("starting statefull sets instances...........")
                p=start_ec2(connection,each_statefull_sets)  
            else:
                print("Please wait untill db's starts---------------------->")
                time =now + timedelta(minutes = 5)
                time=time.strftime("%H:%M")
                print(time)
                cursor = connection.cursor()
                try:
                    query=" UPDATE ec2_instances_schedules  SET {2} = '{0}' where  statefull_set_arn = '{1}'".format(time,statefull_set_arn[j],time_column)
                    print("updated time in ec2 table....")
                except Exception as e:
                    print(e)
                cursor.execute(query) 
                connection.commit()    

    else:
        print("no instance is ready to start")
#getting column name based on which day script running  
days_count = {'Monday':{'time':'mon_str_time'}, 
    'Tuesday':{'time':'tue_str_time'},
    'Wednesday':{'time':'wed_str_time'},
    'Thursday': {'time':'thu_str_time'},
    'Friday':{'time':'fri_str_time'},
    'Saturday':{'time':'sat_str_time'},
    'Sunday':{'time':'sun_str_time'}}
for key in list(days_count.keys()):
    if(key == day):
        columns = days_count[key]
time_column = columns['time']

wanted_columns.append(time_column)
#data from database
data_from_database=get_dbdata_with_columns("ss.ec2_instances_schedules",wanted_columns,sys_time) 




print("%s seconds ====> " % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")




























