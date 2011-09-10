#-*- coding:utf-8 -*-

u"""
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

from StringIO import StringIO
from tempfile import SpooledTemporaryFile

from yatcli import lib, write
from yatcli.command import Command
from yatcli.exceptions import WrongId

class AnnotateCommand (Command):
    u"""

    
    x est l'id d'une note, y z v w  sont des ids de note
    yat note x
    yat note -e y,z,v,w x
    yat note -a x

    -d v,w,z -> delete
    -C -> clear
    -m "bla bla ma note"

    """

    alias = [u"annotate, note"]

    def __init__(self):
        super(AnnotateCommand, self).__init__()

        self.options = [
            ('e', 'edit', 'edit_ids', str),
            ('a', 'all', 'edit_all', None),
            ('d', 'delete', 'delete_ids', str),
            ('C', 'clear', 'clear', None),
            ('m', 'message', 'message', str)
        ]
        
        self.arguments = (['task_id'], {
            'task_id':       ('^({0})$'.format(lib.config["re.id"]),
                         [None], 'task_id')
        })

    def split_notes(temp_file, separator):
        u'''Given a file and the separator, split the content of the file into
        a list of string. The separator must be a whole line.'''
        notes = []
        current_note = StringIO()
        for line in temp_file:
            if line == separator:
                notes.append(current_note.getvalue())
                current_note.close()
                current_note = StringIO()
            else:
                current_note.write(line)
        notes.append(current_note.getvalue())
        return notes

    #pylint: disable=E1101
    def execute(self, cmd):
        # Get the task
        try:
            task = lib.get_task(self.task_id)
        except WrongId:
            write("[ERR] The specified task doesn't exist",
                output_file = sys.stderr,
                color = (Colors.errf, Colors.errb), bold = Colors.errbold)
            return

        # Retrieve the notes to edit
        if self.edit_all:
            notes = task.notes
        elif self.edit_ids:
            array_ids = edit_ids.split(",")
            try:
                notes = lib.get_notes(task = task, ids = array_ids)
            except WrongId:
                # TODO : which id ?
                write("[ERR] At least one of the ids doesn't exist",
                    output_file = sys.stderr,
                    color = (Colors.errf, Colors.errb), bold = Colors.errbold)
                return

        # Launch an editor
        if notes:
            # TODO
            pass

        
    #pylint: enable=E1101
