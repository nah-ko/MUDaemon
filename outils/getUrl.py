#!/usr/bin/env python

# Extract url from Microsoft IE favorites (dot url files)
# This can create bookmark page or sql insertions

# $Id$

import sys, os, time, signal, socket
from signal import SIGTERM
from signal import SIGHUP

def convert_file(datas, action, outfile, verbosity='off'):
    ''' Converting datas into asked mode '''

    link, url, category = datas
    # When there is no subdir I suppose it's not an important link
    if category == "":
    	category = "Other"
    	if verbosity:
    		print "No category, going into 'Other'"

    # Moving datas according to action
    if action == 'sql':
    	result = "INSERT (Url, Nom_url, Categ) INTO favoris VALUES ('%s', '%s', '%s')" % (link, url, category)
    elif action == 'html':
    	result = "%s - <a href=\"%s\"> %s </a>" % (category, url, link)
    if verbosity:
    	print "Resultat: %s" % result
    # Open outfile in creation mode
    file = open(outfile, 'w')
    file.write(result)
    file.close()

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
        print "Category: %s" % Category

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

    return[Linkname, url, Category]


def main():
    from optparse import OptionParser

    # Define usage and give command line options to parser object
    Usage  = "usage: %prog [options] dot_url_file output_file"
    Parser = OptionParser(usage = Usage)
    Parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Verbose (default)")
    Parser.add_option("-q", "--quiet", action="store_false", dest="verbose", help="Be quiet...")
    Parser.add_option("-S", "--sql", action="store_true", dest="SQL", default=False, help="Put url into a sql file (not optional)")
    Parser.add_option("-H", "--html", action="store_true", dest="HTML", default=False, help="Put url into a bookmarks file (not optional)")
    (options, args) = Parser.parse_args()

    # -H, -S, dot_url_file and output_file are not optionnal
    if ( options.SQL == options.HTML ) or len(args) != 2 :
	Parser.print_help()
	sys.exit(2)

    # Select action
    if options.SQL:
        action = "sql"
    elif options.HTML:
        action = "html"

    # Printing some informations while in verbose mode
    if options.verbose:
	print "Going to convert %s file to %s file named %s.%s" % (args[0], action, args[1], action)

    # Get datas from the file
    resultat = read_file(args[0], options.verbose)
    # output filename creation (made with action)
    outputFile = args[1] + '.' + action
    if options.verbose:
    	print "Output file: %s" % outputFile
    convert_file(resultat, action, outputFile, options.verbose)

if __name__ == "__main__":
    # Main code
    main()
