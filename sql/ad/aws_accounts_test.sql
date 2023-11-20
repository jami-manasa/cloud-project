CREATE TABLE ad.aws_accounts_test (
    account_id          varchar(40) ,
    account_name        varchar(40),
    regions             varchar[],
    assume_role         varchar(40),
    account_category    varchar(40),
	tag_key_1           varchar(40),
    tag_key_2           varchar(40),
    tag_key_3           varchar(40),
    tag_key_4           varchar(40),
    uid                 uuid,
    PRIMARY KEY(account_id)
);
