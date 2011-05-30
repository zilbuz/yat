=======
  yat
=======

---------------------------------------------
simple command line todolist manager.
---------------------------------------------

:Author: yat developers <yat-devel@freelist.org>
:Date:   2011-05-30
:Copyright: WTFPL v2
:Version: 0.1
:Manual section: 1
:Manual group: organisational tool

SYNOPSIS
========

    yat OPTIONS [<command> [<args>]]

DESCRIPTION
===========

yat is a simple command line todolist manager, written in python.

OPTIONS
=======
--config-file=<file>
    Read configuration settings from <file> instead of the default \fI~/.yatrc\fP

--version, -v
    Show this program\(aqs version number and exit.

--help, -h
    Show this help message and exit.

COMMANDS
========

For detailled destruction of the command, please run \fIyat help <cmd>\fP
When no command is provided, the default is to run \fIyat show\fP, thus displaying
the tasks of the todolist.

yat add <args>
--------------
This command is used to add elements to the todolist. It can be a new task,
a new list, or a new tag.
    
yat rm <args>
-------------
Use the rm command to remove objects from the list.

yat edit <args>
---------------
Edit an element of the list.

yat show <args>
---------------
yat ls <args>
-------------
Display elements from the todolist.

yat done <args>
---------------
yat undone <args>
-----------------
Mark tasks done, resp undone.

yat clean
---------
Remove the tasks marked as done.

yat help <cmd>
    Display help for the given command

