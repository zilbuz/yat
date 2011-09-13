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

import sys
from StringIO import StringIO
from tempfile import NamedTemporaryFile
from subprocess import call

from yatcli import lib, write, Colors
from yatcli.command import Command
from yat.exceptions import WrongId
from yat.models import Note

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

    alias = [u"annotate", "note"]

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

    @staticmethod
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
        notes = []
        if self.edit_all:
            notes = task.notes
        elif self.edit_ids:
            array_ids = [int(i) for i in self.edit_ids.split(",")]
            try:
                notes = lib.get_notes(task = task, ids = array_ids)
            except WrongId:
                # TODO : which id ?
                write("[ERR] At least one of the ids doesn't exist",
                    output_file = sys.stderr,
                    color = (Colors.errf, Colors.errb), bold = Colors.errbold)
                return

        # Launch an editor
        separator = u'==================================================\n'
        if notes or not (self.edit_ids or self.edit_all):
            with NamedTemporaryFile(delete=False) as temp_file:
                for note in notes:
                    if note != notes[0]:
                        temp_file.write(separator)
                    temp_file.write(note.content)
                temp_file.close()
                call(['sensible-editor', temp_file.name])
                modified_file = open(temp_file.name)
                new_notes = self.split_notes(modified_file, separator)
                modified_file.close()
            if self.edit_ids or self.edit_all:
                array_ids = self.edit_ids.split(',')
                for note_id, note in zip(array_ids, new_notes):
                    task.notes[int(note_id)-1].content = note
            else:
                for note in new_notes:
                    temp_note = Note(lib)
                    temp_note.content = note
                    temp_note.task = task
                    task.notes.append(temp_note)
            task.save()
    #pylint: enable=E1101
