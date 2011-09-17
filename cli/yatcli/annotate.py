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
            ('e', 'edit', 'ids_to_edit', self.__analyze_ids, ['a', 'd', 'C', 'm']),
            ('a', 'all', 'edit_all', None, ['e', 'd', 'C', 'm']),
            ('d', 'delete', 'delete_ids', str, ['a', 'e', 'C', 'm']),
            ('C', 'clear', 'clear', None, ['a', 'd', 'e', 'm']),
            ('m', 'message', 'message', str, ['a', 'd', 'C', 'e'])
        ]
        
        self.arguments = (['task_id'], {
            'task_id':       ('^({0})$'.format(lib.config["re.id"]),
                         [None], 'task_id')
        })
        self.encodings = [u'windows-1252', u'utf8', u'latin9']
        self.separator = \
            u'==================================================' + os.linesep

    @staticmethod
    def __analyze_ids(csv_ids):
        u'''Split a string containing IDs separated by commas into a proper
        list of IDs (as int !)'''
        return [int(i) for i in csv_ids.split(',')]

    @staticmethod
    def __add_trailing_new_line(string):
        u'''If the last character the argument string is not a new line,
        just add one.'''
        if string[-1] not in ['\n', '\r']:
            return string + os.linesep
        return string

    def split_notes(self, temp_file, separator):
        u'''Given a file and the separator, split the content of the file into
        a list of string. The separator must be a whole line.'''
        notes = []
        current_note = StringIO()
        for line in temp_file:
            if self.to_unicode(line.strip()) == separator.strip():
                content = current_note.getvalue()
                if len(content) > 0:
                    notes.append(self.__add_trailing_new_line(content))
                current_note.close()
                current_note = StringIO()
            else:
                current_note.write(line)
        content = current_note.getvalue()
        if len(content) > 0:
            notes.append(self.__add_trailing_new_line(content))
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
        elif self.ids_to_edit:
            try:
                notes = lib.get_notes(task = task, ids = self.ids_to_edit)
            except WrongId:
                # TODO : which id ?
                write("[ERR] At least one of the ids doesn't exist",
                    output_file = sys.stderr,
                    color = (Colors.errf, Colors.errb), bold = Colors.errbold)
                exit()
        else:
            notes = []
        return notes

    def write_notes(self, opened_file, notes):
        u'''Write the notes into an opened file-like object.'''
        for note in notes:
            if note != notes[0]:
                opened_file.write(self.separator)
            if os.name == 'nt':
                to_write = re.sub('(?<!\r)\n', os.linesep, note.content)
            else:
                to_write = note.content
            opened_file.write(self.to_8bytes(to_write))

    def execute(self, cmd):
        # Get the task
        try:
            task = lib.get_task(self.task_id)
        except WrongId:
            write("[ERR] The specified task doesn't exist",
                output_file = sys.stderr,
                color = (Colors.errf, Colors.errb), bold = Colors.errbold)
            return
        if

        notes = self.fetch_notes(task)

        # Launch an editor
        if notes or not (self.ids_to_edit or self.edit_all):
            with NamedTemporaryFile(delete=False) as temp_file:
                # Write the notes fetched earlier
                self.write_notes(temp_file, notes)
                
                temp_file.close()

                # Launch the editor
                if os.name == 'nt':
                    exec_name = 'notepad.exe'
                else:
                    exec_name = 'sensible-editor'
                call([exec_name, temp_file.name])

                # Get the modifications.
                modified_file = open(temp_file.name)
                new_notes = self.split_notes(modified_file, self.separator)
                modified_file.close()
                os.remove(temp_file.name)

            # In case of an edition, replace the content of the notes fetched
            # by the new ones.
            if self.ids_to_edit:
                for note_id, content in zip(self.ids_to_edit, new_notes):
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
