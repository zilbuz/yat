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

def main():
    usage = "%prog [options] yat_program test_file"
    description = """This will launch the program pointed by "yat_program" with
all the test cases that are in "test_file". For instance: "python yatest.py -d
test_cases ../yat test_cases/all.yatest" """

    parser = OptionParser(usage = usage, description = description)

    parser.add_option( "-d", "--directory", 
            dest = "directory", default = os.getcwd(),
            help = "The directory where you want to execute the tested yat. (default: current directory)" )
    parser.add_option( "-s", "--step-by-step",
            action = "store_true", dest = "sbs", default = False,
            help = "Execute one test at a time, asking you to continue between each. (default: False)" )

    (options, args) = parser.parse_args()

    if not len(args) == 2:
        parser.error("incorrect number of arguments")

    # Convert paths to absolute paths
    working_directory = os.path.abspath(options.directory)
    yat = os.path.abspath(args[0])
    test_file = os.path.abspath(args[1])

    # Extract data from the test file
    with open(test_file, 'r') as f:
        tests = f.readlines()
    
    # Switch to the directory given
    os.chdir(working_directory)

    # regexps
    comment = re.compile(r"^\s*#.*")
    meta = re.compile(r"^>>>(.*?)\s*:\s*\"(.*?)\"\s*$")
    empty = re.compile(r"^\s*$")

    metadata = {
            "config-file": "",
        }

    # Testing
    for test in tests:
        test = re.sub(r"\n$", "", test)

        # Handle comments and empty lines
        if comment.match(test) or empty.match(test):
            continue

        # Handle meta information
        res = meta.match(test)
        if res != None:
            metadata[res.group(1)] = res.group(2)
            continue

        # Launch current test
        if metadata["config-file"] != "":
            cfg = "-c " + metadata["config-file"]
        else:
            cfg = ""
        
        print "Calling programme with arguments : " + test
        print "\tconfig-file: " + metadata["config-file"]
        subprocess.call([yat, cfg, test])
        print "\t-> done"
        
        if options.sbs:
            sys.stdout.write("Press enter to launch the next test")
            sys.stdin.readline()

if __name__ == "__main__":
    main()
