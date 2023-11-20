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
columns=get_columns("ss.eks_cluster")
# print(len(columns))
print("-------------------------------------")
ignore_columns=[]
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
                    # print(details_cluster,"__________________________________")
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
                        print(nodegroups_names)
                        node_group_count=len(nodegroups_names[0])
                    else:
                        node_group_count=0
                    m=details_cluster['cluster']['tags']
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
                                    "cluster_name" :[cluster_name],
                                    "cluster_status" :[cluster_status],
                                    "node_group_count":    [node_group_count],   
                                    "kubernets_version" :[kubernets_version],
                                    'endpoint_private_access':[endpoint_Private_Access],
                                    "endpoint_public_access" :[endpoint_Public_Access],
                                    "cluster_created_on" :[cluster_created_on],
                                    "account_id":[acc_id],
                                    'account_name':[account_name],
                                    "region":[region],
                                    'tag_value_1' : [tag_value_1],
                                    'tag_value_2' : [tag_value_2],
                                    'tag_value_3' : [tag_value_3],
                                    'tag_value_4' : [tag_value_4],
                                    })
                    data_from_aws = pd.concat([data_from_aws, df_new_rows])       
        except Exception as e:
            print(region)
            print("----")
            print(e)
    if data_from_aws.empty:
        remove_records("ss.eks_cluster","account_name",account_name)
    else:
        output=pass_to_db("ss.eks_cluster",data_from_aws,"account_name",ignore_columns)
        print("done")
    print("-----------------------------------------------------------------------------------------------------------------------------------------------")
    
   






