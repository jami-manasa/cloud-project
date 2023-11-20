CREATE TABLE so.eip_addresses (
    ipv4_address      		varchar(40) ,
    allocation_id     		varchar(40),
    association_id			varchar(40) ,
	tag_value_1    			varchar(40),
	tag_value_2     		varchar(40),
	tag_value_3     		varchar(40),
    tag_value_4    			varchar(40),
	account_id      		varchar(40) ,
	account_name      		varchar(40) ,
    region          		varchar(40),
	unused_hours            double precision,
	hourly_price            double precision,
	total_waste_spent		double precision,
	recent_scan_time        timestamp without time zone,
	ignore 					boolean,
	PRIMARY KEY(allocation_id),
    CONSTRAINT fk_account_id
      FOREIGN KEY(account_id) 
	  REFERENCES ad.aws_accounts(account_id)
	  ON DELETE CASCADE
);