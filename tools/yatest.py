#!/usr/bin/env python
#-*- coding:utf-8 -*-

u"""
Tool to automatize a series of tests to the command line interface of yat


           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
                   Version 2, December 2004 

 Copyright (C) 2011
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

from optparse import OptionParser
import os
import re
import subprocess
import sys

# Global names
    # Metadata dictionnary
metadata = {
        "info": u"\033[1m\033[36m",     # Color used to display informations (bold cyan)
        "error": u"\033[31m",   # Color used to display errors (red)
        "prompt": u"\033[36m",  # Color used to display prompt texts (cyan)
        "neutral": u"\033[0m",  # Get back to normal color
    }

def prompt(cfg, test):
    u"""Display a prompt"""
    global metadata

    rtr = 0
    help_message = """Help message:

Type any of the command below, <enter> to launch the next test or <ctrl> + c to
quit. If you type <ctrl> + c during the execution of a test, the step by step
option will be activated and this prompt will be displayed.

Available commands:
    help:
        Display this help.
    paths:
        Display the differents paths used. Program tested, current configuration
        file, current test file and current working directory.
    last:
        Display the last test command.
    repeat:
        Relaunch the last test.
    call <cmd>:
        Call <cmd> on the tested program.
    next <nbr> or continue <nbr>:
        Launch the <nbr> next tests. If <nbr> isn't provided, launch the next
        test and display the prompt again. Typing just <enter> will do the same 
        thing.
    finish:
        Launch all the remaining tests without prompting the user.
    quit:
        Quit the test program.
"""

    while True:
        output("> ", type = "prompt", linebreak = False)

        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            output("")
            exit()

        if re.match(r"^\s*help\s*$", line):
            output(help_message, type = "prompt")
            continue

        if re.match(r"^\s*paths\s*$", line):
            output("""Paths used to test the program:
    Program tested:
       {yat}
    Configuration file:
        {cfg}
    Test file:
        {test}
    Working directory:
        {cwd}
""".format( yat = metadata["yat"], cfg = metadata["config-file"], 
    test = metadata["test_file"], cwd = metadata["working_directory"]), 
    type = "prompt")
            continue

        if re.match(r"^\s*last\s*$", line):
            output("""The last test command was:
    {test}""".format(test = cfg + " " + test), type = "prompt")
            continue

        if re.match(r"^\s*repeat\s*$", line):
            launch_test(cfg, test)
            continue

        res = re.match(r"^\s*call\s*(.*?)\s*$", line)
        if res != None:
            tmp_cfg = cfg
            if re.match(r"^.*?(-c|--config-file).*?$", res.group(1)):
                tmp_cfg = ""
            launch_test(tmp_cfg, res.group(1))
            continue

        res = re.match(r"^\s*((next|continue)\s*(\d*?)|)\s*$", line)
        if res != None:
            rtr = 0 if res.group(3) == None else int(res.group(3))
            break

        if re.match(r"^\s*finish\s*$", line):
            output("""Launching all the remaining tests""", type = "prompt")
            metadata["step-by-step"] = False
            break

        if re.match(r"^\s*quit\s*$", line):
            output("""Quitting...""", type = "prompt")
            exit()

        output("""Wrong command: "{line}"\n{help}""".format(line = line, 
            help = help_message), type = "prompt")

    return rtr

def launch_test(cfg, test):
    u"""Launch the tested program with command cfg + test """
    global metadata
    output("Calling programme with arguments : " + test)
    output("\tconfig-file: " + metadata["config-file"])
    subprocess.call([metadata["yat"], cfg, test])
    output("\t-> done")

def output(txt, type = "info", linebreak = True):
    global metadata
    if type != "":
        color = metadata[type]
    else:
        color = ""

    sys.stdout.write(color + txt + metadata["neutral"])

    if linebreak:
        sys.stdout.write(os.linesep)

def main():
    global metadata
    usage = "%prog [options] yat_program test_file"
    description = """This will launch the program pointed by "yat_program" with
all the test cases that are in "test_file". For instance: "python yatest.py -d
test_cases ../cli/yat test_cases/all.yatest" """

    parser = OptionParser(usage = usage, description = description)

    parser.add_option( "-d", "--directory", 
            dest = "directory",
            help = """The directory where you want to execute the tested yat.
(default: test file directory)""" )
    parser.add_option( "-s", "--step-by-step",
            action = "store_true", dest = "sbs", default = True,
            help = """Execute one test at a time, asking you to continue between
each. (default: True)""" )
    parser.add_option( "-c", "--continuous",
            action = "store_false", dest = "sbs",
            help = """Execute all the tests one after another. Type <ctrl> + c
during the tests to activate the step-by-step behavior.""" )

    (options, args) = parser.parse_args()

    metadata["step-by-step"] = options.sbs

    if not len(args) == 2:
        parser.error("incorrect number of arguments")

    # Convert paths to absolute paths
    metadata["yat"] = os.path.abspath(args[0])
    metadata["test_file"] = os.path.abspath(args[1])
    if options.directory != None:
        metadata["working_directory"] = os.path.abspath(options.directory)
    else: # if -d wasn't provided, we set the wd to the test_file directory
        metadata["working_directory"] = os.path.dirname(metadata["test_file"])

    # Extract data from the test file
    with open(metadata["test_file"], 'r') as f:
        tests = f.readlines()
    
    # Switch to the directory given
    os.chdir(metadata["working_directory"])

    # regexps
    comment = re.compile(r"^\s*#.*")
    meta = re.compile(r"^>>>(.*?)\s*:\s*\"(.*?)\"\s*$")
    empty = re.compile(r"^\s*$")

    metadata["config-file"] = ""

    # Testing
    next_test = 0
    for test in tests:
        try:
            # Strip \n from the test command
            test = re.sub(r"\n$", "", test)

            # Handle comments and empty lines
            if comment.match(test) or empty.match(test):
                continue

            # Handle meta information
            res = meta.match(test)
            if res != None:
                metadata[res.group(1)] = res.group(2)
                continue

            if metadata["config-file"] != "":
                cfg = "-c " + metadata["config-file"]
            else:
                cfg = ""
            
            launch_test(cfg, test)
            next_test = next_test - 1 if next_test > 0 else 0

            if metadata["step-by-step"] and next_test <= 0:
                next_test = prompt(cfg, test)

        except KeyboardInterrupt: # if <ctrl>-C then prompt
            metadata["step-by-step"] = True
            output("")
            next_test = prompt(cfg, test)
            

if __name__ == "__main__":
    main()
