#!/usr/bin/env python
#-*- coding:utf-8 -*-

u"""
Very simple command line todolist manager
"""

import inspect
import locale
import os
import re
import sqlite3
import string
import sys

class Command:
    u"""Abstract class for instrospection
    
If you wish to add a command, you have to create a class that derive from this
one, and the docstring must have this format:
Short description

usage: %s cmd_name [options]

Long description
"""
    
    alias = []
    u"""Array containing the different aliases for this command"""

    def execute(self,args):
        u"""Method actually doing something"""
        raise NotImplementedError

    pass

class HelpCommand (Command):
    u"""Show this help or a command specific help if an argument is provided

usage: %s help [command]

Without arguments, provide a short description of the differents commands. If
the name of a command is provided, show the specific help text for this command.
"""

    alias = [u"help"]

    def execute(self,args):
        global progname, aliases, commands

        detailed = False
        cmd = self

        if len(args) > 0:
            if args[0] in aliases:
                cmd = aliases[args[0]]()
                detailed = True

        helptxt = cmd.__doc__.split('\n\n', 1)

        if detailed:
            output(helptxt[1] % progname)

        if cmd.alias[0] == u"help":
            if not detailed:
                output(st = (u"%s (Yet Another Todolist) is a very simple " %
                    progname), linebreak = False)
                output(u"commandline todolist manager.")
                output()
                output(u"usage: %s [command] [arguments]" % progname)
                output()

            output(u"The different commands are:")
            for name, cmd in commands.iteritems():
                output(u"\t", linebreak = False)
                output(cmd.alias[0], linebreak = False)
                output(u"\t", linebreak = False)
                output(cmd.__doc__.split('\n',1)[0], linebreak = False)
                if len(cmd.alias) > 1:
                    output(u" (alias: ", linebreak = False)
                    for i in range(1, len(cmd.alias)):
                        output(cmd.alias[i], linebreak = False)
                        if i < len(cmd.alias) - 1: 
                            output(u",", linebreak = False)
                    output(u")", linebreak = False)
                output()
            output()
            output(u"Please type \"%s help [command]\" to have" % progname, 
                    linebreak = False)
            output(u" detailed informations on a specific command")

        output()
        pass
    pass

