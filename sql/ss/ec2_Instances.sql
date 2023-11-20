
CREATE TABLE "ss".ec2_instances (
    ins_id          varchar(40) ,
    ins_tag_name    varchar(40),
	ins_tag_sol     varchar(40),
	ins_tag_env     varchar(40),
    ins_tag_role    varchar(40),
    tag_value_1    	varchar(40),
	tag_value_2     varchar(40),
	tag_value_3     varchar(40),
    tag_value_4     varchar(40),
    ins_type        varchar(40),
    acc_id          varchar(40),
    acc_name        varchar(40),
    region        	varchar(40),
    hourly_price    varchar(40),
    ec2_group_name  varchar(40),
    auto_stop_enable varchar(40), 
    mon_str_time    varchar(40),
	mon_stp_time    varchar(40),
    tue_str_time    varchar(40),
	tue_stp_time    varchar(40),
    wed_str_time    varchar(40),
	wed_stp_time    varchar(40),
    thu_str_time    varchar(40),
	thu_stp_time    varchar(40),
	fri_stp_time    varchar(40),
    fri_str_time    varchar(40),
    sat_str_time    varchar(40),
	sat_stp_time    varchar(40),
    sun_str_time    varchar(40),
    sun_stp_time    varchar(40),
    PRIMARY KEY(ins_id),
    CONSTRAINT fk_account_id
      FOREIGN KEY(acc_id) 
	  REFERENCES ad.aws_accounts(account_id)
	  ON DELETE CASCADE
);
