CREATE TABLE "ss".ec2_instances_schedules (
    instance_id          varchar(40) ,
    instance_tag_name    varchar(40),
    tag_value_1    	     varchar(40),
	tag_value_2          varchar(40),
	tag_value_3          varchar(40),
    tag_value_4          varchar(40),
    instance_type        varchar(40),
    account_id           varchar(40),
    account_name         varchar(40),
    region        	     varchar(40),
    platform             varchar(40),
    instance_state       varchar(40),
    hourly_price         varchar(40),
    mon_str_time         varchar(40),
	mon_stp_time         varchar(40),
    tue_str_time         varchar(40),
	tue_stp_time         varchar(40),
    wed_str_time         varchar(40),
	wed_stp_time         varchar(40),
    thu_str_time         varchar(40),
	thu_stp_time         varchar(40),
	fri_stp_time         varchar(40),
    fri_str_time         varchar(40),
    sat_str_time         varchar(40),
	sat_stp_time         varchar(40),
    sun_str_time         varchar(40),
    sun_stp_time         varchar(40),
	ec2_group_name       varchar(40),
    auto_stop_enable     varchar(40), 
    stack_arn            varchar(150),
	is_statefull_set     varchar(40),
	statefull_set_name   varchar(40),
	statefull_set_arn    varchar(150),
    enable_schedules     varchar(10),
    recent_launch_time   varchar(100),
    PRIMARY KEY(instance_id),
    CONSTRAINT fk_account_id
      FOREIGN KEY(account_id) 
	  REFERENCES ad.aws_accounts(account_id)
	  ON DELETE CASCADE
);



CREATE TABLE "ss".ec2_instances_schedules (
    instance_id          varchar(40) ,
    instance_tag_name    varchar(40),
    tag_value_1    	     varchar(40),
	tag_value_2          varchar(40),
	tag_value_3          varchar(40),
    tag_value_4          varchar(40),
    instance_type        varchar(40),
    account_id           varchar(40),
    account_name         varchar(40),
    region        	     varchar(40),
    platform             varchar(40),
    instance_state       varchar(40),
    hourly_price         varchar(40),
	ec2_group_name       varchar(40),
    auto_stop_enable     varchar(40), 
    recent_launch_time   varchar(100),
    PRIMARY KEY(instance_id),
    CONSTRAINT fk_account_id
      FOREIGN KEY(account_id) 
	  REFERENCES ad.aws_accounts(account_id)
	  ON DELETE CASCADE
);