class AddCommand (Command):
    u"""Add a task, a list or a tag

usage: %s add [task | list | tag] "<informations>"

Add a task, a list or a tag to the todolist, depending of the first argument
after "add". If the first argument after "add" isn't one of these, then "task"
is assumed.

Adding a task:
    When adding a task, you must provide the task's text, and optionnally some
    symbols to set the priority, due date, tags or list. The symbols are '*',
    '^', '#' and '>'.

    '*' can be used to set the priority of the task, it must be followed by a number
    between 0 and 3. 
    Example: yat add "do the laundry *2".

    '^' can be used to set the due date of the task, it must be followed by a
    date of the form dd/mm/yyyy. 
    Example: yat add "go to the cinema with Wendy ^12/02/2011".

    '#' can be used to set the tags of the task, it must be followed by the name
    of a tag. The tag name can be composed of anything but spaces. You can set 
    multiple tags for a task. If the tag doesn't exist, it will be created.
    Example: yat add "do my homework #work #important"

    '>' can be used to set the list of the task, it must be followed by the name
    of a list. The list name can be composed of anything but spaces. If the list
    doesn't exist, it will be created.
    Example: yad add "peanut butter >groceries"

    Apart for the tags, if a symbol is used more than one time for a task, the
    last one will be used.
    You can place the symbols anywhere in the task text.
    You can escape the symbols with \, for example: "the symbol \> won't be
    processed with this text". And of course, you also have to escape \ if you
    want to use it.
    If your task text uses none of the symbols that the shell can interpret, the
    double quotes are optionnal.

Adding a list:
    Just add a new list. The name can contain anything but spaces.
    Example: yat add list groceries

Adding a tag:
    Just add a new tag. The name can contain anything but spaces.
    Example: yat add tag work
"""
    
    alias = [u"add"]

    def __init__(self):
        self.re_priority = re.compile("^\*(\d)$")
        u"""Regex for the priorty"""

        self.re_tag = re.compile("^#(.*)$")
        u"""Regex for the tags"""

        self.re_list = re.compile("^>(.*)$")
        u"""Regex for the list"""

        self.re_date = re.compile("^\^(\d\d/\d\d/\d{4})$")
        u"""Regex for the date"""

    def execute(self,args):
        global sql, config
        # Separate words
        args = (" ".join(args)).split(" ")

        cmd = ""
        if args[0] in ["task", "list", "tag"]:
            cmd = args[0]
            args = args[1:]

        # Process command
        if cmd in ["tag", "list"]:
            self.__add_tag_or_list(cmd + "s", args[0])
            pass
        else:
            # Init params
            priority = ""
            tags = []
            list = ""
            date = ""
            text = []
            # Look for symbols
            for a in args:
                symbol = False
                # Priority
                res = self.re_priority.match(a)
                if res != None:
                    priority = int(res.group(1))
                    symbol = True
                # Tags
                res = self.re_tag.match(a)
                if res != None:
                    tags.append(res.group(1))
                    symbol = True
                # List
                res = self.re_list.match(a)
                if res != None:
                    list = res.group(1)
                    symbol = True
                # Date
                res = self.re_date.match(a)
                if res != None:
                    date = res.group(1)
                    symbol = True

                # Regular text
                if not symbol:
                    text.append(a)

            if priority == "":
                priority = config["default_priority"]
            elif priority > 3:
                priority = 3

            if tags == []:
                tags.append(config["default_tag"])
            tags_copy = []
            for t in tags:
                self.__add_tag_or_list("tags", t)
                tags_copy.append(self.__get_id("tags", t))
            tags = ",".join(tags_copy) + u','   # Needed to properly remove the tags

            if list == "":
                list = config["default_list"]
            self.__add_tag_or_list("lists", list)
            list = self.__get_id("lists", list)

            text = " ".join(text)

            # Add the task with the correct parameters
            with sql:
                sql.execute('insert into tasks values(null, ?, ?, ?, ?, ?)',
                        (text.decode('utf-8'), priority, date, tags, list))
            pass
        pass

    def __add_tag_or_list(self, table, name):
        u"""Add an element "name" to the "table" if it doesn't exist. It is
        meant to be used with table="lists" or table="tags" """
        global sql
        with sql:
            c = sql.execute('select count(*) as nb from %s where name=?' %
                    table, (name,))
            if c.fetchone()[0] == 0:
                sql.execute('insert into %s values(null, ?)' % table, (name,))
                sql.commit()

    def __get_id(self, table, name):
        u"""Get the id of the element "name" in "table". It's meant to be used
        with table = "lists" or "tags" """
        global sql
        with sql:
            res = sql.execute('select id from %s where name=?' % table, (name,))
            return str(res.fetchone()[0])
    pass
    

class RemoveCommand (Command):
    u"""Remove a task, a list or a tag

usage: %s remove [task | list | tag] <informations>

The use is straightforward : every element matching the
informations gets deleted.

The informations can be either a number or a regexp. The number
is compared to the id of the elements to delete (task, list or tag),
whereas the regexp is compared to the name or the title.
"""

    alias = [u"remove", u"rm"]

    def execute(self,args):
        # TODO
        global sql

        # Separate words
        args = (" ".join(args)).split(" ")

        cmd = ""
        if args[0] in [u"task", u"list", u"tag"]:
            cmd = args[0]
            args = args[1:]
        else:
            cmd = u"task"

        re_number = re.compile("^[0-9]+$")

        operation = u""
        identifier = u""
        for a in args:
            if re_number.match(a) is not None:
                operation = u"="
                identifier = u"id"
            else:
                operation = u" regexp "

                # Test if this is a valid regexp
                try:
                    re.findall(a, "test")
                except Exception:
                    print "The given expression is not a valid REGEXP."
                    print "Please be aware of the difference with the usual shell expressions, especially for the *"
                    raise
                if cmd == u"task"w
                    identifier = cmd
                else:
                    identifier = u"name"

            if cmd != u'task':
                ids = []
                if operation == u'=':
                    ids = [a, ]
                else:
                    temp = sql.execute(u'select id from {0} where name regexp ?'.format(cmd+u's'), (a, )).fetchall()
                    for t in temp:
                        ids.append(str(t[0]))

                # Removing the tasks belonging to the list
                if cmd == u'list':
                    for i in ids:
                        sql.execute(u'delete from tasks where list=?', (i, ))
                # Updating the tag list for the concerned tags.
                else:
                    for i in ids:
                        sql.execute(u'update tasks set tags = replace(tags, "{0}", "") ;'.format(i+u',' )) 
                        sql.execute(u'update tasks set tags = "1," where tags = ""')      # Attributes the notag tag
                        sql.commit()



            # Final cleanup
            sql.execute('delete from {0} where {1}{2} ?'.format(cmd+u's', identifier, operation), (a, ))
            sql.commit()

        # print self.__doc__.split('\n',1)[0]," ",args

