from imports import * 
try:
    with open("/bin/config.json", "r") as conf_file:
        configs = json.load(conf_file)
except FileNotFoundError as err:
    print(err.__str__())
    raise err

def db_connection(schema):
    try:
        connection=psycopg2.connect(options="-c search_path=dbos,{}".format(schema), **configs["DATABASE"])
        return connection
    except Exception as e:
        print("Failed create a db connection -- ",e)
# def insert_values(database_with_schema,data_from_aws):
#     database=database_with_schema.split('.')
#     connection=db_connection(database[0])
#     try:
#         cursor = connection.cursor()
#         buffer = StringIO()
#         data_from_aws.to_csv( buffer, index=False, header=False)
#         buffer.seek(0) 
#         cursor.copy_from(buffer,"{}".format(database[1]), sep=",",null='')
#         connection.commit()
#         cursor.close()
#         return "succesfully "
#     except (Exception, psycopg2.DatabaseError) as error:        
#         print("Error: %s" % error)
#         return "failed to insert data "


def insert_values(database_with_schema,data_from_aws):
    database=database_with_schema.split('.')
    connection=db_connection(database[0])
    try:
        cursor = connection.cursor()
        buffer = StringIO()
        data_from_aws.to_csv( buffer, index=False, header=False)
        print(data_from_aws)
        print("---------------------------------------------------------------------------------------------------------------------------")
        # f=open("name.csv",'r')
        # cursor.copy_expert("COPY ss.ec2_instances_schedules FROM STDIN DELIMITER ','; ", buffer)
        # buffer.seek(0)


        copy_query = "COPY 'ss.ec2_instances_schedules'  FROM STDOUT csv DELIMITER '\t' NULL ''  ESCAPE '\\' HEADER "  # Replace your table name in place of mem_info
        cursor.copy_expert(copy_query, buffer)
        buffer.seek(0)
        print("here iam")
        cursor.copy_from(f, "'ss'.ec2_instances_schedules",sep=",",null='')
        print("-------------------1")
        # buffer.getvalue()
        # print(cursor.copy_expert(buffer,"{}".format(database_with_schema), sep=","))
        print("finally----------------------------------->")
        connection.commit() 
        cursor.close()
        return "successfully"
    except (Exception, psycopg2.DatabaseError) as error:        
        print("Error: %s" % error)
        return "failed to insert data "





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
        return "Succesfully deleted"
    except:
        return "Failed to delete"
def data_crud_operation(connection,count,data_from_cloud,updating_by,database_with_schema,ignore_columns):
    database=database_with_schema.split('.')
    data_from_aws=pd.DataFrame(data_from_cloud)  
    try:
        if count == 0:
          
            inserting=insert_values(database_with_schema,data_from_cloud)
            return "all data needs to insert"
        else:
            data_from_database = get_dbdata(database_with_schema)
            pk=str(list(data_from_database.columns.values.tolist())[0])
            group_name=data_from_cloud[updating_by].unique()
            data_from_database=data_from_database[data_from_database[updating_by] == group_name[0]]
            data_from_cloud=data_from_cloud.sort_values(by = pk)
            data_from_cloud=data_from_cloud.reset_index(drop=True)
            data_from_database= pd.DataFrame(data_from_database.sort_values(by = pk))
            data_from_database=data_from_database.reset_index(drop=True)
            if len(ignore_columns) != 0:
                try:
                    data_from_cloud.loc[data_from_cloud[pk].isin(data_from_database[pk]),ignore_columns ] = data_from_database[ignore_columns]
                    print("considering your ignored columns")
                except:
                    print("getting issuses while ignoring the columns you mentioned")
            if data_from_database.empty:
                print("all data need to insert")
                inserting=insert_values(database_with_schema,data_from_cloud)
                print(str(inserting)+"make changes in database")
            elif data_from_cloud.equals(data_from_database):
              
                print("no need to update the data.Because its equal to data from database")
            else:
                cursor = connection.cursor()
                query = "DELETE FROM {0} WHERE {1} = '{2}'".format(database[1],str(updating_by),str(group_name[0]))
                cursor.execute(query)
                connection.commit()
                cursor.close()
                inserting=insert_values(database_with_schema,data_from_cloud)
                print(str(inserting)+"make changes to old data")
        return "closing the connection"
    except Exception as e:
        print(e)
        print("getting issuses while moving with crud operation")

        
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
            print("already database exits")
        else:
            print("database table needs to Create ")
        cursor = connection.cursor()
        query = " SELECT COUNT(*) FROM {};".format(database[1])
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print("Before entering into the process, There are "+ str(count) +" records exits in database.")
        print(data_crud_operation(connection,count,data_from_cloud,updating_by,database_with_schema,ignore_columns))
        connection.commit()
        cursor.close()
        return "task executed succesfully"
    except:
        print("getting issuses while passing data into a database")









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
        query = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{}';".format(database[1])
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
        cursor.execute(query)
        data_from_database = pd.DataFrame(cursor.fetchall(),columns=wanted_columns)
        connection.commit()
        return data_from_database
    except:
        print("check whether the database exits the exact columns")

def remove_records(database_with_schema,update_by,update_value):
    database=database_with_schema.split('.')
    connection=db_connection(database[0])
    print("")
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
#         print("Error: %s" % error)
#         return "failed to insert data "
