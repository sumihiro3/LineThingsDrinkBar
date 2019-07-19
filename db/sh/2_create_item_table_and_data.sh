#!/bin/bash
psql -U $POSTGRES_USER -d $POSTGRES_DB << "EOSQL"
CREATE TABLE item (
    id varchar(100) PRIMARY KEY,
    name varchar(100),
    description text,
    unit_price integer NOT NULL,
    stock integer NOT NULL DEFAULT 0,
    slot integer NOT NULL DEFAULT 0,
    image_url varchar(200),
    active boolean DEFAULT true,
    sales_period_timestamp_from bigint NOT NULL DEFAULT 0,
    sales_period_timestamp_to bigint NOT NULL DEFAULT 0,
    created_timestamp bigint NOT NULL DEFAULT 0,
    updated_timestamp bigint NOT NULL DEFAULT extract(epoch from now())
);
insert into item (id, name, description, unit_price, stock, active, slot, image_url, created_timestamp) values ('item-0001', 'コーラ', 'スキッと爽やかなコーラ', 100, 100, true, 0, 'https://4.bp.blogspot.com/-Mv0_RUDAK2M/V9ppyNuaczI/AAAAAAAA9yE/l2_CPuRoWOk60Sh9BAoaPqDi0y1YT2R_wCLcB/s800/petbottle_cola.png', 1558925437);
insert into item (id, name, description, unit_price, stock, active, slot, image_url, created_timestamp) values ('item-0003', '麦茶 ', 'ごくごく飲める麦茶', 80, 100, false, 1, 'https://2.bp.blogspot.com/-FjMG-YiRjOM/V9ppyvigbEI/AAAAAAAA9yI/h4Kri1aOOMYWhP6HT9BsphoD2hQuQL0wACLcB/s800/petbottle_tea_koucha.png', 1558925437);
insert into item (id, name, description, unit_price, stock, active, slot, image_url, created_timestamp) values ('item-0002', 'オレンジジュース', 'みんな大好きオレンジジュース', 90, 10, true, 1, 'https://3.bp.blogspot.com/-X3w1bg1-Xcs/V8VFAHqD6eI/AAAAAAAA9XA/nAth-47Zy6s1h2XqC2rducvPW4PGObOdwCLcB/s800/juice_orange.png', 1558925437);
EOSQL
