import json
import boto3
import pandas as pd
from datetime import datetime,timedelta
import pytz
import jmespath
import numpy as np 
from datetime import date
import pandas as pd
import numpy as np 
from datetime import date
from api.pdbc_api  import *
from api.aws_api import *
def myconverter(o):
    if isinstance(o, datetime):
        return o.__str__()



def create_client(account_id, region, assume_role, service):
    sts_client = boto3.client('sts')
    assumed_role_object=sts_client.assume_role(
        RoleArn="arn:aws:iam::"+str(account_id)+":role/"+assume_role,
        RoleSessionName="AssumeRoleSession1"
    )
    credentials=assumed_role_object['Credentials']
    client=boto3.client(
        service,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name=region
    )
    return client



def price(pricing_client,intype,region_name,platform,service_code):
    try:
        if service_code == 'AmazonRDS':
            field_value= 'databaseEngine'
        elif service_code == 'AmazonEC2':
            field_value = 'operatingSystem'
        else:
            field_value = None
        response = pricing_client.get_products(
        ServiceCode='{}'.format(service_code),
        Filters=[
                    {
                        'Type': 'TERM_MATCH',
                        'Field': 'ServiceCode',
                        'Value': '{}'.format(service_code)
                    },
              {
                        "Type": "TERM_MATCH",
                        "Field": field_value,
                        "Value": "{}".format(platform)
                    },
            
             {
                        "Type": "TERM_MATCH",
                        "Field": "location",
                        "Value": "{}".format(region_name)
                    },
             
              {
                        "Type": "TERM_MATCH",
                        "Field": "instanceType",
                        "Value":  "{}".format(intype)
                    },
                    {    'Type' :'TERM_MATCH', 'Field':'tenancy','Value':'Shared'},
                    {'Type' :'TERM_MATCH', 'Field':'marketoption','Value':'OnDemand'},
                    {'Type' :'TERM_MATCH', 'Field':'preInstalledSw','Value':'NA'},
                    {"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}
            
                ],
                    FormatVersion='aws_v1',
                    MaxResults=1
        )
        od = json.loads(response['PriceList'][0])['terms']['OnDemand']
        m=json.loads(response['PriceList'][0])
        
        id1 = list(od)[0]
        id2 = list(od[id1]['priceDimensions'])[0]
        return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']
            
    except Exception as e:
        print("something went wrong in pricing ")

def get_max_cpu(cloudwatch_client,id):
    try:
        u = datetime.utcnow()
        u = u.replace(tzinfo=pytz.utc)
         
        response = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=3600,
                                               Dimensions=[{
                                                   'Name': 'InstanceId','Value': id},],
                                               StartTime=u- timedelta(hours=336),
                                               EndTime=u,
                                               Statistics=['Maximum'])
        x=jmespath.search("Datapoints[*].[Maximum]",response)
        
        if len(x)>0:
            return (max(x)[0])
    except Exception as e:
       
        print("something went wrong in cloudwatch")

def platform(service_client,img_id):
    img_id=[img_id]
    response1= service_client.describe_images(ImageIds=img_id)
    data=json.dumps(response1,default = myconverter)
    data= json.loads(data)
    try:
        os=data['Images'][0]['PlatformDetails']
    except IndexError:
        os=None
    if os == "Linux/UNIX" or os == None:
        os="Linux"
    elif os == "Red Hat Enterprise Linux":
        os = "RHEL"
    elif os == "Windows" or os == "windows":
        os = "Windows"
    else:
        os =None
    return os


def get_whole_matrice_ec2_scan_1(u,cloudwatch_client,id,time_diff):
        response = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=300,
                                                    Dimensions=[{
                                                        'Name': 'InstanceId','Value': id},],
                                                    StartTime=u-timedelta(hours=time_diff,minutes=5),
                                                    EndTime=u-timedelta(minutes=5),
                                                    Statistics=['Maximum'])

        timestamp = jmespath.search("Datapoints[*].[Timestamp]",response)
        maximum  = jmespath.search("Datapoints[*].[Maximum]",response)
        return maximum , timestamp

