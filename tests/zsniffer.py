#!/usr/bin/env python

from optparse import OptionParser
import os

def parse_content(content):
    calls = []
    for line in content:
        call = {}
        temp = line.split(' ')
        call['cmd'] = temp[0]
        call['exe'] = temp[1]
        call['exe_flag'] = temp[2]
        call['dat'] = temp[3]
        call['spp'] = temp[4]
        call['out'] = temp[5]
        call['uca'] = temp[6]
        call['dis'] = temp[7]
        call['alp'] = temp[8]
        call['win'] = temp[9]
        calls.append(call)
        
    return calls

def main():
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option("-F", "--folder", dest="parent",
                      help="Read data from parent folder")
    parser.add_option("-b", "--bat", dest="bat",
                      help="Read data from bat file")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose")
    (options, args) = parser.parse_args()
#    if len(args) != 1:
#        parser.error("incorrect number of arguments")
    if options.verbose:
        print "reading %s..." % options.folder

    if options.bat and os.path.exists(options.bat):
        f = open(options.bat, 'r')
        content = f.readlines()
        data =  parse_content(content)
        print data[0]['spp']

if __name__ == "__main__":
    main()