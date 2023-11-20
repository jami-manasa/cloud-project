CREATE TABLE so.s3_buckets (
    bucket_name             varchar(40),
    account_id              varchar(40) ,
	account_name            varchar(40) ,
    tag_value_1             varchar(40),
	tag_value_2             varchar(40),
	tag_value_3             varchar(40),
    tag_value_4             varchar(40),
    created_on              timestamp without time zone,
    life_cycle_enabled      varchar(40),
    data_size_2weeksago     varchar(40),
	data_size_now           varchar(40) ,
	objects_count_2weeksago double precision ,
	objects_count_now       double precision ,
    standard_storage_size   varchar(40),
	standardia_storage_size varchar(40),
    glacier_storage_size    varchar(40),
    unused_hours            double precision,
    hourly_price            double precision,
    total_waste_spent		double precision,
    recent_scan_time        timestamp without time zone,
    ignore                  boolean,
    PRIMARY KEY(bucket_name),
    CONSTRAINT fk_account_id
      FOREIGN KEY(account_id) 
	  REFERENCES ad.aws_accounts(account_id)
	  ON DELETE CASCADE
);
