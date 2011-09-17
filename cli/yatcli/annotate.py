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
import os
import re
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
        self.encodings = [u'windows-1252', u'utf8', u'latin9']

    def split_notes(self, temp_file, separator):
        u'''Given a file and the separator, split the content of the file into
        a list of string. The separator must be a whole line.'''
        notes = []
        current_note = StringIO()
        for line in temp_file:
            if self.to_unicode(line.strip()) == separator.strip():
                content = current_note.getvalue()
                length = len(os.linesep)
                if len(content) > length:
                    if content[-1] != '\n':
                        content = content + os.linesep
                    notes.append(content)
                current_note.close()
                current_note = StringIO()
            else:
                current_note.write(line)
        content = current_note.getvalue()
        length = len(os.linesep)
        if len(content) > length:
            if content[-1] != '\n':
                content = content + os.linesep
            notes.append(content)
        return notes

    def to_unicode(self, string):
        u'''
        Translates an 8-bytes string into a unicode string even
        on Windows despite its brokenness.
        '''
        try:
            #try the default decoding. Usually works
            return unicode(string)
        except UnicodeDecodeError as error:
            #If not, try the usual suspects.
            for enc in self.encodings:
                try:
                    return unicode(string, enc)
                except UnicodeDecodeError:
                    continue
            raise error

    def to_8bytes(self, unicode_string):
        u'''Return an 8-byte string from a unicode one. It tries the default
        encoding first, and then switch to the usual suspects if needed.'''
        try:
            #try the default encoding. Usually works
            return unicode_string.encode()
        except UnicodeEncodeError as error:
            #If not, try the usual suspects.
            for enc in self.encodings:
                try:
                    return unicode_string.encode(enc)
                except UnicodeDecodeError:
                    continue
            raise error

    #pylint: disable=E1101
    def fetch_notes(self, task):
        u'''Retrieve the notes to edit.'''
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
                exit()
        else:
            notes = []
        return notes

    def execute(self, cmd):
        # Get the task
        try:
            task = lib.get_task(self.task_id)
        except WrongId:
            write("[ERR] The specified task doesn't exist",
                output_file = sys.stderr,
                color = (Colors.errf, Colors.errb), bold = Colors.errbold)
            return

        notes = self.fetch_notes(task)

        # Launch an editor
        separator = u'==================================================' + \
            os.linesep
        if notes or not (self.edit_ids or self.edit_all):
            with NamedTemporaryFile(delete=False) as temp_file:
                # Write the notes fetched earlier
                for note in notes:
                    if note != notes[0]:
                        temp_file.write(separator)
                    if os.name == 'nt':
                        to_write = re.sub('(?<!\r)\n', os.linesep, note.content)
                    else:
                        to_write = note.content
                    temp_file.write(self.to_8bytes(to_write))
                temp_file.close()

                # Launch the editor
                if os.name == 'nt':
                    exec_name = 'notepad.exe'
                else:
                    exec_name = 'sensible-editor'
                call([exec_name, temp_file.name])

                # Get the modifications.
                modified_file = open(temp_file.name)
                new_notes = self.split_notes(modified_file, separator)
                modified_file.close()
                os.remove(temp_file.name)

            # In case of an edition, replace the content of the notes fetched
            # by the new ones.
            if self.edit_ids:
                array_ids = self.edit_ids.split(',')
                for note_id, content in zip(array_ids, new_notes):
                    task.notes[int(note_id)-1].content = \
                        self.to_unicode(content)
            elif self.edit_all:
                for note, content in zip(task.notes, new_notes):
                    note.content = self.to_unicode(content)

            # Just append the new notes to the existing ones.
            else:
                for note in new_notes:
                    temp_note = Note(lib)
                    temp_note.content = self.to_unicode(note)
                    temp_note.task = task
                    task.notes.append(temp_note)
            task.save()
    #pylint: enable=E1101
