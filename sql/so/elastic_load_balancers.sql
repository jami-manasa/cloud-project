`CREATE TABLE so.elastic_load_balancers(
-- loadbalancer_arn        varchar(150),
loadbalancer_name       varchar(40),
account_name            varchar(40),
account_id              varchar(40),
region                  varchar(40),
elb_type                varchar(40),
status                  varchar(40),
target_group_name       varchar(40),
attached_ec2_instances  varchar(1000),
tag_value_1             varchar(40),
tag_value_2             varchar(40),
tag_value_3             varchar(40),
tag_value_4             varchar(40),
unused_hours            double precision,
hourly_price            double precision,
total_waste_spent		    double precision,
recent_scan_time        timestamp without time zone,
ignore                  boolean,
PRIMARY KEY(loadbalancer_arn),
    CONSTRAINT fk_account_id
      FOREIGN KEY(account_id) 
	  REFERENCES ad.aws_accounts(account_id)
	  ON DELETE CASCADE
);

`