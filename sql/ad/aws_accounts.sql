CREATE TABLE ad.aws_accounts (
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


-- INSERT INTO ad.aws_accounts(
-- 	account_id, account_name,assume_role, tag_key_1, tag_key_2, tag_key_3, tag_key_4, regions)
-- 	VALUES (373457809612, 'ce-white', 'role_admin','Environment', 'Solution', 'Role', 'Tier', {'us-east-1','us-east-2','ap-southeast-1','eu-central-1'}),
--     (176744831436, 'ce-blue', 'role_admin','Environment', 'Solution', 'Role', 'Tier', {'us-east-1','us-east-2','ap-southeast-1','eu-central-1'}),
--     (575175637389, 'ce-red', 'role_admin','Env', 'Sol', 'Role', 'Tier',{'us-east-1','us-east-2','ap-southeast-1','eu-central-1'});
