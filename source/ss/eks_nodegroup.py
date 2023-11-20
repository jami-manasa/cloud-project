from api.pdbc_api  import *
from api.aws_api import *
import time
start_time = time.time()
print("--------------------------------------------- datetime:{} -----------------------------------------".format(datetime.now()))
account_ids=[]
#db connection
connection = db_connection("ss")
try:
    cursor = connection.cursor()
    #query for getting account details 
    Query = "SELECT account_id from ad.aws_accounts;"
    cursor.execute(Query)
    records = cursor.fetchall()
    for i in records:
        account_ids.append(i[0])  
    cursor.close()
except:
    print("check whether the database exits or not")

regions=[]
def myconverter(o):
    if isinstance(o, datetime):
        return o.__str__()
columns=get_columns("ss.eks_nodegroups")
ignore_columns=[]
ignore_columns=['mon_scaleout_time', 'mon_scaleout_count', 'mon_scalein_time', 'mon_scalein_count','tue_scaleout_time', 'tue_scaleout_count', 'tue_scalein_time', 'tue_scalein_count', 'wed_scaleout_time', 'wed_scaleout_count', 'wed_scalein_time', 'wed_scalein_count', 'thu_scaleout_time', 'thu_scaleout_count', 'thu_scalein_time', 'thu_scalein_count', 'fri_scaleout_time', 'fri_scaleout_count', 'fri_scalein_time', 'fri_scalein_count', 'sat_scaleout_time', 'sat_scaleout_count', 'sat_scalein_time', 'sat_scalein_count', 'sun_scaleout_time', 'sun_scaleout_count', 'sun_scalein_time', 'sun_scalein_count']
for account_id in account_ids:
    data_from_aws = pd.DataFrame(columns=columns)
    #account details from database
    account_details=get_awsaccount_details(account_id,connection) 
    regions=account_details['regions']
    account_name=account_details['account_name'][0]
    acc_id=account_id
    tag_keys=account_details['tag_keys']
    assume_role=account_details['assume_role'][0]
    for region in regions:
        try:
            ec2 = create_client(account_id, region, assume_role, 'ec2') 
            #creating client ssm client
            ssm_client =create_client(account_id, region, assume_role, 'ssm') 
            #creating client pricing
            pricng = create_client(account_id, 'us-east-1', assume_role, 'pricing') 
            # response = ec2.describe_instances()
            eks = create_client(account_id, region, assume_role, 'eks') 
            list_response = eks.list_clusters()
            #intsances details from aws console
            data=json.dumps(list_response,default = myconverter)
            # instace details
            data= json.loads(data) 
            tmp = '/aws/service/global-infrastructure/regions/%s/longName' % region
            ssm_response = ssm_client.get_parameter(Name = tmp)
            region_name = ssm_response['Parameter']['Value']
            cluster_names=[]
            if  data['clusters']:
                cluster_names.append(data['clusters'])
                for i in range(len(cluster_names[0])):
                    details_cluster=eks.describe_cluster(name=cluster_names[0][i])
                    details_cluster=json.dumps(details_cluster,default = myconverter)
                    details_cluster= json.loads(details_cluster) 
                    cluster_arn=details_cluster['cluster']['arn']
                    cluster_arn= cluster_arn.replace('/',':')
                    cluster_name =details_cluster['cluster']['name']
                    cluster_status  =details_cluster['cluster']['status']
                    kubernets_version=details_cluster['cluster']['version']
                    endpoint_Private_Access=details_cluster['cluster']['resourcesVpcConfig']['endpointPrivateAccess']
                    endpoint_Public_Access=details_cluster['cluster']['resourcesVpcConfig']['endpointPublicAccess']
                    cluster_created_on=details_cluster['cluster']['createdAt']
                    m=details_cluster['cluster']['tags']
                    list_nodegroups=eks.list_nodegroups(clusterName=cluster_names[0][i])
                    list_nodegroups=json.dumps(list_nodegroups,default = myconverter)
                    list_nodegroups= json.loads(list_nodegroups) 
                    nodegroups_names=[]
                    if  list_nodegroups['nodegroups']:
                        nodegroups_names.append(list_nodegroups['nodegroups'])
                        list_nodegroups=eks.list_nodegroups(clusterName=cluster_names[0][i])
                    list_nodegroups=json.dumps(list_nodegroups,default = myconverter)
                    list_nodegroups= json.loads(list_nodegroups) 
                    nodegroups_names=[]
                    if  list_nodegroups['nodegroups']:
                        nodegroups_names.append(list_nodegroups['nodegroups'])
                        for i in range(len(nodegroups_names[0])):
                            details_nodegroup=eks.describe_nodegroup(clusterName=cluster_name,nodegroupName=nodegroups_names[0][i]) 
                            details_nodegroup=json.dumps(details_nodegroup,default = myconverter)
                            details_nodegroup= json.loads(details_nodegroup)
                            node_group_name=details_nodegroup['nodegroup']['nodegroupName']
                            node_group_arn=details_nodegroup['nodegroup']['nodegroupArn']
                            node_group_arn= node_group_arn.replace('/',':')
                            node_group_status=details_nodegroup['nodegroup']['status']
                            node_group_min_size=details_nodegroup['nodegroup']['scalingConfig']['minSize']
                            node_group_max_size=details_nodegroup['nodegroup']['scalingConfig']['maxSize']
                            node_group_desired_size=details_nodegroup['nodegroup']['scalingConfig']['desiredSize']
                            autoScaling_groups_name=details_nodegroup['nodegroup']['resources']['autoScalingGroups'][0]['name']
                            nodegroup_instancetypes=details_nodegroup['nodegroup']['instanceTypes']
                            if nodegroup_instancetypes:
                                nodegroup_instancetypes=nodegroup_instancetypes[0]
                                hourly_price=price(pricng,nodegroup_instancetypes,region_name,"linux",'AmazonEC2')
                            else:
                                nodegroup_instancetypes=None
                                hourly_price=None
                            if hourly_price != None:
                                hourly_price = str(hourly_price)
                            print(hourly_price)
                            nodegroup_capacityType=details_nodegroup['nodegroup']['capacityType']
                            nodegroup_diskSize=details_nodegroup['nodegroup']['diskSize']
                            nodegroup_health_issues=details_nodegroup['nodegroup']['health']['issues']
                            m=details_nodegroup['nodegroup']['tags']
                            try:
                                tag_value_1=str(tag_keys[0])+":"+[v for k, v in m.items() if k == tag_keys[0]][0] 
                            except Exception as e:
                                tag_value_1=None
                            try: 
                                tag_value_2=str(tag_keys[1])+":"+[v for k, v in m.items() if k == tag_keys[1]][0] 
                            except Exception as e:
                                tag_value_2=None
                            try:
                                tag_value_3=str(tag_keys[2])+":"+[v for k, v in m.items() if k == tag_keys[2]][0] 
                            except Exception as e:
                                tag_value_3=None
                            try:
                                tag_value_4=str(tag_keys[3])+":"+[v for k, v in m.items() if k == tag_keys[3]][0] 
                            except Exception as e:
                                tag_value_4=None
                            df_new_rows = pd.DataFrame({
                                                        "cluster_arn":[cluster_arn],
                                                        "node_group_arn":[node_group_arn],
                                                        "node_group_name":[node_group_name],
                                                        "autoscaling_groups_name":[autoScaling_groups_name],
                                                        "node_group_status":[node_group_status],
                                                        "node_group_min_size":[node_group_min_size],
                                                        "node_group_max_size":[node_group_max_size],
                                                        "node_group_desired_size":[node_group_desired_size],
                                                        "account_id":[acc_id],
                                                        'account_name':[account_name],
                                                        "region":[region],
                                                        'os':"linux",
                                                        'hourly_price':[hourly_price],
                                                        'tag_value_1' : [tag_value_1],
                                                        'tag_value_2' : [tag_value_2],
                                                        'tag_value_3' : [tag_value_3],
                                                        'tag_value_4' : [tag_value_4],
                                                        "nodegroup_instancetypes":[nodegroup_instancetypes],
                                                        "nodegroup_capacitytype":[nodegroup_capacityType],
                                                        "nodegroup_disksize":[nodegroup_diskSize],
                                                        "nodegroup_health_issues":[nodegroup_health_issues],
                                                        })
                            data_from_aws = pd.concat([data_from_aws, df_new_rows]) 
        except Exception as e:
            print(region_name)
            print("----")
            print(e)                                     
    if data_from_aws.empty:
        remove_records("ss.eks_nodegroups","account_name",account_name)
    else:
        output=pass_to_db("ss.eks_nodegroups",data_from_aws,"account_name",ignore_columns)
        print("done")