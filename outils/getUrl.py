#!/usr/bin/env python

# Extract url from Microsoft IE favorites (dot url files)
# This can create bookmark page or sql insertions

# $Id$

import sys, os, time, signal, socket

def convert_dir(directory, action, outfile, verbosity='False'):
    ''' Converting directory recursivly into asked mode '''

    # Init vars
    result    = ''
    last_ccat = last_pcat = ''
    saw_cat   = []
    DLopen    = DLclose = 0

    # Getting Category and ParentCategory from path
    if verbosity:
    	print "Working directory: %s" % directory

    # Open outfile in creation mode
    fp = open(outfile, 'w')

    # Change to working dir
    os.chdir(directory)

    # Do parsing
    for root, dirs, files in os.walk('.'):
	    for name in files:
		    dir, file = os.path.split(os.path.join(root, name))
		    if len(dir.split('/')) == 1:
			current_cat = 'Other'
			parent_cat  = None
		    else:
			[parent_cat, current_cat] = dir.split('/')[-2:]
			if parent_cat == '.':
			    parent_cat = 'Other'
		    if verbosity:
		    	print "File: %s\nCurrent category: %s\nParent category: %s (%s)" % (file, current_cat, parent_cat, os.path.join(root, name))
			
		    # Fetching datas
		    urlname, link, category = read_file(os.path.join(root, name), verbosity)

		    # Moving datas according to action
		    if action == 'sql':
		    	result += "INSERT (Link, UrlName, Category, ParentCategory) INTO favoris VALUES ('%s', '%s', '%s', '%s')\n" % (link, urlname, current_cat, parent_cat)
		    elif action == 'html':
		        if result == "": # only one time here, first pass
			    result    += "<DL>\n<DT> %s\n" % current_cat
			    DLopen    += 1
			    last_ccat = current_cat
			    last_pcat = parent_cat
		            saw_cat.append(parent_cat)
			    if verbosity:
			        print "## First ## Current: %s Parent: %s Seen: %s" % (current_cat, parent_cat, saw_cat)
			elif current_cat == last_ccat: # link into a category
			    result    += "<DD><a href=\"%s\"> %s </a>\n" % (link, urlname)
			    last_ccat = current_cat
			    last_pcat = parent_cat
			    if verbosity:
			        print "## Links ## Current: %s Parent: %s Seen: %s" % (current_cat, parent_cat, saw_cat)
			elif current_cat != last_ccat: # new category
			    if parent_cat == last_ccat: # it's a sub category
			        result    += "<DL>\n<DT> %s\n" % current_cat
			        DLopen    += 1
			        last_ccat = current_cat
			        last_pcat = parent_cat
		                saw_cat.append(parent_cat)
			        if verbosity:
			            print "## New sub cat ## Current: %s Parent: %s Seen: %s" % (current_cat, parent_cat, saw_cat)
			    elif parent_cat != last_ccat: # new category in same parent category
			        if parent_cat in saw_cat:
				    while saw_cat[-1] != parent_cat:
				    	if verbosity:
				            print "Remove: %s" % saw_cat[-1]
				    	result  += "</DL>\n"
				    	DLclose += 1
					saw_cat.remove(saw_cat[-1])
			        result    += "</DL>\n<DL>\n<DT> %s\n" % current_cat
			        DLopen    += 1
			        DLclose   += 1
			        last_ccat = current_cat
			        last_pcat = parent_cat
			        if verbosity:
			            print "## DD new cat ## Current: %s Parent: %s Seen: %s" % (current_cat, parent_cat, saw_cat)
    		    if verbosity:
    			print "Resultat: %s" % result

    # Write datas
    fp.write(result)
    # Close file
    fp.close()


def convert_file(infile, action, outfile, verbosity='False'):
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
    	result = "<DL>\n<DT>%s\n<DD><a href=\"%s\"> %s </a>\n</DL>" % (category, urlname, link)
    if verbosity:
    	print "Resultat: %s" % result
    # Open outfile in creation mode
    file = open(outfile, 'w')
    file.write(result)
    file.close()

def read_file(filename, verbosity='False'):
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
    Linkname = os.path.basename(filename).split('.url')[-2]
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

    # output filename creation (made with action)
    outputFile = args[1] + '.' + action
    if options.verbose:
    	print "Output file: %s" % outputFile

    # Set the type of "favorite" argument
    if os.path.isdir(args[1]):
    	srcType = 'dir'
    	if options.verbose:
		print "Going to convert %s %s to %s file named %s.%s" % (args[0], srcType, action, args[1], action)
	convert_dir(args[1], action, outputFile, options.verbose)
    elif os.path.isfile(args[1]):
    	# It's a single file
    	srcType = 'file'
    	if options.verbose:
		print "Going to convert %s %s to %s file named %s.%s" % (args[0], srcType, action, args[1], action)
    	convert_file(args[0], action, outputFile, options.verbose)



if __name__ == "__main__":
    # Main code
    main()
