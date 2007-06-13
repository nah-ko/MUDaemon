#!/usr/bin/env python
# $Id$
#
# Define a class who handle each kind of processes
#

class ProcessHandler:
	def __init__(self, log, options):
		self.log = log
		self.options = options
		self.log.debug('Init ProcessHandler')

	def file(self, file="/tmp/file"):
		''' File processing; here we read a file in which are listed
		files who're about to be passed to the command.
		'''

		import popen2, os.path

		log = self.log
		processflag, command = self.options

		log.debug ("::file():: flag=%s file=%s" % (processflag, file))
		if processflag == 'no':
			log.err ("::file():: Processing already engaged ! :)")
		if os.path.exists(file) and processflag == 'yes':
			processflag = 'no'
			log.info ("::file():: Processing engaged ! :)")
			f = open(file,'r')
			for data in f.read().split('\n'):
				if data <> '':
					log.info ("::file():: Working on: %s" % data)
					cmd = command % data
					log.debug ("::file():: command=%s" % cmd)
					pout, pin, perr = popen2.popen3(cmd)
					OUT = pout.read()
					ERR = perr.read()
					log.debug ("::file():: out=%s err=%s" % (OUT, ERR))
					if not OUT == '':
						log.err ("::file():: %s" % OUT)
					if not ERR == '':
						log.err ("::file():: %s" % ERR)
			f.close()
			processflag = 'yes'
			os.remove(file)
		else:
			log.debug ("::file():: Nothing to do, sleeping")

		log.debug ("::file():: end of function")

	def directory(self, scandir="/tmp/mudaemon", senddir="/tmp/mudaemon",\
		      dirdict={'a': {'A*.TXT': 'A'}}):
		'''Directory scan, each known filename format will be
		passed to command for processing
		'''

		import fnmatch, os, shutil, time, commands

		log = self.log
		processflag, command = self.options

		if processflag == 'yes':
		    for Key in dirdict.keys():
			dirdictSubKey = dirdict.get(Key)
			for SubKey in dirdictSubKey.keys():
				log.debug ("Key: %s - SubKey: %s" % (Key, SubKey))
				for F in fnmatch.filter(os.listdir(scandir), SubKey):
					Fichier     = scandir + F
					Dest        = senddir + dirdictSubKey.get(SubKey) + '.TXT'
					log.debug ("Fichier: %s - Dest: %s" % (Fichier, Dest))
					TailleAvant = os.stat(Fichier).st_size
					time.sleep(3)
					TailleApres = os.stat(Fichier).st_size
					if TailleApres == TailleAvant:
						try:
							shutil.copy(Fichier, Dest)
						except (IOError, os.error), why:
							print "Can't copy %s to %s: %s" % (Fichier,\
								Dest, \
								str(why))
			
						#Commande = "almacom -f %s -t %s" % \
						Commande = command % \
							(Fichier, dirdictSubKey.get(SubKey))
						Status, Output = commands.getstatusoutput(Commande)

						if Status == 0:
							Archives = scandir + 'archives/' +\
						   		Key +'/'
							print "Archives: %s" % Archives
							try:
								shutil.move(Fichier, Archives)
							except (IOError, os.error), why:
								log.debug ("Can't copy %s to %s: %s" % (Fichier,\
									Archives, \
									str(why)))
						else:
							log.debug ("Erreur: %s" % Output)