def get_whole_matrice_ec2_scan_2(u,cloudwatch_client,id,time_diff):
        response1 = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=300,
                                                    Dimensions=[{
                                                        'Name': 'InstanceId','Value': id},],
                                                    StartTime=u-timedelta(hours=120,minutes=5),
                                                    EndTime=u-timedelta(minutes=5),
                                                    Statistics=['Maximum'])
        response2= cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=300,
                                                    Dimensions=[{
                                                        'Name': 'InstanceId','Value': id},],
                                                    StartTime=u-timedelta(hours=time_diff,minutes=5),
                                                    EndTime=u-timedelta(hours=120,minutes=5),
                                                    Statistics=['Maximum'])


        timestamp1 = jmespath.search("Datapoints[*].[Timestamp]",response1)
        maximum1  = jmespath.search("Datapoints[*].[Maximum]",response1)
        timestamp2 = jmespath.search("Datapoints[*].[Timestamp]",response2)
        maximum2  = jmespath.search("Datapoints[*].[Maximum]",response2)
        timestamp = timestamp1+timestamp2
        maximum  = maximum1 + maximum2
        return maximum , timestamp

def get_whole_matrice_ec2_scan_3(u,cloudwatch_client,id,time_diff):
    
        response1 = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=300,
                                                    Dimensions=[{
                                                        'Name': 'InstanceId','Value': id},],
                                                    StartTime=u-timedelta(hours=120,minutes=5),
                                                    EndTime=u-timedelta(minutes=5),
                                                    Statistics=['Maximum'])
        response2= cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=300,
                                                    Dimensions=[{
                                                        'Name': 'InstanceId','Value': id},],
                                                    StartTime=u-timedelta(hours=240,minutes=5),
                                                    EndTime=u-timedelta(hours=120,minutes=5),
                                                    Statistics=['Maximum'])

        response3= cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=300,
                                                    Dimensions=[{
                                                        'Name': 'InstanceId','Value': id},],
                                                    StartTime=u-timedelta(hours=time_diff,minutes=5),
                                                    EndTime=u-timedelta(hours=240,minutes=5),
                                                    Statistics=['Maximum'])


        timestamp1 = jmespath.search("Datapoints[*].[Timestamp]",response1)
        maximum1  = jmespath.search("Datapoints[*].[Maximum]",response1)
        timestamp2 = jmespath.search("Datapoints[*].[Timestamp]",response2)
        maximum2  = jmespath.search("Datapoints[*].[Maximum]",response2)
        timestamp3 = jmespath.search("Datapoints[*].[Timestamp]",response3)
        maximum3 = jmespath.search("Datapoints[*].[Maximum]",response3)
        timestamp = timestamp1+timestamp2+timestamp3
        maximum  = maximum1 + maximum2+ maximum3
        return maximum , timestamp
