#!/opt/CPsuite-R77/fw1/Python/bin/python
# -*- coding: utf-8 -*-
import re, os, argparse

__version__ = "1.2"
parser = argparse.ArgumentParser(description="Wildcard object script v" + __version__)
print ("*** ")
print ("*** " + parser.description)
print ("*** ")
parser.add_argument('mode', choices=["export","update"], help="Operation to perform")
parser.add_argument("infile", help="Objects file with records to convert")
parser.add_argument("outfile", help="Output file")
args = parser.parse_args()
if args.mode.lower() == "export":
    if os.path.exists(args.infile):
        print "objects input file path: " + args.infile
        with open(args.infile, 'rb') as fi:
            objectsFile = fi.read()
        print "file found! file size: {:,} bytes".format(len(objectsFile))
        findpattern = r':name\s+\((.*)\)(?:[\s\S]{0,250}):color\s+\((.*)\)(?:[\s\S]{0,100}):comments\s+\((.*)\)(?:[\s\S]{0,100}):ipaddr\s+\((.*)\)(?:[\s\S]{0,150}):netmask\s+\((.*)\)(?:[\s\S]{0,100}):use_as_wildcard_netmask\s+\(true\)'
        matches = re.findall(findpattern,objectsFile)
        if matches:
            print "Regex matches: {:,}".format(len(matches))
            with open(args.outfile, "wb") as fo:
                #Write CSV header
                fo.write("name,color,comments,ipv4-address,ipv4-mask-wildcard\n")
                for match in matches:
                    fo.write("{},{},{},{},{}\n".format(match[0],match[1],match[2],match[3], match[4]))
            print ""
            print "Output written to: {}".format(args.outfile)
        else:
            print "No matches found!"
    else:
        print "ERROR: File '{}' not found".format(args.infile)
elif args.mode.lower() == "update":
    if args.infile:
        findpattern = r':netmask\s+\(.*\)([\s\S]{0,150}):use_as_wildcard_netmask\s+\(true\)'
        replpattern = r':netmask (255.255.255.0)\1:use_as_wildcard_netmask (true)'
        if os.path.exists(args.infile):
            print "objects input file path: " + args.infile
            with open(args.infile, 'rb') as fi:
                objectsFile = fi.read()
            print "file found! file size: {:,} bytes".format(len(objectsFile))
            replaced = re.subn(findpattern,replpattern,objectsFile)
            if replaced[1] > 0:
                print "replaced: {:,} instances".format(replaced[1])
                with open(args.outfile, "wb") as fo:
                    fo.write(replaced[0])
                print "Conversion complete!"
                print ""
                print "Output written to: {}".format(args.outfile)
            else:
                print "No matching instances found."
        else:
            print "Could not open input file '{}'".format(args.infile)
