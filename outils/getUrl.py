#!/usr/bin/env python

# Extract url from Microsoft IE favorites (dot url files)
# This can create bookmark page or sql insertions

# $Id$

import sys, os, time, signal, socket

def convert_dir(directory, action, outfile, verbosity=false):
    ''' Converting directory recursivly into asked mode '''

def convert_file(infile, action, outfile, verbosity=false):
    ''' Converting datas into asked mode '''

    # Single file, consider ParentCategory not existent
    pcategory = ""
    link, urlname, category = read_file(infile, verbosity)
    # When there is no subdir I suppose it's not an important link
    if category == "":
    	category = "Other"
    	if verbosity:
    		print "No category, going into 'Other'"

    # Moving datas according to action
    if action == 'sql':
    	result = "INSERT (Link, UrlName, Category, ParentCategory) INTO favoris VALUES ('%s', '%s', '%s', '%s')" % (link, urlname, category, pcategory)
    elif action == 'html':
    	result = "%s - <a href=\"%s\"> %s </a>" % (category, urlname, link)
    if verbosity:
    	print "Resultat: %s" % result
    # Open outfile in creation mode
    file = open(outfile, 'w')
    file.write(result)
    file.close()

def read_file(filename, verbosity=false):
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
    Usage  = "usage: %prog [options] favorite(file/dir) output_file"
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

    # Set the type of «favorite» argument
    if os.path.isdir(args[1]):
    	srcType = 'dir'
    	if options.verbose:
		print "Going to convert %s %s to %s file named %s.%s" % (args[0], srcType, action, args[1], action)
    elif os.path.isfile(args[1]):
    	# It's a single file
    	srcType = 'file'
    	# output filename creation (made with action)
    	outputFile = args[1] + '.' + action
    	if options.verbose:
    		print "Output file: %s" % outputFile
    	convert_file(args[0], action, outputFile, options.verbose)
    	if options.verbose:
		print "Going to convert %s %s to %s file named %s.%s" % (args[0], srcType, action, args[1], action)



if __name__ == "__main__":
    # Main code
    main()
