#!/bin/env python

from __future__ import print_function
import os, sys, ftplib, shutil
from ConfigParser import SafeConfigParser as ConfigParser

if len(sys.argv) < 2:
    print("Usage: %s [-q] <configuration-file>" % sys.argv[0])
    sys.exit(1)

config_file = sys.argv[-1]
if not os.path.isfile(config_file):
    print("\"%s\" does not exist." % config_file)
    sys.exit(1)

chatty = not "-q" in sys.argv

# load the configuration-file
config = ConfigParser()
config.readfp(open(config_file))

# map of required sections and their respective options
config_layout = {"folders": ["hotfolder", "coldfolder"]
                ,"server": ["address", "dir", "username", "password", "timeout"]
                }

# compare the supplied configuration with the required sections and options
config_errors = []
for section in config_layout:
    if not config.has_section(section):
        config_errors.append("Missing section \"%s\"" % section)
    else:
        for option in config_layout[section]:
            if not config.has_option(section, option):
                config_errors.append("Missing option \"%s\" in section \"%s\"" % (option, section))

# print list of configuration errors
if len(config_errors) > 0:
    print("Incomplete configuration:")
    map (print, config_errors)
    sys.exit(1)

# fetch options from the configuration
hotfolder = config.get("folders", "hotfolder")
coldfolder = config.get("folders", "coldfolder")
server = config.get("server", "address")
server_dir = config.get("server", "dir")
username = config.get("server", "username")
password = config.get("server", "password")
timeout = config.getfloat("server", "timeout")

# make sure the hotfolder exists
if not os.path.isdir(hotfolder):
    print("Hotfolder \"%s\" does not exist." % hotfolder)
    sys.exit(2)

# make sure the coldfolder exists
if not os.path.isdir(coldfolder):
    print("Coldfolder \"%s\" does not exist." % coldfolder)
    sys.exit(3)

# get a list of files to transfer
files = os.listdir(hotfolder)

if len(files) == 0:
    if chatty: print("No files to upload.")
else:
    upload_count = 0
    fail_count = 0

    if chatty:
        print("Connecting to %s.." % server, end='')
        sys.stdout.flush()
    try:
        ftp = ftplib.FTP(server, timeout=timeout)
        if chatty: print("Done")
    except Exception as e:
        print("Failed: %s" % e)
        sys.exit(4)

    if chatty:
        print("Logging in..", end='')
        sys.stdout.flush()
    try:
        ftp.login(username, password)
        if chatty: print("Done")
    except ftplib.error_perm as e:
        print("Failed: %s" % e)
        sys.exit(5)

    if chatty: print("Starting to upload files to %s%s" % (server, server_dir))
    for f in files:
        source = os.path.join("hotfolder", f)
        destination = os.path.join("coldfolder", f)

        if chatty:
            print("Uploading %s.." % f, end='')
            sys.stdout.flush()
        try:
            with open(source) as handle:
                ftp.storbinary("STOR %s/%s" % (server_dir, f), handle)
        except KeyboardInterrupt:
            print()
            print("Interrupted by user.")
            sys.exit(10)
        except Exception as e:
            print("Failed: %s" % e)
            fail_count += 1
        else:
            if chatty: print("Done")
            upload_count += 1

            if chatty:
                print("Moving %s to %s.. " % (source, destination), end='')
                sys.stdout.flush()
            shutil.move(source, destination)
            if chatty: print("Done")

    try:
        ftp.quit()
    except Exception:
        pass # little point doing anything here

    if chatty: print("Uploaded files: %s, failed files: %s" % (upload_count, fail_count))
