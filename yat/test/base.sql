CREATE TABLE lists (
                    id integer primary key,
                    content text,
                    priority integer,
                    last_modified real,
                    created real,
                    hash_id varchar(64)
                    );
INSERT INTO "lists" VALUES(1,'new_list',1,1308853439.2884,1308853439.28822,'nohash');
INSERT INTO "lists" VALUES(2,'list1',1,1308853467.51665,1308853467.51649,'nohash');
CREATE TABLE tags (
                    id integer primary key,
                    content text,
                    priority integer,
                    last_modified real,
                    created real,
                    hash_id varchar(64)
                    );
INSERT INTO "tags" VALUES(1,'new_tag',1,1308853446.93442,1308853446.93426,'nohash');
INSERT INTO "tags" VALUES(2,'tag1',1,1308853460.08829,1308853460.08813,'nohash');
CREATE TABLE tasks (
                    id integer primary key,
                    content text,
                    parent integer references tasks(id) on delete cascade,
                    priority int,
                    due_date real,
                    list integer references lists(id) on delete cascade,
                    completed integer,
                    last_modified real,
                    created real,
                    hash_id varchar(64)
                );
INSERT INTO "tasks" VALUES(1,'new task',NULL,1,0,NULL,0,1308853429.28504,1308853429.28502,'nohash');
CREATE TABLE notes (
                    id integer primary key,
                    content text,
                    task integer references tasks(id) on delete cascade,
                    last_modified real,
                    created real,
                    hash_id varchar(64)
                );
CREATE TABLE tagging (
                    tag integer references tags(id) on delete cascade,
                    task integer references tasks(id) on delete cascade
                    );
CREATE TABLE metadata (
                    key varchar(30),
                    value varchar(128)
                    );
INSERT INTO "metadata" VALUES('version','0.2');