def get_idle_hours_ec2_instance(cloudwatch_client,ec2_client,id,list_ins_ids):
    try:
        response = ec2_client.describe_instances(InstanceIds=[id,],)
        status=response["Reservations"][0]['Instances'][0]['State']['Name']
        recent_lt=response["Reservations"][0]['Instances'][0]['LaunchTime']
        d_t = datetime.utcnow().replace(tzinfo=pytz.utc)
        time_diff = d_t - recent_lt
        time_diff = (time_diff.total_seconds()/3600)
        if time_diff > 336:
            time_diff = 336 
        u = datetime.utcnow()
        u = u.replace(tzinfo=pytz.utc)
        if status =="running":
            if id not in list_ins_ids:
                if time_diff <= 120:
                    scan_data = get_whole_matrice_ec2_scan_1(u,cloudwatch_client,id,time_diff)
                elif time_diff > 120 and time_diff <= 240:
                    scan_data = get_whole_matrice_ec2_scan_2(u,cloudwatch_client,id,time_diff)
                elif time_diff > 240 and time_diff <= 336:
                    scan_data = get_whole_matrice_ec2_scan_3(u,cloudwatch_client,id,time_diff)

                timestamp = scan_data[1]
                maximum  = scan_data[0]
                if len(maximum)>0:
                    maximum = np.array(maximum).reshape(len(maximum))
                    df = pd.DataFrame(data=timestamp,columns=['date'])
                    df['max']= maximum
                    df['new_date'] = [d.date() for d in df['date']]
                    df['new_time'] = [d.time() for d in df['date']]
                    df = df.sort_values(by="date",ignore_index= True)
                    df1 =  df[df['max']>6]
                    arr = df1.index.tolist()
                    arr = arr[::-1]
                    size = len(arr)
                    index = 0
                    if len(arr):
                        for i in range(size - 3):
                            if (arr[i] - arr[i + 3] == 3)  :
                                index=arr[i]
                                break
                    if index == 0:
                        last_used_date = list(df['date'])[0]
                        return(time_diff,id,recent_lt)
                    else:
                        for_temp_cal = df.iloc[index+1:]
                        if len(for_temp_cal):
                            last_used_date= list(for_temp_cal['date'])[0]
                            d_t = datetime.utcnow().replace(tzinfo=pytz.utc)
                            idle_hours = d_t - list(for_temp_cal['date'])[0]
                            idle_hours = (idle_hours.total_seconds()/3600)
                            return(idle_hours,id,list(for_temp_cal['date'])[0])
                        else:
                            last_used_date = list(df['date'])[0]
                            return(0,id,last_used_date)
                        
                else:
                    return (336,id,time_diff)
        
            else:
                print("Adding 4 hours ")
                response = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=300,
                                                                Dimensions=[{
                                                                    'Name': 'InstanceId','Value': id},],
                                                                StartTime=u- timedelta(hours=24),
                                                                EndTime=u,
                                                                Statistics=['Maximum'])
                timestamp = jmespath.search("Datapoints[*].[Timestamp]",response)
                maximum  = jmespath.search("Datapoints[*].[Maximum]",response)
                if len(maximum)> 0: 
                    try:
                        maximum = np.array(maximum).reshape(len(maximum))
                        df = pd.DataFrame(data=timestamp,columns=['date'])
                        df['max']= maximum
                        df['new_date'] = [d.date() for d in df['date']]
                        df['new_time'] = [d.time() for d in df['date']]
                        df = df.sort_values(by="date",ignore_index= True)
                        df1 =  df[df['max']>6]
                        arr = df1.index.tolist()
                        arr = arr[::-1]
                        size = len(arr)
                        index = 0
                        if len(arr):
                            for i in range(size - 3):
                                
                                if (arr[i] - arr[i + 3] == 3)  :
                                    index=arr[i]
                                    break
                        if index == 0:
                            last_used_date = list(df['date'])[0]
                            return(time_diff,id,recent_lt)
                        else:
                            try:
                                connection = db_connection("so")
                                cursor1 = connection.cursor()
                                cursor1.execute("""select unused_hours from so.ec2_instances WHERE instance_id = %s """ , [str(id),])
                                y1= cursor1.fetchall()[0][0]
                            except Exception as e:
                                print("e:", e)
                            
                            cursor1.execute("""select not_being_used_from from so.ec2_instances WHERE instance_id = %s """ , [str(id),])
                            n=cursor1.fetchall()[0][0]
                            return(int(y1+4),id,n)
                    except Exception as e:
                        print(e)
                else:
                    return(int(336),id,time_diff)#,id
    

    except Exception as e:
        print(e)


u = datetime.utcnow()
u = u.replace(tzinfo=pytz.utc)
def get_whole_matrice_rds_scan_1(u,cloudwatch_client,db_id,main_time_diff):
        response = cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=300,
                                Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime=u-timedelta(hours = main_time_diff,minutes=5),EndTime=u-timedelta(minutes=5), Statistics=['Sum'])
        timestamp = jmespath.search("Datapoints[*].[Timestamp]",response)
        maximum  = jmespath.search("Datapoints[*].[Sum]",response)  
        return maximum , timestamp

