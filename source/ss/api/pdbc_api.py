import pandas as pd
import psycopg2
import pandas as pd
from io import StringIO
import time
import psycopg2.extras
from api.aws_api import *
from sqlalchemy import create_engine 
# try:
#     with open("/bin/config.json", "r") as conf_file:
#         configs = json.load(conf_file)
# except FileNotFoundError as err:
#     print(err.__str__())
#     raise err

# def db_connection(schema):
#     try:
#         connection=psycopg2.connect(options="-c search_path=dbos,{}".format(schema), **configs["DATABASE"])
#         return connection
#     except Exception as e:
#         print("Failed create a db connection -- ",e)

def db_connection(schema):
    try:
        connection=psycopg2.connect(
    host="av-database.cpemqxe3lmha.us-east-2.rds.amazonaws.com",
    port=5432,
    dbname="postgres",
    user="postgres",
    password="x6Iny3sgl7mfgA8mL9WW"
)
        return connection
    except Exception as e:
        print("Failed create a db connection -- ",e)


def insert_values(database_with_schema,data_from_aws):
    database=database_with_schema.split('.')
    connection=db_connection(database[0])
    
    cursor = connection.cursor()
    try:   
        try:
             buffer = StringIO()  
             data_from_aws.to_csv(buffer, index=False, header=False) 
             col=get_columns(database_with_schema)
             print(data_from_aws,"++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
             for row in data_from_aws.itertuples():
                 cursor.execute("""
                 INSERT INTO ss.ec2_instances_schedules (instance_id,instance_tag_name,tag_value_1,tag_value_2,tag_value_3,tag_value_4,instance_type,account_id,account_name,region, platform,instance_state,hourly_price,recent_launch_time)
                 VALUES (%s, %s,%s, %s,%s, %s,%s, %s,%s, %s,%s, %s,%s, %s)
                 """,(row.instance_id ,row.instance_tag_name ,row.tag_value_1 ,row.tag_value_2 ,row.tag_value_3 ,row.tag_value_3 ,row.instance_type ,row.account_id ,row.account_name ,row.region ,row.platform ,row.instance_state ,row.hourly_price,row.recent_launch_time))
             cursor.execute("""UPDATE ss.ec2_instances_schedules SET auto_stop_enable = 'true' WHERE account_name = 'mj-one')"""
             cursor.execute("""query2 = "UPDATE ss.{0} SET auto_stop_enable = 'false' WHERE {1} = '{2}'".format(database[1],'instance_id','i-0d9c856701a373199'))"""
                 
            # Commit and close  
             connection.commit()
             cursor.close()
             connection.close()
        except Exception as e:
            print("error:",e)
        connection.commit() 
        # cursor.close()
        return "successfully"
    except (Exception, psycopg2.DatabaseError) as error:   
        print(error,"-----------------------------")


def delete_values(database_with_schema,data_to_delete):
    database=database_with_schema.split('.')
    connection=db_connection(database[0])
    data_to_delete = tuple(data_to_delete['bucket_name'])
    try:
        cursor = connection.cursor()
        # exit()
        query = "delete from {} where bucket_name in {}".format(database_with_schema,data_to_delete)
        cursor.execute(query)
        connection.commit()
        cursor.close()
        time.sleep(3)
        return "Succesfully deleted ."
    except:
        return "Failed to delete ."

def data_crud_operation(connection,count,data_from_cloud,updating_by,database_with_schema,ignore_columns):
    database=database_with_schema.split('.')
    try:
        if count == 0:
            inserting=insert_values(database_with_schema,data_from_cloud)
            return "All data needs to insert ."
        else:
            data_from_database = get_dbdata(database_with_schema)
            data_from_database = data_from_database.convert_dtypes()
            # print(data_from_database,"--------------------------------------what your looking 111111111111")
            pk=str(list(data_from_database.columns.values.tolist())[0])
            group_name=data_from_cloud[updating_by].unique()
            
            # print(data_from_database,"--------------------------------------what your looking 00000000")
            data_from_database=data_from_database[data_from_database[updating_by] == group_name[0]]
            # print(data_from_database,"--------------------------------------what your looking 99999999999")
            data_from_cloud=data_from_cloud.reset_index(drop=True)
            # print(data_from_database,"--------------------------------------what your looking 666666666666")
            data_from_database=data_from_database.reset_index(drop=True)
            try:
                data_from_database = data_from_database.replace({'<NA>': 'None'}, regex=True)
            except Exception as e:
                    print(e)
                    print("new error-------------------------here--->>")
            
            print(data_from_database,"--------------------------------------what your looking 222222222")
            if len(ignore_columns) != 0:
                try:
                    data_from_cloud.drop(ignore_columns, axis='columns', inplace=True)
                    ignore_columns.append(pk)
                    data_from_cloud = pd.merge(data_from_cloud, data_from_database[ignore_columns], how='left', on=pk)
                    # print(list(data_from_cloud.columns),"------------------------------after merging cloud and database data if database has alreday some data---------------------------->")
                    # print(list(data_from_database.columns),"-=====================>>>>>>>>>>>>>>>")
                    data_from_cloud = data_from_cloud[list(data_from_database.columns)]
                    # print(list(data_from_cloud.columns),"------------------------------after merging cloud and database data if database has alreday some data---------------------------->")
                    # print(list(data_from_database.columns))
                    
                    ignore_columns.pop()
                    # print(ignore_columns)
                except Exception as e:
                    print(e)
                    print("Getting issuses while ignoring the columns you mentioned .")
                    
            if data_from_database.empty:
                print("=============================== now 29th nov")
                print("All data need to insert.")
                inserting=insert_values(database_with_schema,data_from_cloud)
                print(str(inserting)+" changes in database")
            elif data_from_cloud.equals(data_from_database):
                print("=============================== now 29th nov 44444444444444444")
                print("No need to update the data.Because its equal to data from database.")
               
            else:
                cursor = connection.cursor()
                # print(data_from_cloud.head(3))
                # print("=============================== now 29th nov  7777777777777")
                # print(data_from_database.head(3))
                query = "DELETE FROM ss.{0} WHERE {1} = '{2}'".format(database[1],str(updating_by),str(group_name[0]))
        
                cursor.execute(query)
                connection.commit()
                cursor.close()

                
                inserting=insert_values(database_with_schema,data_from_cloud)
                if "failed" in inserting:
                    inserting=insert_values(database_with_schema,data_from_database)
                print(str(inserting)+"changes to old data")
        return "Closing the connection ."
    except Exception as e:
        print(e)
        print("Getting issuses while moving with crud operation .")




 
def pass_to_db(database_with_schema,data_from_cloud,updating_by,ignore_columns):
    try:
        database=database_with_schema.split('.')
        connection=db_connection(database[0])
        cursor = connection.cursor()
        query = "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='{}');".format(database[1])
        cursor.execute(query)
        table = cursor.fetchone()[0]
        connection.commit()
        if table:
            print("Already database exits ------>.")
        else:
            print("Database table needs to Create ")
        cursor = connection.cursor()
        # query = " SELECT COUNT(*) FROM {};".format(database[1])
        query = " SELECT COUNT(*) FROM ss. ec2_instances_schedules;"
        # print(query,"-----------------------")
        try:
            cursor.execute(query)
        except Exception as e :
            print(e)
        
        count = cursor.fetchone()[0]
        print("Before entering into the process, There are "+ str(count) +" records exits in database.")
        print(data_crud_operation(connection,count,data_from_cloud,updating_by,database_with_schema,ignore_columns))
        connection.commit()
        cursor.close()
        return "task executed successfully"
    except:
        print("getting issues while passing data into a database")




def get_awsaccount_details(account_id,connection):
    cursor = connection.cursor()
    cursor.execute( """select regions,account_name,tag_key_1,tag_key_2,tag_key_3,tag_key_4,assume_role from  ad.aws_accounts WHERE account_id = %s""",[str(account_id),])
    reg_keys=cursor.fetchall()[0]
    regions=reg_keys[0]
    account_name=reg_keys[1]
    tag_keys=reg_keys[2:-1]
    list=[regions,[account_name],tag_keys,[reg_keys[-1]]]
    df=pd.DataFrame(list).transpose()
    df.columns =['regions', 'account_name','tag_keys','assume_role']
    connection.commit()
    cursor.close()
    return(df)


def get_columns(database_with_schema):
    database=database_with_schema.split('.')
    connection=db_connection(database[0])
    try:
        cursor = connection.cursor()
        # query = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{}';".format(database[1])
        query = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ec2_instances_schedules';"
        cursor.execute(query)
        records = cursor.fetchall()
        connection.commit()
        columns=[]
        for i in records:
            columns.append(i[0])
        columns=columns
        return columns
    except:
        print("check whether the database exits or not")

def get_dbdata(database_with_schema):
    try:
        columns=get_columns(database_with_schema)
        database=database_with_schema.split('.')
        connection=db_connection(database[0])
        cursor = connection.cursor()
        query = " SELECT * FROM {};".format(database_with_schema)
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=columns)
        try:
            data_from_database = data_from_database.replace(np.nan, None)
        except:
            print("new error-------------------------here--->>")
        # print(data_from_database.head(2),"-----------data_from_database------------?")
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits or not")
def get_dbdata_with_columns(database_with_schema,wanted_columns):
    col = ','.join([str(elem) for elem in wanted_columns])
    try:
        database=database_with_schema.split('.')
        connection=db_connection(database[0])
        cursor = connection.cursor()
        query = " SELECT {0} FROM {1};".format(col,database[1])
        print(query)
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        connection.commit()
        return data_from_database
    except:
        print("check whether table or column name ----------------------------------------------------------------> ")

def remove_records(database_with_schema,update_by,update_value):
    database=database_with_schema.split('.')
    connection=db_connection(database[0])
    print("          ")
    try:
        cursor = connection.cursor()
        query = "DELETE FROM {0} WHERE {1} = '{2}'".format(database[1],update_by,update_value)
        cursor.execute(query)
        print("Deleted old data from database - ",update_value)
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        print(e)


























# def insert_values(database_with_schema,data_from_aws):
#     database=database_with_schema.split('.')
#     connection=db_connection(database[0])
#     try:
#         cursor = connection.cursor()
#         buffer = StringIO()
#         data_from_aws.to_csv( buffer, index=False, header=False)
#         # f=open("name.csv",'r')
#         # cursor.copy_expert("COPY ss.ec2_instances_schedules FROM STDIN DELIMITER ','; ", buffer)
#         # buffer.seek(0)


#         # copy_query = "COPY 'ss.ec2_instances_schedules'  FROM STDOUT csv DELIMITER '\t' NULL ''  ESCAPE '\\' HEADER "  # Replace your table name in place of mem_info
#         # cursor.copy_expert(copy_query, buffer)
#         # buffer.seek(0)
#         # cursor.copy_from(f, "'ss'.ec2_instances_schedules",sep=",",null='')
#         buffer.getvalue()
#         print(cursor.copy_expert(buffer,"{}".format(database_with_schema), sep=","))
#         # connection.commit() 
#         # cursor.close()
#         return "succesfully "
#     except (Exception, psycopg2.DatabaseError) as error:    


# def insert_values(database_with_schema,data_from_aws):
#     print("in insert function")
#     database=database_with_schema.split('.')
#     connection=db_connection(database[0])
#     try:
#         cursor = connection.cursor()
#         buffer = StringIO()
#         data_from_aws.to_csv( buffer, index=False, header=False)
#         print(data_from_aws)
#         print("---------------------------------------------------------------------------------------------------------------------------")
#         # f=open("name.csv",'r')
#         # cursor.copy_expert("COPY ss.ec2_instances_schedules FROM STDIN DELIMITER ','; ", buffer)
#         # buffer.seek(0)


#         # copy_query = "COPY ss.ec2_instances_schedules  FROM STDOUT csv DELIMITER '\t' NULL ''  ESCAPE '\\' HEADER "  # Replace your table name in place of mem_info
        
#         # cursor.copy_expert(copy_query, buffer)
        
#         # buffer.seek(0)
#         print("here I am")
#         cursor.copy_from(data_from_aws, "'ss'.ec2_instances_schedules",sep=",",null='')
#         print("-------------------1")
#         buffer.getvalue()
#         print(cursor.copy_expert(buffer,"{}".format(database_with_schema), sep=","))
#         print("finally----------------------------------->")
#         connection.commit() 
#         cursor.close()
#         print("finally----------------------------------->1111")
#         return "successfully"
#     except (Exception, psycopg2.DatabaseError) as error:        
#         print("Error: %s" % error)
#         return "failed to insert data "

#         print("Error: %s" % error)
#         return "failed to insert data "
