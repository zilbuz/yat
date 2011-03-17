
import lib

class Task:
    children_id = {}

    def __init__(self, sql_line, lib):
        u"""Constructs a Task from an sql entry and an instance of Yat
        """
        self.id = sql_line["id"]
        self.parent_id = sql_line["parent"]

        if self.parent_id not in Task.children_id:
            Task.children_id[self.parent_id] = (None, [])
        self.parent = Task.children_id[self.parent_id]
        if self.id not in Task.children_id[self.parent_id][1]:
            Task.children_id[self.parent_id][1].append(self.id)

        self.content = sql_line["task"]
        self.due_date = sql_line["due_date"]
        self.priority = sql_line["priority"]
        self.list = lib.get_list(sql_line["list"])
        self.tags = lib.get_tags([int(i) for i in sql_line[tags].split(",")])
        self.completed = sql_line["completed"]
        self.last_modified = sql_line["last_modified"]
        self.created = sql_line["created"]

