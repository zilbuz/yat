#-*- coding:utf-8 -*-

u"""
The Task, List, Note and Tag classes

           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
                   Version 2, December 2004 

 Copyright (C) 2010, 2011
    Basile Desloges <basile.desloges@gmail.com>
    Simon Chopin <chopin.simon@gmail.com>

 Everyone is permitted to copy and distribute verbatim or modified 
 copies of this license document, and changing it is allowed as long 
 as the name is changed. 

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION 

  0. You just DO WHAT THE FUCK YOU WANT TO. 

This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
http://sam.zoy.org/wtfpl/COPYING for more details.
"""

from yat.exceptions import WrongId, IncoherentObject, WrongName

#pylint: disable=R0903
class DBObject(object):
    u"""Describes the basis of all the objects having a DB representation."""
    class_lib = None

    def __setattr__(self, attr, value):
        u'''When changing an attribute, memorize it.'''
        super(DBObject, self).__setattr__('changed', True)
        super(DBObject, self).__setattr__(attr, value)

    def __init__(self, lib):
        self.lib = lib
        if DBObject.class_lib == None:
            DBObject.class_lib = self.lib
        elif self.lib == None:
            self.lib = DBObject.class_lib

        #pylint: disable=C0103
        self.id = None
        #pylint: enable=C0103
        self.content = None
        self.created = 0
        self.hash = None
        self.last_modified = 0
#pylint: enable=R0903

#pylint: disable=R0902
class Task(DBObject):
    u'''This class describe a task in a OO perspective
    '''

    def __init__(self, lib):
        u"""Constructs a Task from an sql entry and an instance of Yat
        """
        super(Task, self).__init__(lib)
        # Creation of a blank Task
        self.parent = None
        self.due_date = None
        self.priority = None
        self.list = NoList(self.lib)
        self.tags = set()
        self.completed = 0
        self.changed = False
        self.notes = []

    def check_values(self, lib = None):
        u'''Checks the values of the object, and correct them
        if needed by using the default values provided by lib.
        '''
        if lib == None:
            lib = self.lib
        if self.priority == None:
            if self.parent != None:
                self.priority = self.parent.priority
            else:
                self.priority = lib.config["default_priority"]
        elif self.priority > 3:
            self.priority = 3

        for tag in self.tags:
            tag.check_values(lib)

        self.list.check_values(lib)

        if self.due_date == None:
            if self.parent == None:
                self.due_date = lib.config["default_date"]
            else:
                self.due_date = self.parent.due_date

        if self.created <= 0:
            self.created = lib.get_time()

        if self.completed == True or self.completed == 1:
            self.completed = 1
        else:
            self.completed = 0

    def save(self, lib = None):
        u'''Ensure that all the task's dependencies have been saved, and
then save itself into the lib.

Here, save can mean creation or update of an entry.
If lib isn't the lib specified at the creation of the object, it will
automatically create a new task.
The return value is always None.'''
        if lib == None:
            lib = self.lib
        elif lib != self.lib:
            #pylint: disable=C0103
            self.id = None
            #pylint: enable=C0103

        new_list = self.list.save(lib)
        if new_list != None:  # The list has been replaced in the new lib
            self.list = new_list

        to_remove = set()
        to_add = set()
        for tag in self.tags:
            new_tag = tag.save(lib)
            if new_tag != None:  # The tag has been replaced in the new lib
                to_add.add(new_tag)
                to_remove.add(new_tag)
        self.tags -= to_remove
        self.tags |= to_add

        #TODO: Do it cleanly !
        for note in self.notes:
            note.save(lib)

        if self.parent != None:
            new_parent = self.parent.save(lib)
            # It shouldn't happen, but better safe than sorry
            if new_parent != None:
                self.parent = new_parent
        #pylint: disable=W0212
        # The access to the protected functions is deliberate,
        # it was meant like that.
        if self.id == None:
            save_function = lib._add_task
        else:
            save_function = lib._edit_task
        #pylint: enable=W0212
        save_function(self)
        self.lib = lib
        return None

    def __str__(self):
        retour = "Task "
        retour += str(self.id)
        return retour

    def parents_in_group(self, group):
        u"""Returns True if at least one parent of self is in the group,
        False otherwise."""
        return (self.parent != None and
                (group.directly_related_with(self.parent) or
                 self.parent.parents_in_group(group)))

    def get_list_parents(self):
        u"""Returns a list of all the parents of self, beginning with the
        root ancestor."""
        if self.parent == None:
            return []
        parent_list = self.parent.get_list_parents()
        parent_list.append(self.parent)
        return parent_list
