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
			log.info ("::file():: Nothing to do, sleeping")

		log.debug ("::file():: end of function")

	def directory(self, scandir="/tmp/mudaemon", senddir="/tmp/mudaemon", dirdict={}):
		'''Directory scan, each known filename format will be
		passed to command for processing
		'''

		import fnmatch, os, shutil, time, commands

		log = self.log
		processflag, command = self.options
		default_command = None

		if not os.path.exists(scandir):
			log.notice("::directory():: %s doesn't exists !" % scandir)
			return

		if not os.path.exists(senddir):
			log.notice("::directory():: %s doesn't exists !" % senddir)
			return

		if processflag == 'yes':
			processflag = 'no'
			log.debug("::directory():: flag=%s" % processflag)
			log.debug("::directory():: dico=%s" % dirdict)
			log.debug("::directory():: scandir=%s" % scandir)
			log.debug("::directory():: senddir=%s" % senddir)
			for Key in dirdict:
				# We test if an overriding option
				# 'command' has been written to config
				# section
				if dirdict[Key].has_key('COMMAND'):
				    # Backup default COMMAND
				    default_command = command
				    command = dirdict[Key].get('COMMAND')
				    log.debug("::directory():: Modified command: %s" % command)
				# We test if an overriding option 'tosend' has been
				# written to config section
				if dirdict[Key].has_key('TOSEND'):
				    # Value no more need to be present,
				    # so we get it and erase from dict
				    realsenddir = dirdict[Key].get('TOSEND')
				    if not os.path.exists(realsenddir):
					log.notice("::directory():: %s doesn't exists !" % realsenddir)
					continue
				    log.debug("::directory():: Modified senddir: %s" % realsenddir)
				else:
				    realsenddir = senddir
				for SubKey in [ option for option in dirdict[Key] if option not in [ 'TOSEND', 'COMMAND' ]]:
					log.debug("::directory():: Key: %s - SubKey: %s" % (Key, SubKey))
					FileMask = dirdict[Key][SubKey]
					log.debug("::directory():: FileMask=%s" % FileMask)
					for F in fnmatch.filter(os.listdir(scandir), FileMask):
						Fichier     = scandir + F
						# check if ".lock" file
						# exist to prevent from resend
						# un-backuped file
						Lock        = Fichier + ".lock"
						if os.path.exists(Lock):
							log.notice("::directory():: %s present, can't go beyond..." % Lock)
							continue
						Dest        = realsenddir + SubKey + '.TXT'
						log.debug("::directory():: Fichier: %s - Dest: %s" % (Fichier, Dest))
						TailleAvant = os.stat(Fichier).st_size
						time.sleep(15)
						TailleApres = os.stat(Fichier).st_size
						if TailleApres == TailleAvant:
							try:
								shutil.copy(Fichier, Dest)
							except (IOError, os.error), why:
								log.err("::directory():: Can't copy %s to %s: %s" % (Fichier, Dest, str(why)))

							Commande = command % (Fichier, SubKey)
							log.info("::directory():: Commande=%s" % Commande)
							# create lock file
							FD = open(Lock, "w")
							FD.write(time.ctime(time.mktime(time.localtime())))
							FD.close
							log.info("::directory():: Lock file %s created" % Lock)
							Status, Output = commands.getstatusoutput(Commande)

							# Command successful, backup file
							if Status == 0:
								Archives = scandir + 'archives/' + Key +'/'
								log.debug("::directory():: Archives: %s" % Archives)
								try:
									shutil.move(Fichier, Archives)
								except (IOError, os.error), why:
									log.err("::directory():: Can't copy %s to %s: %s" % (Fichier, Archives, str(why)))
									try:
										time.sleep(5)
										shutil.move(Fichier, Fichier + '_ARCH_PB')
									except (IOError, os.error), why:
										log.err("::directory():: Can't rename %s to %s: %s" % (Fichier, Fichier + '_ARCH_PB', str(why)))
										log.err("::directory():: Second error, abort.")
										continue
								try:
									os.remove(Lock)
									log.info("::directory():: Lock %s removed" % Lock)
								except (IOError, OSError):
									log.err("::directory():: Can't remove lock, general problem")
									continue
							else:
								log.err("::directory():: Error: %s" % Output)
				if default_command is not None:
				    command = default_command
				    default_command = None
				    log.debug("::directory():: Restore command: %s" % command)
		else:
			log.info("::directory():: Nothing to do, sleeping")

		log.debug("::directory():: end of function")