def get_whole_matrice_rds_scan_2(u,cloudwatch_client,db_id,time_diff):
        response1 = cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=300,
                                Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime= u - timedelta(hours = 120,minutes=5),EndTime=u-timedelta(minutes=5), Statistics=['Sum'])
        timestamp1 = jmespath.search("Datapoints[*].[Timestamp]",response1)
        maximum1  = jmespath.search("Datapoints[*].[Sum]",response1)
        response2= cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=300,
                                Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime= u - timedelta(hours = time_diff,minutes=5),EndTime= u - timedelta(hours = 120,minutes=5), Statistics=['Sum'])
        timestamp2 = jmespath.search("Datapoints[*].[Timestamp]",response2)
        maximum2  = jmespath.search("Datapoints[*].[Sum]",response2)
        
        timestamp = timestamp1 + timestamp2
        maximum  = maximum1 + maximum2
        return maximum , timestamp

def get_whole_matrice_rds_scan_3(u,cloudwatch_client,db_id,time_diff):
   
    response1 = cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=300,
                                Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime= u - timedelta(hours = 120,minutes=5),EndTime=u-timedelta(minutes=5), Statistics=['Sum'])
    response2= cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=300,
                                Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime= u - timedelta(hours = 240,minutes=5),EndTime= u - timedelta(hours = 120,minutes=5), Statistics=['Sum'])
    response3 = cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=300,
                                Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime=u - timedelta(hours = time_diff,minutes=5),EndTime=u - timedelta(hours = 240,minutes=5), Statistics=['Sum'])


    timestamp1 = jmespath.search("Datapoints[*].[Timestamp]",response1)
    maximum1  = jmespath.search("Datapoints[*].[Sum]",response1)
    timestamp2 = jmespath.search("Datapoints[*].[Timestamp]",response2)
    maximum2  = jmespath.search("Datapoints[*].[Sum]",response2)
    timestamp3 = jmespath.search("Datapoints[*].[Timestamp]",response3)
    maximum3 = jmespath.search("Datapoints[*].[Sum]",response3)
    timestamp = timestamp1 + timestamp2 + timestamp3
    maximum  = maximum1 + maximum2 + maximum3
    return maximum , timestamp

def get_whole_matrice_rds_start_time(u,cloudwatch_client,db_id,start_time,end_time):
        response = cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=300,
                                Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime=start_time,EndTime=end_time, Statistics=['Sum'])
        timestamp = jmespath.search("Datapoints[*].[Timestamp]",response)
        maximum  = jmespath.search("Datapoints[*].[Sum]",response)  
        return maximum , timestamp