#pylint: enable=R0902

class Note(DBObject):
    u'''The python representation of a task annotation.'''
    def __init__(self, lib):
        super(Note, self).__init__(lib)
        self.task = None
        self.changed = False

    def save(self, lib):
        u'''Update or create the note into the lib/db'''
        if lib == None:
            lib = self.lib
        self.check_values(lib)
        if lib != self.lib:
            try:
                return lib.get_note(self.task, self.content, False)
            except WrongName:
                #pylint: disable=C0103
                self.id = None
                #pylint: enable=C0103
            except WrongId:
                raise IncoherentObject('A note must be associated to \
                                        an existing task.')
        #pylint: disable=W0212
        if self.id == None:
            lib._add_note(self)
        elif self.changed:
            lib._edit_note(self)
        #pylint: enable=W0212
        self.lib = lib
        return None

    def check_values(self, lib = None):
        u"""Check if the attributes of the note are valid."""
        if self.task == None:
            raise IncoherentObject('A note must be associated to a task.')
        if lib == None:
            lib = self.lib

        if self.created <= 0:
            self.created = self.lib.get_time()

#pylint: disable=R0903
class Group(DBObject):
    u'''Abstraction for the tags and the lists.'''
    def __init__(self, lib):
        u"""Constructs a group from an sql row"""
        super(Group, self).__init__(lib)
        self.priority = None
        self.changed = False

    def check_values(self, lib = None):
        u"""Check if the attributes of the group are valid."""
        if lib == None:
            lib = self.lib

        if self.priority == None:
            self.priority = lib.config["default_priority"]

        if self.created <= 0:
            self.created = self.lib.get_time()

    def _save(self, lib, getter):
        u'''Update or create the group into the lib/db'''
        if lib == None:
            lib = self.lib
        self.check_values(lib)
        if lib != self.lib:
            try:
                return getter(self.content, False)
            except WrongName:
                #pylint: disable=C0103
                self.id = None
                #pylint: enable=C0103
        #pylint: disable=W0212
        if self.id == None:
            lib._add_group(self)
        elif self.changed:
            lib._edit_group(self)
        #pylint: enable=W0212
        self.lib = lib
        return None
#pylint: enable=R0903

class List(Group):
    u'''This class represent the "meta-data" of a list.
    It is NOT a container !'''
    table_name = 'lists'

    def __init__(self, lib):
        u"""Constructs an empty List."""
        super(List, self).__init__(lib)

    def __str__(self):
        retour = "List " + str(self.id)
        return retour

    def save(self, lib=None):
        u'''Saves the Tag instance into the DB represented by lib, or
        the one referenced by the instance.'''
        if lib == None:
            lib = self.lib
        return self._save(lib, lib.get_list)

class Tag(Group):
    u'''This class represent the "meta-data" of a tag.
    It is NOT a container !'''
    table_name = 'tags'

    def __init__(self, lib):
        u"""Constructs an empty Tag."""
        super(Tag, self).__init__(lib)

    def save(self, lib=None):
        u'''Saves the Tag instance into the DB represented by lib, or
        the one referenced by the instance.'''
        if lib == None:
            lib = self.lib
        return self._save(lib, lib.get_tag)

#pylint: disable=W0613
class NoGroup(object):
    u'''Bogus class used to represent the absence of groups.'''
    def __init__(self, lib):
        #pylint: disable=C0103
        self.id = None
        #pylint: enable=C0103
        self.lib = lib

    def save(self, lib = None):
        u'''Bogus function.'''
        pass

    def check_values(self, lib = None):
        u'''Bogus function.'''
        pass

class NoList(NoGroup, List):
    u'''Bogus specialization for the List class counterpart.'''
    # List provides unique algorithms, but here we override its
    # polymorphism abilities
    __mro__ = (NoGroup, Group, DBObject, object, List)
    __instance = None
    def __new__(cls, lib):
        if cls.__instance == None:
            cls.__instance = super(NoList, cls).__new__(cls)
        return cls.__instance

    def __init__(self, lib):
        super(NoList, self).__init__(lib)

class NoTag(NoGroup, Tag):
    u'''Bogus specialization for the Tag class counterpart.'''
    # Same as for NoList's MRO.
    __mro__ = (NoGroup, Group, object, Tag)
    __instance = None

    def __new__(cls, lib):
        if cls.__instance == None:
            cls.__instance = super(NoTag, cls).__new__(cls)
        return cls.__instance

    def __init__(self, lib):
        super(NoTag, self).__init__(lib)
#pylint: enable=W0613
