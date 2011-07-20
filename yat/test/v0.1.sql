CREATE TABLE tasks (
                        id integer primary key,
                        task text,
                        priority int,
                        due_date real,
                        tags text,
                        list text,
                        completed integer,
                        last_modified real,
                        created real
                    );
INSERT INTO "tasks" VALUES(1,'task1',1,null,'2','2',0,1308606495.15304,1308606495.15304);
INSERT INTO "tasks" VALUES(2,'task2',2,1297537200.0,'1','1',0,1308607391.7593,1308607391.7593);
INSERT INTO "tasks" VALUES(3,'task3',1,null,'2,3','1',0,1308607652.28616,1308607652.28616);
CREATE TABLE tags (
                        id integer primary key,
                        name text,
                        priority integer,
                        last_modified real,
                        created real
                        );
INSERT INTO "tags" VALUES(1,'notag',-1,1308606495.14419,1308606495.14419);
INSERT INTO "tags" VALUES(2,'tag1',0,1308606495.15004,1308606495.15005);
INSERT INTO "tags" VALUES(3,'tag2',0,1308607652.24592,1308607652.24593);
INSERT INTO "tags" VALUES(4,'tag3',4,1308610844.3672,1308610844.36721);
CREATE TABLE lists (
                        id integer primary key,
                        name text,
                        priority integer,
                        last_modified real,
                        created real
                        );
INSERT INTO "lists" VALUES(1,'nolist',-1,1308606495.14431,1308606495.14431);
INSERT INTO "lists" VALUES(2,'list1',0,1308606495.1516,1308606495.1516);
INSERT INTO "lists" VALUES(3,'list2',-2,1308610867.82455,1308610867.82456);
