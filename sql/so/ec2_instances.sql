drop table so.ec2_instances;
CREATE TABLE so.ec2_instances (
    instance_id                   varchar(40) ,
    instance_name                 varchar(40),
    instance_type                 varchar(40) ,
    instance_state_name           varchar(40),
    instance_recent_launch_time   timestamp without time zone,
    platform                      varchar(40) ,
    account_id                    varchar(40) ,
    account_name                  varchar(40) ,
    region                        varchar(40),
    tag_value_1                   varchar(40) ,
    tag_value_2                   varchar(40) ,
    tag_value_3                   varchar(40) ,
    tag_value_4                   varchar(40) ,
    not_being_used_from           timestamp without time zone,
    unused_hours                  integer,
    hourly_price                  double precision,
    total_waste_spent		          double precision,
    recent_scan_time              timestamp without time zone,
    ignore                        boolean,
    PRIMARY KEY(instance_id),
    CONSTRAINT fk_account_id
      FOREIGN KEY(account_id) 
	  REFERENCES ad.aws_accounts(account_id)
	  ON DELETE CASCADE
);
