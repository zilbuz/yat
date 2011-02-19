yat - Yet Another Todolist
==========================

Yat is a very simple commandline todolist manager.

Installation
------------

Just clone the repository somewhere in your computer.
`git clone git://github.com/Zilbuz/yat.git`

Then if you want, you can load the development branch by doing 
`git checkout dev` in the yat folder.

Finally, create a symbolic link to yat.py in a path directory. For example:
`ln -s /path/to/yat/yat.py /usr/local/bin/yat`

How to use
----------

Simply type `yat help` to have the list of all available commands, and `yat
help <cmd>` to get the documentation of the specific <cmd>.

The most common commands are:

*   `yat add "some task"`

    Simply add a task to your todolist. It will be added in a default list and
    default tag. You can specify a priority, a due date, some tags and a list
    with symbols in the text of your task. See `yat help add` for a complete
    list of these symbols.

    You can also add lists or tags with this command. Again, see `yat help add`
    for detailed instructions.

*   `yat remove "some task"` or `yat remove id=2`

    The first command will remove the task(s) with the name some task, while the
    second command will remove the task with the id 2. When entering the name of
    the task, you can use * as a joker for any number of any character, and ? as
    a joker for one occurence of any character.

*   `yat done "some task"` or `yat done id=2`

    This command will mark a task as done. The mean to identify which task to
    mark is like the "remove" command.

*   `yat clean`

    Delete all completed tasks.


Configuration file
------------------

All the available options for yat are described in the file `yatrc.sample`
provided in the repository. To customize yat, simply create a file named
`.yatrc` in your home and fill it with the options you want to customize, or
copy paste the `yatrc.sample` file and modify the options. If you don't specify
an option, the default value will be used.

