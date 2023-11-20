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
        query = " select {0} FROM {1} where {2} = '{3}';".format(col,database[1],wanted_columns[7],sys_time[0]) #getting  only data which is equal to current time
        # print(query)
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
def eks_scale_in(eks,cluster_name,node_group_name,count):
            try:
                response = eks.update_nodegroup_config(clusterName=cluster_name,nodegroupName=node_group_name,scalingConfig={'desiredSize': count}
                )
                return("Updated Succesfully--------->")
            except Exception as e:
                 print(e)
my_date = date.today()
day=calendar.day_name[my_date.weekday()]
now = datetime.now()
sys_time= now.strftime("%H:%M")
print(sys_time)
wanted_columns=["node_group_name","node_group_min_size","node_group_desired_size","account_name","account_id","cluster_arn","region"]
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
    wanted_columns.append("auto_scale_enabled")
     #data from database
    data_from_database=get_dbdata_with_columns("ss.eks_nodegroups",wanted_columns,sys_time) 
    if not data_from_database.empty:
        for i in range(len(data_from_database)):
            #passing data to aws console to update
            
            account_id=list(data_from_database["account_id"])[i]
            region=list(data_from_database["region"])[i]     
            cluster_arn=list(data_from_database['cluster_arn'])[i]
            cluster_name=list(data_from_database['cluster_arn'])[0].split(":")[-1]
            node_group_name=list(data_from_database['node_group_name'])[i]
            reg_keys=get_awsaccount_details(account_id,connection)
            count=list(data_from_database[count_column])[i]
            r=reg_keys['regions']
            for reg in r:
                if reg==region:
                    assume_role=reg_keys['assume_role'][0]
            print(node_group_name)
            query="select enable_scalling from ss.eks_cluster WHERE cluster_arn='{}'".format(cluster_arn)
            print(query,"---------------------------------------------------------------------------------")
            cursor = connection.cursor()
            cursor.execute(query)
            enable_scalling = list(cursor.fetchall())[0][0]
            print(enable_scalling)
            eks=create_client(account_id, region, assume_role, 'eks')
            if enable_scalling=="true":
                p=eks_scale_in(eks,cluster_name,node_group_name,count)  
                print(p)
            else:
                p=eks_scale_in(eks,cluster_name,node_group_name,0)  
                print(p)
 # getting count column and time column based on script running time to pass aws console fpr update
get_time_count_list(time_column,count_column)  
print("%s seconds ====>" % (time.time() - start_time),"time taken by script")
print("-----------------------------------------------END---------------------------------------------------")
print("script_end")
