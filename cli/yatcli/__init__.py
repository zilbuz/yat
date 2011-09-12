#-*- coding:utf-8 -*-

u"""
Initialization file for the commands. Each new command should be in a separate
file, and the name file should be included in the __all__ list.


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

import datetime
import time
import inspect
import os
import sys
import yat
import re

# import all the command to load the aliases no matter what
#pylint: disable=W0403
import command
import add
import remove
import show
import aid
import edit
import done
import clean
import migrate
#pylint: enable=W0403

__all__ = [
        "command",
        "annotate"
        "aid",
        "add",
        "remove",
        "show",
        "edit",
        "done",
        "clean",
        "migrate"
        ]
# All filename listed here will be loaded when using the expression
# "from yatcli import *"

#pylint: disable=C0103
lib = None
name = None
commands = None
aliases = None
#pylint: enable=C0103
class MissingArgument(Exception):
    '''Raised when an argument is missing. Doh !'''
    pass

class BadArgument(Exception):
    '''Raised when an unexpected argument is encountered.'''
    pass

#pylint: disable=W0232,R0903
class Colors:
    u"""ASCII code to change console colors. f... is for foreground colors, and
    b... is for background colors"""
    default     = u"\033[0m"
    bold        = u"\033[1m"
    fblack      = u"\033[30m"
    fred        = u"\033[31m"
    fgreen      = u"\033[32m"
    fyellow     = u"\033[33m"
    fblue       = u"\033[34m"
    fmagenta    = u"\033[35m"
    fcyan       = u"\033[36m"
    fwhite      = u"\033[37m"
    bblack      = u"\033[40m"
    bred        = u"\033[41m"
    bgreen      = u"\033[42m"
    byellow     = u"\033[43m"
    bblue       = u"\033[44m"
    bmagenta    = u"\033[45m"
    bcyan       = u"\033[46m"
    bwhite      = u"\033[47m"

    available = ["", "black", "white", "red", "green",
                 "yellow", "blue", "magenta", "cyan"]

    # Shortcut to errors colors
    errf = "red"
    errb = ""
    errbold = True

    @staticmethod
    def get(foreground, background, bold):
        u"""Return the string with the code to change the colors of the console
        text. The first two parameters are the color name, in "red", "green",
        "yellow", "blue", "magenta", "cyan", "white", "black". The last
        parameter is True or False."""

        foreground = foreground.lower()
        background = background.lower()

        if foreground in Colors.available and background in Colors.available:
            color_dict = dict(inspect.getmembers(Colors))

            fcolor = u""
            if foreground != "":
                fcolor = color_dict["f" + foreground]

            bcolor = u""
            if background != "":
                bcolor = color_dict["b" + background]
            
            if bold:
                bold_code = Colors.bold
            else:
                bold_code = u""
                
            return bold_code + fcolor + bcolor
#pylint: enable=W0232,R0903

def is_command(obj):
    u"""Check if the parameter is a class derived from Command, without being
    Command"""

    if inspect.isclass(obj):
        return (issubclass(obj, command.Command) and
                not(obj is command.Command))
    else:
        return False

def write(string = u"", output_file = None, linebreak = True,
           color = None, bold = False):
    u'''Write a string in a file (or any file-like output).
    When file isn't specified, the one in yatcli.lib is used.
    If linebreak is set to True, a linebreak will be inserted after the
    string.
    color is a couple of strings used for the foreground and the background.
    '''
    # Defaults when the library isn't set yet
    if lib == None:
        if output_file == None:
            output_file = sys.stderr
        use_colors = not os.name == 'nt'
        enc = 'utf-8'
    else:
        use_colors = lib.config["cli.colors"] and not os.name == 'nt'
        enc = lib.enc

    # Default output
    if output_file == None:
        output_file = lib.output

    # Process colors
    if use_colors and color:
        foreground = color[0] if color[0] else ''
        background = color[1] if color[1] else ''
        string = Colors.get(foreground, background, bold) + \
                string + Colors.default

    output_file.write(string.encode(enc))
    if linebreak:
        output_file.write(os.linesep)

def read(input_file = None):
    u'''Read a line from a file. The file defaults to the one specified
    in yatcli.lib.
    '''
    if input_file == None:
        input_file = lib.input
    return input_file.readline().encode(lib.enc)

def yes_no_question(txt, default = False,
                    input_file = None, output_file = None):
    u"""Ask the user the 'txt' yes/no question (append ' (Y/n)' or (y/N)
    depending of the 'default' parameter) and return the answer with a boolean:
    True for yes and False for no. 'i' and 'o' are the input and output to use.
    If None, they use the ones defined in yat.ib"""

    yn_txt = ""
    if default:
        yn_txt = "Y/n"
    else:
        yn_txt = "y/N"

    write(txt + " ("+ yn_txt + ")", output_file = output_file)
    rep = read(input_file).lower()
    while len(rep) == 0 or (rep[0] != "y" and rep[0] != "n" and rep[0] != "\n"):
        write(yn_txt + " :", output_file = output_file)
        rep = read().lower()

    if rep[0] == "\n":
        return default
    else:
        return rep[0] != "n"

def parse_input_date(date_string):
    u"""This function parses a string representing a date, and return the
    corresponding timestamp. Raises a ValueError if there is an error in the
    date."""
    regex_date = re.match(lib.config["re.date"], date_string)
    re_date = regex_date.groupdict()
    year = int(re_date["year"])
    if lib.config["cli.input_date"] == "dd/mm":
        month = int(re_date["x2"])
        day = int(re_date["x1"])
    else:
        month = int(re_date["x1"])
        day = int(re_date["x2"])

    hour = 0
    if re_date["hour"] != None: 
        hour = int(re_date["hour"])

    minute = 0
    if re_date["minute"] != None: 
        minute = int(re_date["minute"])

    apm = "am"
    if re_date["apm"] != None:
        apm = re_date["apm"]

    if lib.config["cli.input_time"] == "12" and apm == "pm":
        hour += 12

    date = datetime.datetime(year, month, day, hour, minute)
    return time.mktime(date.timetuple())

def parse_output_date(timestamp):
    u"""This function parse a timestamp into the format defined in the
    cli.output_datetime option. (empty string if the timestamp is infinite)"""
    date_string = ""
    if (timestamp != float('+inf') and timestamp != float('-inf') and
        timestamp != float('+nan') and timestamp != float('-nan')):
        date = datetime.datetime.fromtimestamp(timestamp)
        date_string = u"{0:" + lib.config["cli.output_datetime"] + u"}"
        date_string = date_string.format(date)
    return date_string
