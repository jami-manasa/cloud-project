drop table so.ebs_volumes;
CREATE TABLE so.ebs_volumes (
    volume_id      					varchar(40) ,
    volume_tag_name     			varchar(40),
    attached_ec2_instance_id 		varchar(40) ,
	attached_ec2_instance_status	varchar(40) ,
	volume_size     				varchar(40),
	volumes_type					varchar(40),
	volume_state					varchar(20),
	tag_value_1    					varchar(40),
	tag_value_2    					varchar(40),
	tag_value_3     				varchar(40),
    tag_value_4    					varchar(40),
	account_id      				varchar(40) ,
	account_name      				varchar(40) ,
    region          				varchar(40),
	instance_stopped_time			timestamp,
	unused_hours            		double precision,
	hourly_price            		double precision,
	total_waste_spent				double precision,
	recent_scan_time        		timestamp without time zone,
	ignore 							boolean,
	
	PRIMARY KEY(volume_id),
    CONSTRAINT fk_account_id
      FOREIGN KEY(account_id) 
	  REFERENCES ad.aws_accounts(account_id)
	  ON DELETE CASCADE
);

