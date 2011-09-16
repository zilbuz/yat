PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE lists (
                    id integer primary key,
                    content text,
                    priority integer,
                    last_modified real,
                    created real,
                    hash_id varchar(64)
                    );
INSERT INTO "lists" VALUES(1,'list1',-5,1311248581.889,1311246275.135,'nohash');
INSERT INTO "lists" VALUES(2,'list2',1,1311248581.585,1311246349.434,'nohash');
CREATE TABLE tags (
                    id integer primary key,
                    content text,
                    priority integer,
                    last_modified real,
                    created real,
                    hash_id varchar(64)
                    );
INSERT INTO "tags" VALUES(1,'tag1',1,1308853460.08829,1308853460.08813,'nohash');
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
INSERT INTO "tasks" VALUES(1,'task1',NULL,1,NULL,NULL,0,1311248581.995,1311248538.503,'nohash');
INSERT INTO "tasks" VALUES(2,'task2',1,3,NULL,NULL,0,1311248550.848,1311248545.489,'nohash');
INSERT INTO "tasks" VALUES(3,'task3',2,2,NULL,NULL,0,1311248550.969,1311248550.969,'nohash');
INSERT INTO "tasks" VALUES(4,'task4',1,1,NULL,1,0,1311248582.106,1311248557.427,'nohash');
INSERT INTO "tasks" VALUES(5,'task5',4,1,NULL,1,0,1311248582.223,1311248563.906,'nohash');
INSERT INTO "tasks" VALUES(6,'task6',5,1,NULL,1,0,1311248582.318,1311248569.558,'nohash');
INSERT INTO "tasks" VALUES(7,'task7',6,1,NULL,2,0,1311248582.418,1311248576.098,'nohash');
INSERT INTO "tasks" VALUES(8,'task8',7,1,NULL,2,0,1311248582.539,1311248582.539,'nohash');
INSERT INTO "tasks" VALUES(9,'task9',8,1,NULL,NULL,0,1311248582.539,1311248582.539,'nohash');
INSERT INTO "tasks" VALUES(10,'task10',9,1,NULL,NULL,0,1311248582.539,1311248582.539,'nohash');
INSERT INTO "tasks" VALUES(11,'task11',7,1,NULL,2,0,1311248582.539,1311248582.539,'nohash');
INSERT INTO "tasks" VALUES(12,'task12',11,1,NULL,NULL,0,1311248582.539,1311248582.539,'nohash');
INSERT INTO "tasks" VALUES(13,'atask13',7,1,NULL,2,0,1211348961.432,1201236487.432, 'nohash');
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
INSERT INTO "tagging" VALUES(1,2);
CREATE TABLE metadata (
                    key varchar(30),
                    value varchar(128)
                    );
INSERT INTO "metadata" VALUES('version','0.2');
COMMIT;