def get_rds_metrideatails(cloudwatch_client,db_id,list_rds_ids,db_resource_id,cursor):
    if db_resource_id not in list_rds_ids:
        print("New process  ")
        for i in range(3):
            if i == 0:
                str_time = 120
                stp_time = 0
            elif i == 1:
                str_time = 240
                stp_time = 120
            elif i == 2:
                str_time = 336
                stp_time = 240
            start_time = u - timedelta(hours=str_time,minutes=5)
            stp_time = u - timedelta(hours=stp_time,minutes=5)
            # for getting start time of db
            m = get_whole_matrice_rds_start_time(u,cloudwatch_client,db_id,start_time,stp_time)  
            timestamp = m[1]
            maximum = m[0]
            if len(maximum)>0:
                maximum = np.array(maximum).reshape(len(maximum))
                df = pd.DataFrame(data=timestamp,columns=['date'])
                df['sum']= maximum
                df['new_date'] = [d.date() for d in df['date']]
                df['new_time'] = [d.time() for d in df['date']]
                df = df.sort_values(by="date",ignore_index= True)
                df1 = df[df['sum']>=0]
                arr = list(df1['date'])
                size = len(arr)
                start_time  = 0
                if len(arr):
                    for i in range(size - 3):
                        diff =arr[i + 3]  - arr[i] 
                        diff = (diff.total_seconds()/3600)
                        if diff == 0.25:
                            start_time  = 0
                        else:
                            
                            start_time = arr[i+3]
                            break
                else:
                    start_time = 0
            if start_time != 0:
                if start_time != 0:
                    d_t = datetime.utcnow().replace(tzinfo=pytz.utc)
                    main_time_diff  = d_t - start_time
                    main_time_diff = (main_time_diff.total_seconds()/3600)
                else:
                    main_time_diff = 336
                if main_time_diff <= 120:
                        scan_data = get_whole_matrice_rds_scan_1(u,cloudwatch_client,db_id,main_time_diff)
                elif main_time_diff > 120 and main_time_diff <= 240:
                    scan_data = get_whole_matrice_rds_scan_2(u,cloudwatch_client,db_id,main_time_diff)
                elif main_time_diff > 240 and main_time_diff <= 336:
                    scan_data = get_whole_matrice_rds_scan_3(u,cloudwatch_client,db_id,main_time_diff)
                timestamp = scan_data[1]
                maximum  = scan_data[0]
                if len(maximum)>0:
                    maximum = np.array(maximum).reshape(len(maximum))
                    df = pd.DataFrame(data=timestamp,columns=['date'])
                    df['max']= maximum
                    df['new_date'] = [d.date() for d in df['date']]
                    df['new_time'] = [d.time() for d in df['date']]
                    df = df.sort_values(by="date",ignore_index= True)
                    df1 =  df[df['max']>0]
                    final_data=df1.iloc[-1:]
                    arr = df1.index.tolist()
                    arr = arr[::-1]
                    size = len(arr)
                    index = 0
                    if len(arr)==0:
                        return(main_time_diff,db_id,list(df['date'])[0])
                    if len(arr):
                        for i in range(size - 3):
                            if (arr[i] - arr[i + 1] == 1)  and (arr[i+1] - arr[i + 2] == 1)  :
                                index=arr[i]
                                break
                    if len(final_data):
                        today =date.today()
                        if list(df['date'])[index] == today:
                            last_used_date= list(df['date'])[0]
                            return(0,db_id,last_used_date)
                        else:
                            for_temp_cal = df.iloc[index+1:]
                            if len(for_temp_cal):
                                d_t = datetime.utcnow().replace(tzinfo=pytz.utc)
                                idle_hours = d_t - list(for_temp_cal['date'])[0]
                                idle_hours = (idle_hours.total_seconds()/3600)
                                return(idle_hours,db_id,list(for_temp_cal['date'])[0])
                            
                break

        
        
    else:
        print("ADD 4 hours")
        response = cloudwatch_client.get_metric_statistics(Namespace='AWS/RDS',MetricName='DatabaseConnections',Period=300,
                                Dimensions=[{'Name': 'DBInstanceIdentifier','Value': db_id},],StartTime=u-timedelta(hours = 24,minutes=5),EndTime=u-timedelta(minutes=5), Statistics=['Sum'])
        timestamp = jmespath.search("Datapoints[*].[Timestamp]",response)
        maximum  = jmespath.search("Datapoints[*].[Sum]",response)
        if len(maximum)>0:
            maximum = np.array(maximum).reshape(len(maximum))
            df = pd.DataFrame(data=timestamp,columns=['date'])
            df['max']= maximum
            df['new_date'] = [d.date() for d in df['date']]
            df['new_time'] = [d.time() for d in df['date']]
            df = df.sort_values(by="date",ignore_index= True)
            df1 =  df[df['max']>0]
            final_data=df1.iloc[-1:]
            arr = df1.index.tolist()
            arr = arr[::-1]
            size = len(arr)
            index = 0
            if len(arr)==0:
                cursor.execute("""select unused_hours from so.rds_databases WHERE db_resource_id = %s """ , [str(db_resource_id),])
                y1= cursor.fetchall()[0][0]
                return(int(y1+4),db_id,list(df['date'])[0])
            if len(arr):
                for i in range(size - 3):
                    if (arr[i] - arr[i + 1] == 1)  and (arr[i+1] - arr[i + 2] == 1)  :
                        index=arr[i]
                        break
            if len(final_data):
                today =date.today()
                if list(df['date'])[index] == today:
                    last_used_date= list(df['date'])[0]
                    return(0,db_id,last_used_date)
                else:
                    try:
                        cursor.execute("""select unused_hours from so.rds_databases WHERE db_resource_id = %s """ , [str(db_resource_id),])
                        y1= cursor.fetchall()[0][0]
                    except Exception as e:
                        print("e:", e)
                    return(int(y1+4),db_id)



            

