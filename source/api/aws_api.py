from imports import*
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
            
                ],
                    FormatVersion='aws_v1',
                    MaxResults=1
        )
        od = json.loads(response['PriceList'][0])['terms']['OnDemand']
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
                                               starttime=u- timedelta(hours=336),
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


def get_max_cpu1(cloudwatch_client,id):  # for so 
    try:
        u = datetime.utcnow()
        u = u.replace(tzinfo=pytz.utc)
        starttime=u- timedelta(hours=336)
        connection = db_connection("so")
        cursor = connection.cursor()
        cursor.execute("""select count(*) from so.ec2_instances """)
        count_in = cursor.fetchall()[0][0]
        if count_in == 0:
            response = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=3600,
                                                Dimensions=[{
                                                    'Name': 'InstanceId','Value': id},
                                                    ],
                                                starttime=u- timedelta(hours=336),
                                                EndTime=u,
                                                Statistics=['Maximum'])
            timestamp = jmespath.search("Datapoints[*].[Timestamp]",response)
            maximum  = jmespath.search("Datapoints[*].[Maximum]",response)
            if len(maximum)> 0: 
                maximum = np.array(maximum).reshape(len(maximum))
                df = pd.DataFrame(data=timestamp,columns=['date'])
                df['max']= maximum
                df['new_date'] = [d.date() for d in df['date']]
                df['new_time'] = [d.time() for d in df['date']]
                df = df.sort_values(by="date",ignore_index= True)
                present= df[df.iloc[:,2] == df.iloc[-1,2]]
                past = df[df.iloc[:,2] != df.iloc[-1,2]]
                c= (present['max']> 0).any()
                c1= len(past['max'])
                if c == True:
                   
                    return (0,0)
                else:
                   
                    return(int(336-c1),id,df.iloc[0,0])#,id
            else:
               
                return(int(336),id,starttime)#,id
        elif count_in != 0:
            # print("entered else block count is more than zero")
            response = cloudwatch_client.get_metric_statistics(Namespace='AWS/EC2',MetricName='CPUUtilization',Period=3600,
                                                Dimensions=[{
                                                    'Name': 'InstanceId','Value': id},
                                                    ],
                                                starttime=u- timedelta(hours=24),
                                                EndTime=u,
                                                Statistics=['Maximum'])
            timestamp = jmespath.search("Datapoints[*].[Timestamp]",response)
            maximum  = jmespath.search("Datapoints[*].[Maximum]",response)
            if len(maximum)> 0: 
               
                maximum = np.array(maximum).reshape(len(maximum))
                df = pd.DataFrame(data=timestamp,columns=['date'])
                df['max']= maximum
                df['new_date'] = [d.date() for d in df['date']]
                df['new_time'] = [d.time() for d in df['date']]
                df = df.sort_values(by="date",ignore_index= True)
                present= df[df.iloc[:,2] == df.iloc[-1,2]]
                c= (present['max']> 0).any()
                if c == True :
                    return(0,0,0)
            else:
               
                try:
                    cursor.execute("select unused_hours from so.ec2_instances WHERE instance_id = %s """ , [str(id),])
                    y1= cursor.fetchall()[0][0]
                except Exception as e:
                    print("e:", e)
                cursor.execute("select not_being_used_from from so.ec2_instances WHERE instance_id = %s """ , [str(id),])
                n=cursor.fetchall()[0][0]
                return(int(y1+24),id,n)
    except Exception as e:
        print(e)
        print("something went wrong in cloudwatch")
