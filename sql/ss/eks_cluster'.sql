drop table "ss".eks_cluster;
CREATE TABLE "ss".eks_cluster(
	cluster_arn               varchar(100),
	cluster_name              varchar(40),
	cluster_status            varchar(10),
	node_group_count          varchar(3),
	kubernets_version         varchar(10),
	endpoint_Private_Access   varchar(10),
	endpoint_Public_Access    varchar(10),
	cluster_created_on        varchar(40),
    account_id                varchar(40),
	account_name              varchar(40),
    region                    varchar(40),
    tag_value_1               varchar(40),
    tag_value_2               varchar(40),
    tag_value_3               varchar(40),
    tag_value_4               varchar(40),
	enable_scalling           varchar(10),
	PRIMARY KEY(cluster_arn),
	CONSTRAINT fk_account_id
	FOREIGN KEY(account_id)
	REFERENCES ad.aws_accounts(account_id)
	ON DELETE CASCADE
);