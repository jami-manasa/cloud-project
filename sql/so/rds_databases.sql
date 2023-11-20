CREATE TABLE so.rds_databases (
	db_resource_id      	varchar(40),
    db_identifier           varchar(40) ,
    db_tag_name        		varchar(40),
    date_created_on 		varchar(40) ,
	db_instance_type		varchar(40),
	db_storage_type			varchar(40),
	db_storage_size 		int,
	account_id      		varchar(40) ,
	account_name     	    varchar(40) ,
    region      			varchar(40),
	tag_value_1    			varchar(40),
	tag_value_2    			varchar(40),
	tag_value_3     		varchar(40),
    tag_value_4    			varchar(40),
	unused_hours            double precision,
	hourly_price            double precision,
	total_waste_spent		double precision,
	recent_scan_time        timestamp without time zone,
	ignore 					boolean,
	PRIMARY KEY(db_resource_id),
    CONSTRAINT fk_account_id
      FOREIGN KEY(account_id) 
	  REFERENCES ad.aws_accounts(account_id)
	  ON DELETE CASCADE
);