class ListCommand (Command):
    u"""List the current tasks

usage: %s list
"""

    alias = [u"list", u"show"]

    def execute(self,args):
        global sql
        # TODO
        with sql:
            print "tasks:"
            for r in sql.execute("""select * from tasks"""):
                print "\t",r
            print "lists:"
            for r in sql.execute("""select * from lists"""):
                print "\t",r
            print "tags:"
            for r in sql.execute("""select * from tags"""):
                print "\t",r
        pass
    pass


def init():
    u"""Initialisation of the program
    - loading user preferences
    - initialising database access
    - initializing some global vars
    """
    global enc, out, config, sql

    # Default encoding
    enc = locale.getpreferredencoding()

    # Default output : stdout
    out = sys.stdout

    # Loading configuration
    config = {}
    try:
        with open(os.environ.get("HOME") + "/.yatrc", "r") as config_file:
            for line in config_file:
                if not (re.match(r'^\s*#.*$', line) or re.match(r'^\s*$', line)):
                    line = re.sub(r'\s*=\s*', "=", line, 1)
                    line = re.sub(r'\n$', r'', line)
                    opt = line.split('=', 1)
                    config[opt[0]] = opt[1]
        config_file.close()
    except IOError:
        # No .yatrc
        pass

    # For each option, loading default if it isn't defined
    config["yatdir"] = config.get("yatdir", "~/.yat")
    config["default_list"] = config.get("default_list", "nolist")
    config["default_tag"] = config.get("default_tag", "notag")
    config["default_priority"] = config.get("default_priority", "1")

    # Create yat directory
    if config["yatdir"][0] == "~":
        config["yatdir"] = os.environ.get("HOME") + config["yatdir"][1:]
    if not os.path.isdir(config["yatdir"]):
        os.makedirs(config["yatdir"], mode=0700)

    # Connect to sqlite db
    sql = sqlite3.connect(config["yatdir"] + "/yat.db")
    try:
        with sql:
            sql.execute("select * from tags")
    except sqlite3.OperationalError:
        # Create tables
        with sql:
            sql.execute("""
                create table tasks (
                    id integer primary key,
                    task text,
                    priority int,
                    due_date text,
                    tags text,
                    list text
                )""")
            sql.execute("""
                create table tags (
                    id integer primary key,
                    name text
                    )""")
            sql.execute("""
                create table lists (
                    id integer primary key,
                    name text
                    )""")
            sql.execute("""insert into tags values (null, "notag")""")
            sql.execute("""insert into lists values (null, "nolist")""")
            sql.commit()
    pass

    # Add support for the REGEXP() operator
    def regexp(expr, item):
        r = re.findall(expr,item)
        return len(r) == 1 and r[0] == item
    sql.create_function("regexp", 2, regexp)


def isCommand(obj):
    u"""Check if the parameter is a class derived from Command, without being
    Command"""

    if inspect.isclass(obj):
        return (issubclass(obj, Command) and not(obj is Command))
    else:
        return False

def output(st = u"", f = None, linebreak = True):
    global enc, out
    if f == None:
        f = out
    f.write(st.encode(enc))
    if linebreak:
        f.write(os.linesep)

def main(argv):
    u"""
    Entry point of the program
    """
    global commands, aliases, progname

    # Initialisation
    init()

    # Getting the name of the program
    progname = argv[0]

    # Getting all the commands
    commands = dict(inspect.getmembers(sys.modules[__name__], isCommand))
    aliases = {}

    # Fill the aliases dictionnary
    for name, cmd in commands.iteritems():
        for a in cmd.alias:
            aliases[a] = cmd

    # Determining which command to use (default list)
    cmd = ListCommand()
    cmd_args = []
    if len(argv) > 1:
        if argv[1] in aliases:
            cmd = aliases[argv[1]]()
            cmd_args = argv[2:]
        else:
            cmd = AddCommand()
            cmd_args = argv[1:]

    # Executing command with the rest of the arguments
    cmd.execute(cmd_args)

if __name__ == "__main__":
    main(sys.argv)
