#!/usr/bin/env python

# Extract url from Microsoft IE favorites (dot url files)
# This can create bookmark page or sql insertions

# $Id$

import sys, os, time, signal, socket
from signal import SIGTERM
from signal import SIGHUP

def read_file(filename, verbosity='off'):
    ''' Reading url file '''

    import ConfigParser

    # Reading file
    if verbosity:
    	print "Reading file %s" % filename
    config = ConfigParser.ConfigParser()
    config.read(filename)

    # Get dirname to categorise url
    Category = os.path.dirname(filename)
    if verbosity:
        print "Directory: %s" % Category

    # Name of link
    Linkname, Extension = os.path.basename(filename).split('.')
    if verbosity:
    	print "Link name: %s" % Linkname
    # Fetching URL
    if verbosity:
    	print "Fetch data..."
    for section in config.sections():
        for option in config.options(section):
	    if option == 'url':
	        url = config.get(section,option)
                if verbosity:
    	            print "Url found: %s" % url

    return[(Linkname, url, Category)]


def main():
    from optparse import OptionParser

    Usage  = "usage: %prog [options] dot_url_file"
    Parser = OptionParser(usage = Usage)
    Parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=True, help="Verbose (default)")
    Parser.add_option("-q", "--quiet", action="store_false", dest="verbose", help="Be quiet...")
    Parser.add_option("-S", "--sql", action="store_true", dest="SQL", default=False, help="Put url into a sql file (not optional)")
    Parser.add_option("-H", "--html", action="store_true", dest="HTML", default=False, help="Put url into a bookmarks file (not optional)")
    (options, args) = Parser.parse_args()

    if ( options.SQL == options.HTML ) or len(args) != 1 :
	Parser.print_help()
	sys.exit(2)
    if options.verbose:
	print "Verbosity is ON"
	print "Going to proceed %s file" % args[0]

    read_file(args[0], options.verbose)

if __name__ == "__main__":
    # Main code
    main()
